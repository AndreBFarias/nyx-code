"""Constantes e valores padrão do Nyx-Code."""

from __future__ import annotations

import os

# PID file para single-instance (UX-LIFECYCLE-01).
# Fonte única consumida por run.sh + nyx.agent.services.lifecycle.
# Override via env var `NYX_PID_FILE` (test isolation, multi-projeto).
# Default em /tmp por convenção POSIX para lock files de processo único.
NYX_PID_FILE: str = os.environ.get("NYX_PID_FILE", "/tmp/nyx.pid")  # noqa: abs-path

# MCP (Model Context Protocol) config file. Lido por nyx.agent.services.mcp_client.
# Override via env var NYX_MCP_CONFIG (test isolation, multi-projeto).
NYX_MCP_CONFIG: str = os.environ.get(
    "NYX_MCP_CONFIG",
    str(__import__("pathlib").Path.home() / ".nyx" / "mcp.json"),
)

# Plugins instaláveis (PLUGINS-01). Cada subdiretório é um plugin com manifest.toml.
NYX_PLUGINS_DIR: str = os.environ.get(
    "NYX_PLUGINS_DIR",
    str(__import__("pathlib").Path.home() / ".nyx" / "plugins"),
)

# Stats persistidos do proxy (INFRA-OOM-HISTORY-01). Mantem oom_recovery_count
# cross-session para auditoria longitudinal de instabilidade. JSON pequeno,
# atomico via tmp + os.replace. Override via NYX_PROXY_STATS_PATH (test isolation).
PROXY_STATS_PATH: str = os.environ.get(
    "NYX_PROXY_STATS_PATH",
    str(__import__("pathlib").Path.home() / ".nyx" / "proxy_stats.json"),
)

# Cockpit (COCKPIT-01). FastAPI server bind 127.0.0.1 apenas.
COCKPIT_PORT: int = int(os.environ.get("NYX_COCKPIT_PORT", "11437"))
COCKPIT_HOST: str = "127.0.0.1"

# Estetica (VISUAL-LAYOUT-08). Aesthetic + entity ativos lidos por
# nyx.themes.design_tokens_extended.get_active().
# Aesthetics validos: default | arcano | cyberpunk | brutalist | mecha | editorial
# Entities validas: nyx | eris | juno | lars | luna | mars | somn
NYX_AESTHETIC: str = os.environ.get("NYX_AESTHETIC", "default")
NYX_ENTITY: str = os.environ.get("NYX_ENTITY", "nyx")

OLLAMA_PORT: int = 11435
PROXY_PORT: int = 11436
# Contrato dual:
# - NYX_OLLAMA_HOST (interno, consumido por Nyx/Python): host puro, sem porta.
# - OLLAMA_HOST exportado (daemon Ollama externo): host:port, convenção upstream.
# run.sh monta a composição no momento do export; este default é o host puro.
OLLAMA_HOST: str = "127.0.0.1"
OLLAMA_URL: str = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
PROXY_URL: str = f"http://{OLLAMA_HOST}:{PROXY_PORT}"
PROXY_V1_URL: str = f"{PROXY_URL}/v1"
DEFAULT_MODEL: str = "qwen2.5-coder:3b"

# Modelos Ollama que suportam o parametro `think` (chain-of-thought nativa).
# Qwen3 com sufixo *-thinking aceita. qwen2.5-coder, llama3.x e similares
# rejeitam com HTTP 400 "does not support thinking" se o proxy enviar think=true.
# GAUNTLET-RAPIDO-FIXES-01 (P-07): centraliza a decisao aqui (N-para-N).
MODELS_SUPPORTING_THINKING: tuple[str, ...] = (
    "qwen3",
)


def model_supports_thinking(model: str) -> bool:
    """Retorna True se o modelo aceita o parametro `think` do Ollama."""
    name = (model or "").lower()
    return any(prefix in name for prefix in MODELS_SUPPORTING_THINKING)

