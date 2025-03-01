"""Constantes e valores padrão do Nyx-Code."""

from __future__ import annotations

OLLAMA_PORT: int = 11435
OLLAMA_HOST: str = "127.0.0.1"
DEFAULT_MODEL: str = "qwen3:4b"
VRAM_MAX_GB: float = 2.5
MAX_ITERATIONS: int = 50
TEMPERATURE: float = 0.3
MAX_TOKENS: int = 2048
NUM_CTX: int = 16384
CURL_TIMEOUT: int = 10
OLLAMA_START_TIMEOUT: int = 30

NUM_GPU_7B: int = 18
NUM_GPU_3B: int = -1


# "A simplicidade é a sofisticação suprema." -- Leonardo da Vinci
