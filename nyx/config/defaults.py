"""Constantes e valores padrão do Nyx-Code."""

from __future__ import annotations

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
NUM_CTX: int = 4096
CURL_TIMEOUT: int = 10
OLLAMA_START_TIMEOUT: int = 30

NUM_GPU_7B: int = 18
NUM_GPU_3B: int = -1

# Orcamento de tokens de saida por categoria de turno (PERF-INFERENCE-01).
# Em CPU-bound (RTX 3050 4GB com 25/37 layers em RAM) o modelo gera ~16 tok/s,
# entao cada token de "thinking" inutil custa caro. Cap agressivo p/ chat.
NUM_PREDICT_CHAT: int = 80
NUM_PREDICT_TOOL: int = 512
# Manter modelo carregado em VRAM entre chamadas evita o load_duration de
# ~7s que ocorre no cold start.
OLLAMA_KEEP_ALIVE: str = "30m"


# "A simplicidade é a sofisticação suprema." -- Leonardo da Vinci