VRAM_MAX_GB: float = 2.5
MAX_ITERATIONS: int = 50
TEMPERATURE: float = 0.3
MAX_TOKENS: int = 2048
# Janela de ENTRADA do Ollama (num_ctx enviado ao modelo). E uma das tres
# camadas independentes de "contexto"; não confundir com:
#   - ContextBudget.DEFAULT_MAX_TOKENS (nyx/agent/context.py): gatilho de
#     compactação INTERNO do histórico, deliberadamente conservador.
#   - NUM_PREDICT_BY_INTENT / num_predict_for (abaixo): orçamento de SAIDA.
NUM_CTX: int = 4096
CURL_TIMEOUT: int = 10
OLLAMA_START_TIMEOUT: int = 30

# INFRA-NUM-GPU-RECONCILE-01: estes valores sao INERTES no boot real.
# A fonte de verdade do num_gpu e o auto-tune (scripts/detect_gpu.py),
# que run.sh injeta sempre via --num-gpu (12 ou cap por VRAM). Em proxy.py
# o argparse `--num-gpu default=15` popula app["state"]["num_gpu"] ANTES do
# _on_startup, entao o setdefault(_INITIAL_NUM_GPU=NUM_GPU_3B) nunca alcanca
# o -1. Mantidos apenas como fallback teorico / espelho de model_tier.
NUM_GPU_7B: int = 18
NUM_GPU_3B: int = -1

# Orcamento de tokens de saida por categoria de turno (PERF-INFERENCE-01).
# Em CPU-bound (RTX 3050 4GB com 25/37 layers em RAM) o modelo gera ~16 tok/s,
# entao cada token de "thinking" inutil custa caro. Cap agressivo p/ chat.
#
# NYX-OUTPUT-LIMITS-01: num_predict adaptativo por intent.
# - saudacao: oi/ola, respostas <50 tok
# - comando : slash hibrido, eventualmente precisa breve resposta
# - chat    : explicacao curta
# - tool    : tool call + resumo subsequente
# - code    : geracao de codigo (write_file, edit_file)
# - plan    : /plan, refactor amplo, documentacao tecnica
# - default : qualquer intent não mapeado
NUM_PREDICT_BY_INTENT: dict[str, int] = {
    "saudacao": 80,
    "comando": 120,
    "chat": 512,
    "tool": 2048,
    "tool-needed": 2048,
    "code": 4096,
    "plan": 8192,
    "default": 1024,
}

# Hard cap anti-runaway. Mesmo override explicito do request não ultrapassa.
NUM_PREDICT_HARD_CAP: int = 8192

# Compatibilidade retroativa: codigo existente (e gauntlet/perf fixtures) ainda
# importa estes nomes. Permanecem espelhando os defaults pre-OUTPUT-LIMITS-01.
NUM_PREDICT_CHAT: int = NUM_PREDICT_BY_INTENT["chat"]
NUM_PREDICT_TOOL: int = NUM_PREDICT_BY_INTENT["tool"]


def num_predict_for(intent: str, override: int | None = None) -> int:
    """Resolve num_predict por intent. Override (env ou request) tem precedencia.

    Precedencia:
    1. override numerico explicito (max_tokens do request).
    2. NYX_NUM_PREDICT_OVERRIDE no env (debug/CLI).
    3. mapa NUM_PREDICT_BY_INTENT[intent].
    4. NUM_PREDICT_BY_INTENT['default'] (fallback).

    Aplicar NUM_PREDICT_HARD_CAP sempre, mesmo em overrides, evita runaway
    em CPU-bound (RTX 3050 4GB gera ~16 tok/s; 32k tokens = 33 minutos).
    """
    if isinstance(override, bool):
        override = None  # bool e subtipo de int; evitar True=1 silencioso
    if isinstance(override, int) and override > 0:
        return min(override, NUM_PREDICT_HARD_CAP)
    if isinstance(override, str) and override.isdigit():
        return min(int(override), NUM_PREDICT_HARD_CAP)
    env_override = os.environ.get("NYX_NUM_PREDICT_OVERRIDE", "").strip()
    if env_override.isdigit():
        return min(int(env_override), NUM_PREDICT_HARD_CAP)
    key = (intent or "").lower().strip()
    return NUM_PREDICT_BY_INTENT.get(key, NUM_PREDICT_BY_INTENT["default"])

# Manter modelo carregado em VRAM entre chamadas evita o load_duration de
# ~7s que ocorre no cold start.
OLLAMA_KEEP_ALIVE: str = "30m"


# "A simplicidade é a sofisticação suprema." -- Leonardo da Vinci
