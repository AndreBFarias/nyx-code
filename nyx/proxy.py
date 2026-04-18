"""Proxy OpenAI -> Ollama nativa com think adaptativo.

think=true quando há tools (qwen3 precisa raciocinar para gerar tool_calls).
think=false quando é chat puro (economiza tokens).
Filtra blocos <think> da resposta para não poluir o output.

Usa aiohttp (já no sistema) em vez de FastAPI para ser leve.
"""

from __future__ import annotations

import json
import logging
import re
import sys
import time
import uuid
from pathlib import Path

# Permitir execução como script direto (python nyx/proxy.py) além de -m nyx.proxy.
# Sem isso, só o diretório nyx/ entra no sys.path e `import nyx.config` falha.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from aiohttp import ClientSession, ClientTimeout, web

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [proxy] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nyx.proxy")

from nyx.config.defaults import NUM_CTX as _DEFAULT_NUM_CTX
from nyx.config.defaults import NUM_GPU_3B as _DEFAULT_NUM_GPU

OLLAMA_URL = "http://127.0.0.1:11435"
NUM_GPU = _DEFAULT_NUM_GPU
NUM_CTX = _DEFAULT_NUM_CTX

# Graceful degradation: quando Ollama retorna OOM, cai pra CPU permanente
# até o fim da sessão. Evita loop de retry e mantém o serviço vivo (ADR-001).
_OOM_DEGRADED = False
_OOM_PATTERNS = (
    "out of memory",
    "cuda out of memory",
    "cudamalloc",
    "requires more memory",
    "not enough memory",
    "no cuda device",
    "unable to allocate",
)


def _is_oom_error(text: str) -> bool:
    if not text:
        return False
    low = text.lower()
    return any(p in low for p in _OOM_PATTERNS)


