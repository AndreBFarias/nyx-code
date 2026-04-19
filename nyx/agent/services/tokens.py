"""Token Estimation -- Heurística de contagem de tokens.

Heurística local sem API: len(text) / bytes_per_token.
JSON é mais denso (~2 bytes/token), texto normal ~4 bytes/token.
"""

from __future__ import annotations

from pathlib import Path

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.services.tokens")

DEFAULT_BYTES_PER_TOKEN = 4

FILE_TYPE_RATIOS: dict[str, int] = {
    ".json": 2,
    ".jsonl": 2,
    ".jsonc": 2,
    ".xml": 3,
    ".html": 3,
    ".yaml": 3,
    ".yml": 3,
    ".css": 3,
}


def estimate_tokens(text: str, bytes_per_token: int = DEFAULT_BYTES_PER_TOKEN) -> int:
    """Estimativa rápida de tokens sem dependência externa."""
    if not text:
        return 0
    return max(1, len(text) // bytes_per_token)


def estimate_tokens_for_file(content: str, file_path: str) -> int:
    """Estimativa ajustada pelo tipo de arquivo."""
    ext = Path(file_path).suffix.lower()
    ratio = FILE_TYPE_RATIOS.get(ext, DEFAULT_BYTES_PER_TOKEN)
    return estimate_tokens(content, ratio)


def estimate_messages_tokens(messages: list[dict]) -> int:
    """Estima tokens de uma lista de mensagens no formato LLM."""
    total = 0
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    text = block.get("text", "")
                    total += estimate_tokens(text)
                elif isinstance(block, str):
                    total += estimate_tokens(block)
    return total


def format_token_count(tokens: int) -> str:
    """Formata contagem de tokens para exibição."""
    if tokens < 1000:
        return f"{tokens}tok"
    if tokens < 10000:
        return f"{tokens / 1000:.1f}k tok"
    return f"{tokens // 1000}k tok"


# "Medir é saber." -- Lord Kelvin
