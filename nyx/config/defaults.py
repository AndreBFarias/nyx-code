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