def _normalize_content(content):
    """Converte content array (Anthropic) para string (Ollama)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif item.get("type") == "tool_result":
                    parts.append(str(item.get("content", "")))
                else:
                    parts.append(str(item))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    return str(content)


def _normalize_messages(messages: list) -> list:
    """Normaliza content de cada mensagem para string."""
    result = []
    for msg in messages:
        normalized = dict(msg)
        if "content" in normalized:
            normalized["content"] = _normalize_content(normalized["content"])
        result.append(normalized)
    return result


def openai_to_ollama(body: dict) -> dict:
    """Converte request OpenAI -> Ollama nativa.

    think=true quando há tools (qwen3 precisa pensar para gerar tool_calls).
    think=false quando é chat puro (economiza tokens).
    """
    has_tools = bool(body.get("tools"))
    result: dict = {
        "model": body.get("model", "qwen3:4b"),
        "messages": _normalize_messages(body.get("messages", [])),
        "think": has_tools,
        "stream": False,
        "options": {
            "num_gpu": NUM_GPU,
            "num_ctx": NUM_CTX,
        },
    }
    if has_tools:
        result["tools"] = body["tools"]
    if not has_tools:
        result["options"]["num_predict"] = 1024
    if body.get("temperature") is not None:
        result["options"]["temperature"] = body["temperature"]
    max_tok = body.get("max_tokens") or body.get("max_completion_tokens")
    if max_tok:
        result["options"]["num_predict"] = max_tok
    return result


THINK_PATTERN = re.compile(r"<think>.*?</think>\s*", re.DOTALL)


def _strip_think(text: str) -> str:
    """Remove blocos <think>...</think> da resposta."""
    return THINK_PATTERN.sub("", text).strip()


def ollama_to_openai(data: dict, model: str) -> dict:
    """Converte resposta Ollama nativa -> formato OpenAI."""
    msg = data.get("message", {})
    content = _strip_think(msg.get("content", ""))
    choice: dict = {
        "index": 0,
        "message": {
            "role": msg.get("role", "assistant"),
            "content": content,
        },
        "finish_reason": "stop",
    }
    tool_calls = msg.get("tool_calls")
    if tool_calls:
        oai_tc = []
        for i, tc in enumerate(tool_calls):
            func = tc.get("function", {})
            args = func.get("arguments", {})
            if isinstance(args, dict):
                args = json.dumps(args)
            oai_tc.append(
                {
                    "id": tc.get("id", f"call_{uuid.uuid4().hex[:8]}"),
                    "index": i,
                    "type": "function",
                    "function": {"name": func.get("name", ""), "arguments": args},
                }
            )
        choice["message"]["tool_calls"] = oai_tc
        choice["message"]["content"] = ""  # Limpar reasoning quando há tool_calls
        choice["finish_reason"] = "tool_calls"

    return {
        "id": f"chatcmpl-{uuid.uuid4().hex[:6]}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "system_fingerprint": "fp_nyx_proxy",
        "choices": [choice],
        "usage": {
            "prompt_tokens": data.get("prompt_eval_count", 0),
            "completion_tokens": data.get("eval_count", 0),
            "total_tokens": data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
        },
    }


async def _get_session(app: web.Application) -> ClientSession:
    """Retorna sessão HTTP compartilhada (criada uma vez por app)."""
    return app["http_session"]


async def handle_chat(request: web.Request) -> web.StreamResponse:
    global _OOM_DEGRADED, NUM_GPU

    body = await request.json()
    model = body.get("model", "qwen3:4b")
    ollama_body = openai_to_ollama(body)

    n_tools = len(body.get("tools", []))
    logger.info("-> model=%s tools=%d", model, n_tools)

    session = await _get_session(request.app)
    async with session.post(f"{OLLAMA_URL}/api/chat", json=ollama_body) as ollama_resp:
        if ollama_resp.status != 200:
            text = await ollama_resp.text()
            logger.error("Ollama %d: %s", ollama_resp.status, text[:200])

            if _is_oom_error(text) and not _OOM_DEGRADED:
                _OOM_DEGRADED = True
                NUM_GPU = 0
                logger.warning("OOM detectado. Degradando num_gpu=0 (CPU) para esta sessão")
                ollama_body["options"]["num_gpu"] = 0
                async with session.post(f"{OLLAMA_URL}/api/chat", json=ollama_body) as retry_resp:
                    if retry_resp.status != 200:
                        retry_text = await retry_resp.text()
                        logger.error("Retry CPU falhou: %d %s", retry_resp.status, retry_text[:200])
                        return web.json_response(
                            {"error": {"message": retry_text, "type": "api_error"}},
                            status=retry_resp.status,
                        )
                    data = await retry_resp.json()
                    logger.info("OOM recovery OK: resposta via CPU")
            else:
                return web.json_response(
                    {"error": {"message": text, "type": "api_error"}},
                    status=ollama_resp.status,
                )
        else:
            data = await ollama_resp.json()

    logger.info("Ollama raw keys: %s", list(data.get("message", {}).keys()))
    logger.info("Ollama tool_calls: %s", data.get("message", {}).get("tool_calls", "NONE"))
    result = ollama_to_openai(data, model)
    tc = result["choices"][0]["message"].get("tool_calls")
    if tc:
        logger.info("<- tool_calls: %s", [t["function"]["name"] for t in tc])
    else:
        logger.info("<- text: %s", result["choices"][0]["message"].get("content", "")[:60])
    return web.json_response(result)


async def handle_models(request: web.Request) -> web.Response:
    session = await _get_session(request.app)
    try:
        async with session.get(f"{OLLAMA_URL}/api/tags") as resp:
            if resp.status != 200:
                return web.json_response({"object": "list", "data": []})
            tags = await resp.json()
    except Exception as e:
        logger.debug("Falha ao listar modelos: %s", e)
        return web.json_response({"object": "list", "data": []})
    models = [
        {"id": m["name"], "object": "model", "created": int(time.time()), "owned_by": "ollama"}
        for m in tags.get("models", [])
    ]
    return web.json_response({"object": "list", "data": models})


async def handle_model(request: web.Request) -> web.Response:
    model_id = request.match_info["model_id"]
    return web.json_response({"id": model_id, "object": "model", "created": int(time.time()), "owned_by": "ollama"})


async def handle_health(request: web.Request) -> web.Response:
    """Health check: verifica se Ollama responde."""
    session = await _get_session(request.app)
    ollama_ok = False
    try:
        async with session.get(f"{OLLAMA_URL}/api/version") as resp:
            ollama_ok = resp.status == 200
    except Exception as e:
        logger.debug("Health check Ollama falhou: %s", e)

    status = "ok" if ollama_ok else "degraded"
    return web.json_response({"status": status, "ollama": ollama_ok, "proxy": True})


async def _on_startup(app: web.Application) -> None:
    app["http_session"] = ClientSession(timeout=ClientTimeout(total=600))
    logger.info("Sessão HTTP criada")


async def _on_cleanup(app: web.Application) -> None:
    await app["http_session"].close()
    logger.info("Sessão HTTP encerrada")


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=11436)
    parser.add_argument("--ollama-port", type=int, default=11435)
    parser.add_argument("--num-gpu", type=int, default=15)
    parser.add_argument("--num-ctx", type=int, default=8192)
    args = parser.parse_args()

    global OLLAMA_URL, NUM_GPU, NUM_CTX
    OLLAMA_URL = f"http://127.0.0.1:{args.ollama_port}"
    NUM_GPU = args.num_gpu
    NUM_CTX = args.num_ctx

    logger.info("Proxy :%d -> Ollama :%d (num_gpu=%d, think=false)", args.port, args.ollama_port, NUM_GPU)

    app = web.Application()
    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)
    app.router.add_post("/v1/chat/completions", handle_chat)
    app.router.add_get("/v1/models", handle_models)
    app.router.add_get("/v1/models/{model_id}", handle_model)
    app.router.add_get("/health", handle_health)
    web.run_app(app, host="127.0.0.1", port=args.port, print=None)


if __name__ == "__main__":
    main()


# "Entre o estímulo e a resposta há um espaço." -- Viktor Frankl
