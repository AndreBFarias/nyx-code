"""Proxy OpenAI -> Ollama nativa com think adaptativo.  # noqa-anonimato

think=true quando há tools (qwen3 precisa raciocinar para gerar tool_calls).
think=false quando é chat puro (economiza tokens).
Filtra blocos <think> da resposta para não poluir o output.

Usa aiohttp (já no sistema) em vez de FastAPI para ser leve.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import signal
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
from nyx.agent.intent import wants_save_memory as _wants_save_memory  # noqa: E402
from nyx.agent.lang_check import is_pt_br as _is_pt_br  # noqa: E402
from nyx.agent.lang_check import mentions_provider as _mentions_provider  # noqa: E402
from nyx.config.defaults import DEFAULT_MODEL as _DEFAULT_MODEL  # noqa: E402
from nyx.config.defaults import NUM_CTX as _DEFAULT_NUM_CTX  # noqa: E402
from nyx.config.defaults import NUM_GPU_3B as _DEFAULT_NUM_GPU  # noqa: E402
from nyx.config.defaults import OLLAMA_KEEP_ALIVE as _KEEP_ALIVE  # noqa: E402
from nyx.config.defaults import OLLAMA_PORT as _DEFAULT_OLLAMA_PORT  # noqa: E402
from nyx.config.defaults import OLLAMA_URL as _DEFAULT_OLLAMA_URL  # noqa: E402
from nyx.config.defaults import PROXY_PORT as _DEFAULT_PROXY_PORT  # noqa: E402
from nyx.config.defaults import PROXY_STATS_PATH as _PROXY_STATS_PATH  # noqa: E402
from nyx.config.defaults import model_supports_thinking as _model_supports_thinking  # noqa: E402
from nyx.config.defaults import num_predict_for as _num_predict_for  # noqa: E402

OLLAMA_URL = _DEFAULT_OLLAMA_URL
NUM_CTX = _DEFAULT_NUM_CTX

# PROXY-NUMGPU-RUNTIME-01: num_gpu deixa de ser módulo-global. Snapshot
# inicial vai para app["num_gpu"] em _on_startup e pode ser re-tunado em
# runtime via GET /admin/tune (loopback) sem reiniciar o proxy.
#
# INFRA-NUM-GPU-RECONCILE-01: cadeia REAL do num_gpu no boot e
#   run.sh (auto-tune detect_gpu.py) -> --num-gpu -> app["state"]["num_gpu"].
# O import de NUM_GPU_3B (=-1) e SO fallback teorico: o argparse
# `--num-gpu default=15` ja popula state["num_gpu"] antes do _on_startup,
# entao o setdefault(_INITIAL_NUM_GPU) abaixo nunca alcanca o import.
_INITIAL_NUM_GPU = _DEFAULT_NUM_GPU

# Graceful degradation: quando Ollama retorna OOM, cai pra CPU permanente
# até o fim da sessão. Evita loop de retry e mantém o serviço vivo (ADR-001).
#
# Trigger: _is_oom_error casa _OOM_PATTERNS contra texto da resposta 500
# de /api/chat do Ollama (ex.: "cudaMalloc failed", "out of memory").
#
# Ação: ao primeiro hit, handle_chat tenta passo intermediário num_gpu // 2
# antes do fallback CPU (INFRA-OOM-RETRY-STEP-01). Sequência: 15 -> 7 -> 0.
# Se intermediário (GPU parcial) também retornar OOM, cai para num_gpu=0
# e seta state["oom_degraded"]=True. Cap de 2 retries total (sem loop).
# Incrementa state["oom_recovery_count"] uma vez por OOM event (não por retry).
# Observabilidade via GET /admin/stats (INFRA-OOM-02).
#
# Permanência: a degradação é PERMANENTE até restart do proxy. handle_tune
# respeita o fail-safe e NÃO reanima GPU após OOM (ver bloco state["oom_degraded"]
# em handle_tune). Justificativa: evitar oscilação CPU<->GPU em loop quando
# VRAM oscila no limite. ADR-001 Local First prioriza serviço vivo sobre
# throughput.
#
# PROXY-HANDLE-CHAT-REFACTOR-01: o flag vive em app["state"]["oom_degraded"]
# (default False em _on_startup e main()), coerente com num_gpu e
# oom_recovery_count, que já moraram em app["state"] desde PROXY-NUMGPU-RUNTIME-01.
# INFRA-OOM-ADAPTIVE-GPU-01 (opt-in NYX_GPU_ADAPTIVE=1): reanimação de GPU.
# Quando a sessão degradou para CPU mas a VRAM liberou depois (ex.: o usuário
# fechou o Chrome), o Nyx volta ao num_gpu de boot em vez de ficar preso em CPU
# até reiniciar. Default OFF preserva o fail-safe estabilizado (CPU permanente,
# anti-loop). NÃO sobe o cap de boot -- a fragmentação CUDA limita o teto
# (ADR-003 / detect_gpu.py); a reanimação usa o num_gpu sugerido pelo detect_gpu
# (já capado), nunca um valor maior.
_GPU_ADAPTIVE = os.environ.get("NYX_GPU_ADAPTIVE") == "1"
# time.monotonic() do último OOM; cooldown anti-thrash entre tentativas de reanimar.
_OOM_LAST_TS = 0.0
_REANIMATE_COOLDOWN_S = 120.0
# Cobertura empírica: 9 padrões observados em runtime real do RTX 3050 4GB
# com qwen2.5-coder:3b. INFRA-OOM-PATTERNS-KV-CACHE-01 adicionou
# 'kv cache' (Ollama kv cache buffer alloc fail) e 'ggml_assert'
# (assert interno do llama.cpp via Ollama).
_OOM_PATTERNS = (
    "out of memory",
    "cuda out of memory",
    "cudamalloc",
    "requires more memory",
    "not enough memory",
    "no cuda device",
    "unable to allocate",
    "kv cache",
    "ggml_assert",
)


def _is_oom_error(text: str) -> bool:
    if not text:
        return False
    low = text.lower()
    return any(p in low for p in _OOM_PATTERNS)


def _next_num_gpu_step(current: int) -> int:
    """Calcula próximo passo de degradação OOM: current // 2 ou 0.

    Sequência esperada (INFRA-OOM-RETRY-STEP-01): 15 -> 7 -> 0.
    Quando current <= 1, retorna 0 (fim da cadeia, fallback CPU).
    Quando current <= 0, retorna 0 (defensivo; não chamado em runtime).
    """
    if current <= 1:
        return 0
    return current // 2


def _load_persisted_stats(path: Path | None = None) -> dict:
    """Lê ~/.nyx/proxy_stats.json. Retorna dict com 'oom_recovery_count' (int).

    Tratamento defensivo (INFRA-OOM-HISTORY-01):
    - arquivo ausente: retorna {'oom_recovery_count': 0} sem warning.
    - JSON parse fail / schema inválido / version != '1': log warning + move
      para .bak via Path.rename + retorna {'oom_recovery_count': 0}.
    - permissão negada / qualquer OSError: log warning + count=0.

    NUNCA propaga exceção para não quebrar boot (ADR-001 Local First).
    """
    p = path if path is not None else Path(_PROXY_STATS_PATH)
    if not p.exists():
        return {"oom_recovery_count": 0}
    try:
        raw = p.read_text(encoding="utf-8")
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise ValueError("schema: top-level não é dict")
        if data.get("version") != "1":
            raise ValueError(f"schema: version inválida: {data.get('version')}")
        count = data.get("oom_recovery_count")
        if not isinstance(count, int) or isinstance(count, bool):
            raise ValueError(f"schema: oom_recovery_count não é int: {type(count).__name__}")
        return data
    except Exception as e:
        logger.warning("proxy_stats.json inválido (%s); criando .bak e zerando", e)
        try:
            p.rename(p.with_suffix(p.suffix + ".bak"))
        except OSError as bak_err:
            logger.warning("Falha ao criar .bak: %s", bak_err)
        return {"oom_recovery_count": 0}


def _persist_stats(state: dict, path: Path | None = None) -> None:
    """Escreve oom_recovery_count em ~/.nyx/proxy_stats.json atomicamente.

    Atomicidade via write para tmp + os.replace (POSIX). Preserva first_session
    se arquivo já existia; novo apenas na criação. last_recovery sempre
    atualiza para now (UTC iso8601).

    Falha de I/O (permissão negada, disco cheio) loga warning e segue sem
    raise -- não bloqueia o caminho de recovery do OOM (INFRA-OOM-HISTORY-01).
    """
    from datetime import datetime, timezone

    p = path if path is not None else Path(_PROXY_STATS_PATH)
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        existing: dict = {}
        if p.exists():
            try:
                existing_raw = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(existing_raw, dict):
                    existing = existing_raw
            except Exception:
                existing = {}
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = {
            "version": "1",
            "oom_recovery_count": int(state.get("oom_recovery_count", 0)),
            "first_session": existing.get("first_session") or now_iso,
            "last_recovery": now_iso,
        }
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        os.replace(tmp, p)
    except OSError as e:
        logger.warning("Falha ao persistir proxy_stats.json: %s", e)


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


def openai_to_ollama(body: dict, num_gpu: int) -> tuple[dict, str]:
    """Converte request OpenAI -> Ollama nativa.  # noqa-anonimato

    `num_gpu` é injetado pelo caller (vem de ``request.app["state"]["num_gpu"]``)
    para permitir re-tune em runtime via /admin/tune sem reiniciar o proxy.

    Retorna tupla (body_ollama, intent) para que o caller decida se aplica
    guardrail de idioma (LANG-ENFORCE-01).

    Gating por intent (PERF-INFERENCE-01 + NYX-OUTPUT-LIMITS-01):
    - num_predict resolvido por nyx.config.defaults.num_predict_for(intent, override).
    - Override explicito do request (max_tokens / max_completion_tokens) tem
      precedencia sobre o mapa por intent; ainda assim e capado por
      NUM_PREDICT_HARD_CAP (anti-runaway em CPU-bound).
    - Override via env NYX_NUM_PREDICT_OVERRIDE permite debug rapido sem editar
      codigo (ver run.sh --num-predict N).
    - Suprime tools quando intent não precisa (saudacao/chat/comando).
    - think=true so quando o modelo suporta chain-of-thought nativa
      (GAUNTLET-RAPIDO-FIXES-01 P-07).
    """
    messages = _normalize_messages(body.get("messages", []))
    last_user = _last_user_text(messages)
    intent = _classify_intent(last_user)

    has_tools = bool(body.get("tools"))
    # Suprime tools quando intent não precisa.
    if intent in ("saudacao", "chat", "comando") and has_tools:
        logger.info("intent=%s -> tools suprimidos (%d)", intent, len(body["tools"]))
        has_tools = False

    # GAUNTLET-RAPIDO-FIXES-01 (P-07): think=true so quando o modelo suporta.
    # Modelos sem chain-of-thought nativa (qwen2.5-coder, llama3.x) retornam
    # HTTP 400 "does not support thinking" se receberem think=true.
    model_name = body.get("model", _DEFAULT_MODEL)
    use_thinking = has_tools and _model_supports_thinking(model_name)

    # NYX-OUTPUT-LIMITS-01: num_predict adaptativo.
    # Mapeia o intent canônico para a chave do dict: quando ha tools no payload
    # final, usa orcamento de 'tool' (resposta tipicamente envolve tool_call +
    # resumo); senao usa o intent classificado pelo input do usuário.
    # PROXY-INTENT-CODE-BUDGET-01 (#352a): escrita de código ('code') PRESERVA o
    # budget maior (4096) mesmo com tools -- o tool_call de write_file carrega o
    # arquivo inteiro e truncava em 2048 ('tool'), invalidando o JSON.
    if has_tools:
        intent_for_budget = "code" if intent == "code" else "tool"
    else:
        intent_for_budget = intent
    max_tok_override = body.get("max_tokens") or body.get("max_completion_tokens")
    # Orçamento de SAIDA por intent (camada própria): independente da janela de
    # ENTRADA NUM_CTX (options abaixo) e do budget de compactação interno
    # ContextBudget.DEFAULT_MAX_TOKENS (nyx/agent/context.py).
    num_predict = _num_predict_for(intent_for_budget, max_tok_override)

    result: dict = {
        "model": model_name,
        "messages": messages,
        "think": use_thinking,
        "stream": False,
        "keep_alive": _KEEP_ALIVE,
        "options": {
            "num_gpu": num_gpu,
            "num_ctx": NUM_CTX,
            "num_predict": num_predict,
        },
    }
    if has_tools:
        result["tools"] = body["tools"]
    if body.get("temperature") is not None:
        result["options"]["temperature"] = body["temperature"]
    logger.info(
        "intent=%s tools=%s num_predict=%d (override=%s)",
        intent, has_tools, num_predict, bool(max_tok_override),
    )
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


# Pattern paralelo a THINK_PATTERN: captura o GRUPO interno (sem as tags).
# TUI-REDESIGN-25-09-PARTE-3: anti-débito de descarte de raciocínio.
# Em vez de strippar e perder o conteúdo, expomos como campo aditivo
# `nyx_reasoning` em choices[0].message para clientes que queiram renderizar
# o thinking (ex.: TUI mostra cinza-claro, prefixado por "Pensando:").
_THINK_CAPTURE = re.compile(r"<think>(.*?)</think>", re.DOTALL)


def _extract_think(text: str) -> str:
    """Extrai o conteúdo do PRIMEIRO bloco <think>...</think> sem as tags.

    Retorna string vazia quando não há thinking (campo deve ser omitido pelo
    callsite, não enviado como string vazia — preserva o contrato "ausente
    quando sem thinking", lição não-zero default).

    Não trata o caso de </think> órfão sem abertura porque esse formato
    (qwen3 com think=false) já é descartado por design — quando há thinking
    real, vem sempre bem-formado com <think> de abertura.
    """
    if not text:
        return ""
    match = _THINK_CAPTURE.search(text)
    if not match:
        return ""
    return match.group(1).strip()


_CODE_FENCE_PATTERN = re.compile(r"```(?:json)?\s*", re.IGNORECASE)


def _extract_tool_call_from_content(text: str, allowed_names: list[str] | None = None) -> dict | None:
    """Detecta tool_call emitido como JSON dentro do content.

    Modelos como qwen2.5-coder:3b não expõem `tool_calls` nativo do Ollama;
    emitem o tool_call como JSON dentro do content, geralmente envolvido em
    code fences. GAUNTLET-RAPIDO-FIXES-01 (P-07): normaliza para que clientes
    OpenAI-compativel recebam o formato esperado.  # noqa-anonimato

    Aceita formatos:
        ```json
        {"name": "Read", "arguments": {"file_path": "README.md"}}
        ```
        {"name": "Read", "arguments": {...}}
        {"tool": "Read", "args": {...}}

    GAUNTLET-TOOLS-DESC-MATCH-01: quando `allowed_names` é fornecido e o
    modelo alucina o `name` concatenando nome + description (ex: "Read Lê
    arquivo"), tentamos cross-validar e normalizar pegando o primeiro
    whitespace-token que casa com algum nome permitido.

    Retorna {"name": str, "arguments": str_json} ou None.
    """
    if not text:
        return None
    stripped = _CODE_FENCE_PATTERN.sub("", text).strip().rstrip("`").strip()
    start = stripped.find("{")
    if start == -1:
        # Sem JSON; tenta fallback shell-like.
        return _extract_tool_call_shell_like(text, allowed_names)
    candidate = stripped[start:]
    depth = 0
    data = None
    for i, ch in enumerate(candidate):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                try:
                    data = json.loads(candidate[: i + 1])
                    break
                except json.JSONDecodeError:
                    continue
    if not isinstance(data, dict):
        # Fallback shell-like: `tool_name arg1="val1" arg2="val2"`
        # qwen2.5-coder:3b emite write_memory nesse formato (MEMORY-INTENT-ENFORCE-01).
        return _extract_tool_call_shell_like(text, allowed_names)
    name = data.get("name") or data.get("tool") or data.get("function") or ""
    args = data.get("arguments") or data.get("args") or data.get("parameters") or {}
    if not name or not isinstance(name, str):
        return None
    if allowed_names and name not in allowed_names:
        first_token = name.split()[0] if name.split() else ""
        if first_token and first_token in allowed_names:
            logger.warning(
                "tool name corrompido pelo modelo normalizado: %r -> %r",
                name,
                first_token,
            )
            name = first_token
    if isinstance(args, dict):
        args_json = json.dumps(args, ensure_ascii=False)
    elif isinstance(args, str):
        args_json = args
    else:
        return None
    return {"name": name, "arguments": args_json}


# Pattern para sintaxe shell-like: `tool_name attr="val with spaces" other="x"`.
# qwen2.5-coder:3b ocasionalmente emite tool calls nesse formato em vez de JSON
# (MEMORY-INTENT-ENFORCE-01). Captura args com aspas duplas; valores podem ter
# espaços. Backslash-escape simples para aspas internas via `\"`.
_SHELL_ARG_PATTERN = re.compile(r'(\w+)\s*=\s*"((?:[^"\\]|\\.)*)"')


def _extract_tool_call_shell_like(text: str, allowed_names: list[str] | None) -> dict | None:
    """Parsea formato `tool_name arg1="val1" arg2="val2"`.

    Cinto-de-segurança para qwen2.5-coder:3b que emite write_memory assim.
    Requer `allowed_names` para validar o name extraído (evita falso positivo
    com palavras comuns que casariam o regex).
    """
    if not text or not allowed_names:
        return None
    stripped = _CODE_FENCE_PATTERN.sub("", text).strip()
    parts = stripped.split(None, 1)
    if not parts:
        return None
    candidate_name = parts[0].strip(".,:;!?")
    if candidate_name not in allowed_names:
        return None
    rest = parts[1] if len(parts) > 1 else ""
    args = {m.group(1): m.group(2).replace('\\"', '"') for m in _SHELL_ARG_PATTERN.finditer(rest)}
    if not args:
        return None
    logger.info(
        "tool_call extraido do content (formato shell-like %r com %d args)",
        candidate_name,
        len(args),
    )
    return {"name": candidate_name, "arguments": json.dumps(args, ensure_ascii=False)}


def ollama_to_openai(
    data: dict,
    model: str,
    has_tools_request: bool = False,
    allowed_tool_names: list[str] | None = None,
) -> dict:
    """Converte resposta Ollama nativa -> formato OpenAI.

    Se `has_tools_request` e o modelo emitiu JSON tool_call no content (formato
    não-nativo), promove para tool_calls OpenAI (GAUNTLET-RAPIDO-FIXES-01 P-07).  # noqa-anonimato
    `allowed_tool_names` habilita cross-validation contra a lista do request
    (GAUNTLET-TOOLS-DESC-MATCH-01).
    """
    msg = data.get("message", {})
    raw_content = msg.get("content", "")
    # TUI-REDESIGN-25-09-PARTE-3: captura o thinking ANTES de strippar.
    # Campo aditivo, não substitui content (que segue limpo). Clientes que
    # não conhecem nyx_reasoning ignoram silenciosamente.
    reasoning = _extract_think(raw_content)
    content = _strip_think(raw_content)
    choice: dict = {
        "index": 0,
        "message": {
            "role": msg.get("role", "assistant"),
            "content": content,
        },
        "finish_reason": "stop",
    }
    # Inserir nyx_reasoning APENAS quando não-vazio. Campo ausente quando sem
    # thinking (contrato non-zero-default; ver acceptance criteria PARTE-3).
    if reasoning:
        choice["message"]["nyx_reasoning"] = reasoning
    tool_calls = msg.get("tool_calls")
    # Fallback: quando o request tinha tools mas o modelo emitiu JSON inline.
    if not tool_calls and has_tools_request and content:
        extracted = _extract_tool_call_from_content(content, allowed_names=allowed_tool_names)
        if extracted:
            tool_calls = [{"function": extracted}]
            logger.info("tool_call extraido do content (formato JSON inline)")
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


async def _maybe_reanimate_gpu(request: web.Request, model: str) -> None:
    """INFRA-OOM-ADAPTIVE-GPU-01: reanima a GPU se degradado e a VRAM liberou.

    Opt-in (NYX_GPU_ADAPTIVE=1). Só age quando: (a) já degradou para CPU
    (state['oom_degraded']), (b) passou o cooldown desde o último OOM, e (c) o
    detect_gpu (VRAM real, já capado pela tabela de fragmentação) sugere
    num_gpu > 0. Reseta state['oom_degraded'] e restaura o num_gpu sugerido. Se
    OOMar de novo, handle_chat re-degrada e reinicia o cooldown -- 1 tentativa
    por cooldown, sem loop.
    """
    state = request.app["state"]
    if not _GPU_ADAPTIVE or not state["oom_degraded"]:
        return
    if (time.monotonic() - _OOM_LAST_TS) < _REANIMATE_COOLDOWN_S:
        return
    new_value, stderr_tail = await _detect_num_gpu_async(model=model)
    if new_value and new_value > 0:
        state["num_gpu"] = new_value
        state["oom_degraded"] = False
        logger.info(
            "OOM reanimação: VRAM liberou (free=%s MB); num_gpu 0 -> %d (NYX_GPU_ADAPTIVE)",
            _parse_vram_free_mb(stderr_tail),
            new_value,
        )


async def _retry_with_hint(
    session: ClientSession,
    base_body: dict,
    hint_text: str,
    *,
    result_transform,
    validate,
    prev_content: str | None = None,
    tag: str = "RETRY",
):
    """Helper comum aos guardrails de saída (LANG/IDENTITY/MEMORY-INTENT).

    Encapsula o padrão repetido: clona ``base_body``, anexa o turno anterior do
    assistente (``prev_content``, quando informado) + um turno do usuário com
    ``hint_text``, re-posta em ``/api/chat`` (cap 1 retry, sem loop) e converte
    a resposta via ``result_transform(data) -> dict`` no formato OpenAI. Se a
    re-resposta passa em ``validate(result) -> bool``, retorna o novo ``result``;
    caso contrário (validação falhou, HTTP != 200) retorna ``None`` e o caller
    preserva o ``result`` original. Mantém a semântica observável dos 3
    guardrails idêntica: append assistant+user hint -> re-post -> valida -> troca.
    """
    retry_body = dict(base_body)
    retry_messages = list(base_body.get("messages", []))
    if prev_content:
        retry_messages.append({"role": "assistant", "content": prev_content})
    retry_messages.append({"role": "user", "content": hint_text})
    retry_body["messages"] = retry_messages
    async with session.post(f"{OLLAMA_URL}/api/chat", json=retry_body) as resp:
        if resp.status != 200:
            logger.warning("%s: retry HTTP %d; passa adiante", tag, resp.status)
            return None
        data = await resp.json()
    candidate = result_transform(data)
    if validate(candidate):
        logger.info("%s: retry recuperou", tag)
        return candidate
    logger.info("%s: retry insistiu; passa adiante", tag)
    return None


async def _post_chat_with_oom_recovery(
    session: ClientSession,
    ollama_body: dict,
    state: dict,
    num_gpu: int,
) -> tuple[dict | None, web.Response | None]:
    """Posta em /api/chat com a cascata de recuperação OOM em 4 camadas.

    Retorna ``(data, None)`` no caminho de sucesso (resposta Ollama nativa) ou
    ``(None, error_response)`` quando deve abortar com erro HTTP. Comportamento
    observável idêntico ao bloco inline anterior (INFRA-OOM-RETRY-STEP-01):
    1) post normal; 2) se 200, devolve; 3) se erro não-OOM ou já degradado,
    devolve o erro; 4) se OOM e não-degradado: passo intermediário num_gpu//2
    (se >0) e, persistindo o OOM, fallback CPU (num_gpu=0) com
    ``state['oom_degraded']=True`` permanente. Incrementa ``oom_recovery_count``
    uma vez por recuperação e persiste via _persist_stats (INFRA-OOM-HISTORY-01).
    """
    global _OOM_LAST_TS
    async with session.post(f"{OLLAMA_URL}/api/chat", json=ollama_body) as ollama_resp:
        if ollama_resp.status == 200:
            return await ollama_resp.json(), None
        text = await ollama_resp.text()
        logger.error("Ollama %d: %s", ollama_resp.status, text[:200])
        if not (_is_oom_error(text) and not state["oom_degraded"]):
            return None, web.json_response(
                {"error": {"message": text, "type": "api_error"}},
                status=ollama_resp.status,
            )

        intermediate = _next_num_gpu_step(num_gpu)
        # 1o retry: passo intermediário (GPU parcial), apenas se intermediate > 0
        if intermediate > 0:
            logger.warning("OOM degradation step: %d -> %d", num_gpu, intermediate)
            state["num_gpu"] = intermediate
            ollama_body["options"]["num_gpu"] = intermediate
            async with session.post(f"{OLLAMA_URL}/api/chat", json=ollama_body) as inter_resp:
                if inter_resp.status == 200:
                    data = await inter_resp.json()
                    logger.info("OOM recovery OK: resposta via GPU parcial (num_gpu=%d)", intermediate)
                    state["oom_recovery_count"] = state.get("oom_recovery_count", 0) + 1
                    _persist_stats(state)  # INFRA-OOM-HISTORY-01
                    return data, None
                inter_text = await inter_resp.text()
                if not _is_oom_error(inter_text):
                    logger.error(
                        "Retry intermediário falhou (não-OOM): %d %s",
                        inter_resp.status,
                        inter_text[:200],
                    )
                    return None, web.json_response(
                        {"error": {"message": inter_text, "type": "api_error"}},
                        status=inter_resp.status,
                    )
                # OOM também no intermediário: cai para fallback CPU abaixo

        # 2o retry: fallback CPU (intermediate <= 0 OU 1o retry também deu OOM)
        state["oom_degraded"] = True
        # INFRA-OOM-ADAPTIVE-GPU-01: inicia o cooldown de reanimação.
        _OOM_LAST_TS = time.monotonic()
        state["num_gpu"] = 0
        logger.warning("OOM detectado. Degradando num_gpu=0 (CPU) para esta sessão")
        ollama_body["options"]["num_gpu"] = 0
        async with session.post(f"{OLLAMA_URL}/api/chat", json=ollama_body) as retry_resp:
            if retry_resp.status != 200:
                retry_text = await retry_resp.text()
                logger.error("Retry CPU falhou: %d %s", retry_resp.status, retry_text[:200])
                return None, web.json_response(
                    {"error": {"message": retry_text, "type": "api_error"}},
                    status=retry_resp.status,
                )
            data = await retry_resp.json()
            logger.info("OOM recovery OK: resposta via CPU")
            state["oom_recovery_count"] = state.get("oom_recovery_count", 0) + 1
            _persist_stats(state)  # INFRA-OOM-HISTORY-01
            return data, None


async def _apply_output_guardrails(
    session: ClientSession,
    ollama_body: dict,
    body: dict,
    result: dict,
    *,
    intent: str,
    model: str,
    has_tools_request: bool,
    allowed_tool_names: list[str],
) -> dict:
    """Aplica os 3 guardrails de saída em sequência via _retry_with_hint.

    Cada guardrail mantém seu gating e ordem originais (LANG -> IDENTITY ->
    MEMORY-INTENT). Cap 1 retry por guardrail (preserva P50). Retorna o
    ``result`` final (trocado se algum retry recuperou, original caso contrário).
    """
    # LANG-ENFORCE-01: guardrail de idioma em respostas conversacionais.
    # Cobre saudacao/chat/comando (qwen2.5-coder:3b frequentemente responde
    # /help em inglês). tool-needed fora do escopo: pode envolver tool_calls
    # e o content é descartado pelo agent loop.
    if intent in ("saudacao", "chat", "comando"):
        choice_msg = result["choices"][0]["message"]
        content = choice_msg.get("content", "")
        has_tc = bool(choice_msg.get("tool_calls"))
        if content and not has_tc and not _is_pt_br(content):
            logger.warning("LANG: resposta em ingles detectada (intent=%s); retry 1x com hint", intent)
            recovered = await _retry_with_hint(
                session,
                ollama_body,
                "Responda em português brasileiro. "
                "Sua resposta anterior estava em inglês; refaça em português.",
                result_transform=lambda d: ollama_to_openai(d, model),
                validate=lambda r: bool(c := r["choices"][0]["message"].get("content", "")) and _is_pt_br(c),
                prev_content=content,
                tag="LANG",
            )
            if recovered is not None:
                result = recovered

    # IDENTITY-ENFORCE-01: guardrail de identidade Nyx (ADR-005 + ADR-027).
    # Modelo (qwen2.5-coder:3b, qualquer outro) NUNCA pode mencionar nenhum
    # provider proprietário no content. Identidade Nyx é inviolável. Cobre
    # saudacao/chat/comando; tool-needed fora do escopo (content descartado).
    # noqa-anonimato -- hint do retry abaixo cita nomes intencionalmente
    if intent in ("saudacao", "chat", "comando"):
        choice_msg = result["choices"][0]["message"]
        content = choice_msg.get("content", "")
        has_tc = bool(choice_msg.get("tool_calls"))
        if content and not has_tc:
            leaked = _mentions_provider(content)
            if leaked:
                logger.warning(
                    "IDENTITY: vazamento de modelo subjacente %r detectado (intent=%s); retry 1x com hint",
                    leaked,
                    intent,
                )
                recovered = await _retry_with_hint(
                    session,
                    ollama_body,
                    "Você é Nyx, codificadora local. Não mencione modelo subjacente "
                    "(Qwen, GPT, Claude, Llama, etc.). Refaça em PT-BR sem citar IA proprietária.",  # noqa-anonimato  # noqa: ai-mention
                    result_transform=lambda d: ollama_to_openai(d, model),
                    validate=lambda r: (
                        bool(c := r["choices"][0]["message"].get("content", ""))
                        and not _mentions_provider(c)
                    ),
                    prev_content=content,
                    tag="IDENTITY",
                )
                if recovered is not None:
                    result = recovered

    # MEMORY-INTENT-ENFORCE-01: força write_memory quando usuário pede para
    # lembrar de algo (ADR-026 Agência + filosofia "infra > modelo"). Modelo
    # frequentemente responde só texto "ok, vou lembrar" sem chamar a tool.
    # Gating: intent tool-needed + wants_save_memory + write_memory disponível
    # em body['tools'] + modelo não chamou. CTX-11 do gauntlet captura.
    if intent == "tool-needed":
        last_user = _last_user_text(ollama_body.get("messages", []))
        if _wants_save_memory(last_user):
            choice_msg = result["choices"][0]["message"]
            tcs = choice_msg.get("tool_calls", []) or []
            called_wm = any(
                tc.get("function", {}).get("name") == "write_memory" for tc in tcs
            )
            wm_available = any(
                t.get("function", {}).get("name") == "write_memory"
                for t in (body.get("tools") or [])
                if isinstance(t, dict)
            )
            if wm_available and not called_wm:
                logger.warning(
                    "MEMORY: usuário pediu para lembrar; modelo não chamou write_memory; retry 1x com hint"
                )
                recovered = await _retry_with_hint(
                    session,
                    ollama_body,
                    "O usuário pediu para você LEMBRAR de algo importante. "
                    "Use a tool write_memory AGORA. Responda APENAS com JSON "
                    "no formato exato (sem texto antes/depois):\n"
                    '```json\n'
                    '{"name": "write_memory", "arguments": {'
                    '"file": "<snake_case_curto>", '
                    '"content": "<o fato a lembrar>", '
                    '"reason": "<1 linha de motivo>"}}\n'
                    '```',
                    result_transform=lambda d: ollama_to_openai(
                        d,
                        model,
                        has_tools_request=has_tools_request,
                        allowed_tool_names=allowed_tool_names or None,
                    ),
                    validate=lambda r: any(
                        tc.get("function", {}).get("name") == "write_memory"
                        for tc in (r["choices"][0]["message"].get("tool_calls", []) or [])
                    ),
                    prev_content=choice_msg.get("content", "") or None,
                    tag="MEMORY",
                )
                if recovered is not None:
                    result = recovered

    return result


async def handle_chat(request: web.Request) -> web.StreamResponse:
    body = await request.json()
    model = body.get("model", _DEFAULT_MODEL)
    state = request.app["state"]
    # INFRA-OOM-ADAPTIVE-GPU-01: antes do turno, se opt-in e degradado, tenta
    # reanimar a GPU quando a VRAM já liberou (no-op no caminho normal/não-degradado).
    await _maybe_reanimate_gpu(request, model)
    num_gpu = state["num_gpu"]
    ollama_body, intent = openai_to_ollama(body, num_gpu)

    n_tools = len(body.get("tools", []))
    logger.info("-> model=%s tools=%d intent=%s num_gpu=%d", model, n_tools, intent, num_gpu)

    session = await _get_session(request.app)
    data, error = await _post_chat_with_oom_recovery(session, ollama_body, state, num_gpu)
    if error is not None:
        return error

    logger.info("Ollama raw keys: %s", list(data.get("message", {}).keys()))
    logger.info("Ollama tool_calls: %s", data.get("message", {}).get("tool_calls", "NONE"))
    has_tools_request = bool(body.get("tools"))
    allowed_tool_names = [
        t.get("function", {}).get("name", "")
        for t in body.get("tools", [])
        if isinstance(t, dict)
    ]
    allowed_tool_names = [n for n in allowed_tool_names if n]
    result = ollama_to_openai(
        data,
        model,
        has_tools_request=has_tools_request,
        allowed_tool_names=allowed_tool_names or None,
    )

    result = await _apply_output_guardrails(
        session,
        ollama_body,
        body,
        result,
        intent=intent,
        model=model,
        has_tools_request=has_tools_request,
        allowed_tool_names=allowed_tool_names,
    )

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


# UX-LIFECYCLE-01: endpoint de shutdown gracioso. Aceita apenas loopback
# (127.0.0.1 / ::1). Responde 200 antes de derrubar o loop para que o
# cliente receba confirmação. Útil para o CLI sinalizar fim de sessão
# sem depender exclusivamente de SIGTERM do shell wrapper.
_LOOPBACK_HOSTS: tuple[str, ...] = ("127.0.0.1", "::1")


async def _delayed_shutdown(delay_s: float = 0.5) -> None:
    """Aguarda resposta sair e envia SIGTERM ao próprio processo."""
    await asyncio.sleep(delay_s)
    logger.info("shutdown executando SIGTERM no PID=%d", os.getpid())
    try:
        os.kill(os.getpid(), signal.SIGTERM)
    except OSError as exc:
        logger.warning("falha ao auto-SIGTERM: %s", exc)
        sys.exit(0)


async def handle_shutdown(request: web.Request) -> web.Response:
    """Encerra o proxy graciosamente. Rejeita não-loopback com HTTP 403."""
    remote = request.remote or ""
    if remote not in _LOOPBACK_HOSTS:
        logger.warning("shutdown rejeitado: remote=%s não-loopback", remote)
        return web.json_response({"error": "loopback only"}, status=403)
    logger.info("shutdown solicitado via /admin/shutdown (remote=%s)", remote)
    asyncio.create_task(_delayed_shutdown())
    return web.json_response({"status": "shutting_down"})


# PROXY-NUMGPU-RUNTIME-01: re-tune proativo em runtime.
# detect_gpu.py corre fora do event loop via asyncio.create_subprocess_exec
# (argv separado, sem shell -- imune a injection). Loopback-only por ADR-001.
_TUNE_MODEL_PATTERN = re.compile(r"^[A-Za-z0-9._:\-]{1,64}$")


async def _detect_num_gpu_async(model: str = "qwen3:4b", timeout_s: float = 15.0) -> tuple[int | None, str]:
    """Executa scripts/detect_gpu.py --for-model <model> em subprocess assíncrono.

    Retorna (num_gpu | None, stderr_tail). num_gpu=None indica falha de parsing
    ou timeout; caller decide manter snapshot atual. `model` é validado contra
    regex restritiva antes de virar argv (defesa em profundidade, mesmo já
    sendo argv-list).
    """
    if not _TUNE_MODEL_PATTERN.match(model):
        return None, f"modelo inválido: {model[:40]}"
    script = _PROJECT_ROOT / "scripts" / "detect_gpu.py"
    proc = await asyncio.create_subprocess_exec(
        sys.executable,
        str(script),
        "--for-model",
        model,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout_s)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return None, "timeout"
    stderr_text = stderr.decode("utf-8", errors="replace").strip()
    if proc.returncode != 0:
        return None, stderr_text[-200:]
    raw = stdout.decode("utf-8", errors="replace").strip()
    try:
        return int(raw or "0"), stderr_text[-200:]
    except ValueError:
        return None, f"stdout não-inteiro: {raw[:80]}"


def _parse_vram_free_mb(stderr_tail: str) -> int | None:
    """Extrai vram_free do log do detect_gpu.py.

    Formato esperado em stderr: ``... vram_free=3706MB ...``. Retorna None se
    não casar (caller exibe 'desconhecido').
    """
    match = re.search(r"vram_free=(\d+)\s*MB", stderr_tail)
    if not match:
        return None
    return int(match.group(1))


async def handle_tune(request: web.Request) -> web.Response:
    """Re-roda detect_gpu.py e atualiza app['num_gpu'] live (loopback-only).

    Retorna JSON: ``{old_num_gpu, new_num_gpu, vram_free_mb, changed, oom_degraded}``.
    Se OOM já degradou, num_gpu permanece 0 (não sobrescreve fail-safe) e
    ``oom_degraded=true`` sinaliza ao caller que tune fica capado em 0.
    """
    remote = request.remote or ""
    if remote not in _LOOPBACK_HOSTS:
        logger.warning("tune rejeitado: remote=%s não-loopback", remote)
        return web.json_response({"error": "loopback only"}, status=403)

    model = request.query.get("model", "qwen3:4b")
    new_value, stderr_tail = await _detect_num_gpu_async(model=model)
    vram_free_mb = _parse_vram_free_mb(stderr_tail)
    state = request.app["state"]
    old = state["num_gpu"]

    if new_value is None:
        logger.warning("tune: detect_gpu falhou (%s); mantendo num_gpu=%d", stderr_tail[:80], old)
        return web.json_response(
            {
                "old_num_gpu": old,
                "new_num_gpu": old,
                "vram_free_mb": vram_free_mb,
                "changed": False,
                "oom_degraded": state["oom_degraded"],
                "error": "detect_gpu falhou",
                "stderr": stderr_tail[:200],
            },
            status=500,
        )

    if state["oom_degraded"]:
        # Fail-safe vence: tune não reanima GPU após OOM nesta sessão.
        logger.info("tune: OOM já degradou; preservando num_gpu=0 (sugerido seria %d)", new_value)
        return web.json_response(
            {
                "old_num_gpu": old,
                "new_num_gpu": old,
                "vram_free_mb": vram_free_mb,
                "changed": False,
                "oom_degraded": True,
                "suggested": new_value,
            }
        )

    state["num_gpu"] = new_value
    changed = old != new_value
    logger.info(
        "tune: num_gpu %d -> %d (vram_free=%s MB, model=%s)",
        old,
        new_value,
        vram_free_mb if vram_free_mb is not None else "?",
        model,
    )
    return web.json_response(
        {
            "old_num_gpu": old,
            "new_num_gpu": new_value,
            "vram_free_mb": vram_free_mb,
            "changed": changed,
            "oom_degraded": False,
        }
    )


async def handle_stats(request: web.Request) -> web.Response:
    """Retorna snapshot de estado do proxy (loopback-only).

    JSON: {oom_recovery_count, num_gpu_current, num_gpu_initial, oom_degraded}.
    Leitura pura; não muta estado. Útil para diagnosticar sessões longas
    sem grep no log (ver INFRA-OOM-02).
    """
    remote = request.remote or ""
    if remote not in _LOOPBACK_HOSTS:
        logger.warning("stats rejeitado: remote=%s não-loopback", remote)
        return web.json_response({"error": "loopback only"}, status=403)

    state = request.app["state"]
    return web.json_response(
        {
            "oom_recovery_count": state.get("oom_recovery_count", 0),
            "num_gpu_current": state.get("num_gpu", 0),
            "num_gpu_initial": state.get("num_gpu_initial", state.get("num_gpu", 0)),
            "oom_degraded": state.get("oom_degraded", False),
        }
    )


async def _on_startup(app: web.Application) -> None:
    app["http_session"] = ClientSession(timeout=ClientTimeout(total=600))
    # PROXY-NUMGPU-RUNTIME-01: aiohttp deprecia mutação de app[...] após
    # startup. Guardamos o estado dinâmico num dict interno (app["state"])
    # para mutar valores em runtime sem violar a API. main() prepara o dict
    # antes do startup com o num_gpu da CLI; defaults aplicados se ausente.
    state = app.setdefault("state", {})
    state.setdefault("num_gpu", _INITIAL_NUM_GPU)
    state.setdefault("num_gpu_initial", state["num_gpu"])
    state.setdefault("oom_recovery_count", 0)
    # PROXY-HANDLE-CHAT-REFACTOR-01: fail-safe anti-oscilação OOM migrado de
    # módulo-global para o dict de estado (coerência com num_gpu/oom_recovery_count).
    # aiohttp roda single-threaded no event loop: a mutação de state é segura
    # entre awaits porque cada seção crítica (checar -> escrever oom_degraded) não
    # contém await no meio; um handler nunca é preemptado fora de um ponto await.
    state.setdefault("oom_degraded", False)
    # INFRA-OOM-HISTORY-01: hidrata contador cross-session se arquivo existir.
    persisted = _load_persisted_stats()
    if persisted.get("oom_recovery_count", 0) > 0:
        state["oom_recovery_count"] = persisted["oom_recovery_count"]
        logger.info(
            "Hidratando oom_recovery_count=%d do arquivo persistido",
            state["oom_recovery_count"],
        )
    logger.info("Sessão HTTP criada (num_gpu inicial=%d)", state["num_gpu"])


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

    global OLLAMA_URL, NUM_CTX
    OLLAMA_URL = f"http://127.0.0.1:{args.ollama_port}"
    NUM_CTX = args.num_ctx

    logger.info("Proxy :%d -> Ollama :%d (num_gpu=%d, think=false)", args.port, args.ollama_port, args.num_gpu)

    app = web.Application()
    # PROXY-NUMGPU-RUNTIME-01: snapshot inicial vai pelo dict state interno;
    # pode ser re-tunado em runtime via GET /admin/tune sem reiniciar o proxy.
    # _on_startup garante a chave 'state' e popula num_gpu se ausente.
    app["state"] = {
        "num_gpu": args.num_gpu,
        "num_gpu_initial": args.num_gpu,
        "oom_recovery_count": 0,
        "oom_degraded": False,
    }
    app.on_startup.append(_on_startup)
    app.on_cleanup.append(_on_cleanup)
    app.router.add_post("/v1/chat/completions", handle_chat)
    app.router.add_get("/v1/models", handle_models)
    app.router.add_get("/v1/models/{model_id}", handle_model)
    app.router.add_get("/health", handle_health)
    app.router.add_post("/admin/shutdown", handle_shutdown)
    app.router.add_get("/admin/tune", handle_tune)
    app.router.add_get("/admin/stats", handle_stats)
    web.run_app(app, host="127.0.0.1", port=args.port, print=None)


if __name__ == "__main__":
    main()


# "Entre o estímulo e a resposta há um espaço." -- Viktor Frankl
