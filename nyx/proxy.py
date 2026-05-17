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

from aiohttp import ClientSession, ClientTimeout, web  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [proxy] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nyx.proxy")

from nyx.agent.intent import classify as _classify_intent  # noqa: E402
from nyx.agent.lang_check import is_pt_br as _is_pt_br  # noqa: E402
from nyx.config.defaults import DEFAULT_MODEL as _DEFAULT_MODEL  # noqa: E402
from nyx.config.defaults import NUM_CTX as _DEFAULT_NUM_CTX  # noqa: E402
from nyx.config.defaults import NUM_GPU_3B as _DEFAULT_NUM_GPU  # noqa: E402
from nyx.config.defaults import NUM_PREDICT_CHAT as _NUM_PREDICT_CHAT  # noqa: E402
from nyx.config.defaults import NUM_PREDICT_TOOL as _NUM_PREDICT_TOOL  # noqa: E402
from nyx.config.defaults import OLLAMA_KEEP_ALIVE as _KEEP_ALIVE  # noqa: E402
from nyx.config.defaults import OLLAMA_PORT as _DEFAULT_OLLAMA_PORT  # noqa: E402
from nyx.config.defaults import OLLAMA_URL as _DEFAULT_OLLAMA_URL  # noqa: E402
from nyx.config.defaults import PROXY_PORT as _DEFAULT_PROXY_PORT  # noqa: E402

OLLAMA_URL = _DEFAULT_OLLAMA_URL
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
    """Converte content array (formato de chat) para string (Ollama)."""
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


def _last_user_text(messages: list) -> str:
    """Retorna o conteúdo do último turno role=user. '' se não houver."""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            content = msg.get("content", "")
            if isinstance(content, str):
                return content
            return _normalize_content(content)
    return ""


def openai_to_ollama(body: dict) -> tuple[dict, str]:
    """Converte request OpenAI -> Ollama nativa.

    Retorna tupla (body_ollama, intent) para que o caller decida se aplica
    guardrail de idioma (LANG-ENFORCE-01).

    Gating por intent (PERF-INFERENCE-01):
    - intent=saudacao/chat: tools=[]; think=false; num_predict=NUM_PREDICT_CHAT.
    - intent=tool-needed: mantém tools do request; think=true; num_predict=NUM_PREDICT_TOOL.
    - intent=comando: idêntico a chat (proxy não trata /command, mas o caso é raro
      pois CLI intercepta antes do payload).
    """
    messages = _normalize_messages(body.get("messages", []))
    last_user = _last_user_text(messages)
    intent = _classify_intent(last_user)

    has_tools = bool(body.get("tools"))
    # Suprime tools quando intent não precisa.
    if intent in ("saudacao", "chat", "comando") and has_tools:
        logger.info("intent=%s -> tools suprimidos (%d)", intent, len(body["tools"]))
        has_tools = False

    result: dict = {
        "model": body.get("model", _DEFAULT_MODEL),
        "messages": messages,
        "think": has_tools,
        "stream": False,
        "keep_alive": _KEEP_ALIVE,
        "options": {
            "num_gpu": NUM_GPU,
            "num_ctx": NUM_CTX,
        },
    }
    if has_tools:
        result["tools"] = body["tools"]
        result["options"]["num_predict"] = _NUM_PREDICT_TOOL
    else:
        result["options"]["num_predict"] = _NUM_PREDICT_CHAT
    if body.get("temperature") is not None:
        result["options"]["temperature"] = body["temperature"]
    # max_tokens explícito do request sobrescreve heurística.
    max_tok = body.get("max_tokens") or body.get("max_completion_tokens")
    if max_tok:
        result["options"]["num_predict"] = max_tok
    return result, intent


THINK_PATTERN = re.compile(r"<think>.*?</think>\s*", re.DOTALL)
# Qwen3 thinking 2507 com think=false às vezes emite raciocínio sem a tag
# de abertura, fechando com </think>\n\n. Captura tudo até o primeiro </think>.
THINK_PARTIAL = re.compile(r"^.*?</think>\s*", re.DOTALL)


def _strip_think(text: str) -> str:
    """Remove blocos <think>...</think> da resposta.

    Cobre 3 formatos:
    1. <think>...</think> bem-formado.
    2. ...</think> (qwen3 com think=false emite raciocínio sem abrir tag).
    3. Sem tag (nada a remover).
    """
    if not text:
        return ""
    out = THINK_PATTERN.sub("", text)
    # Se ainda restou um </think> órfão, descarta tudo antes dele.
    if "</think>" in out:
        out = THINK_PARTIAL.sub("", out, count=1)
    return out.strip()


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
    model = body.get("model", _DEFAULT_MODEL)
    ollama_body, intent = openai_to_ollama(body)

    n_tools = len(body.get("tools", []))
    logger.info("-> model=%s tools=%d intent=%s", model, n_tools, intent)

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

    # LANG-ENFORCE-01: guardrail de idioma em respostas conversacionais.
    # Se intent é saudacao/chat, modelo respondeu em inglês e não tem tool_calls,
    # faz UM retry com hint reforçado. Cap em 1 para não explodir P50.
    if intent in ("saudacao", "chat"):
        choice_msg = result["choices"][0]["message"]
        content = choice_msg.get("content", "")
        has_tc = bool(choice_msg.get("tool_calls"))
        if content and not has_tc and not _is_pt_br(content):
            logger.warning("LANG: resposta em ingles detectada (intent=%s); retry 1x com hint", intent)
            retry_body = dict(ollama_body)
            retry_messages = list(ollama_body.get("messages", []))
            retry_messages.append({"role": "assistant", "content": content})
            retry_messages.append(
                {
                    "role": "user",
                    "content": (
                        "Responda em português brasileiro. "
                        "Sua resposta anterior estava em inglês; refaça em português."
                    ),
                }
            )
            retry_body["messages"] = retry_messages
            async with session.post(f"{OLLAMA_URL}/api/chat", json=retry_body) as lang_resp:
                if lang_resp.status == 200:
                    lang_data = await lang_resp.json()
                    lang_result = ollama_to_openai(lang_data, model)
                    lang_content = lang_result["choices"][0]["message"].get("content", "")
                    if lang_content and _is_pt_br(lang_content):
                        logger.info("LANG: retry recuperou PT-BR")
                        result = lang_result
                    else:
                        logger.info("LANG: retry insistiu em ingles; passa adiante")
                else:
                    logger.warning("LANG: retry HTTP %d; passa adiante", lang_resp.status)

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
    parser.add_argument("--port", type=int, default=_DEFAULT_PROXY_PORT)
    parser.add_argument("--ollama-port", type=int, default=_DEFAULT_OLLAMA_PORT)
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
