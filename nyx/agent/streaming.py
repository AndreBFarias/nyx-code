"""Streaming de tokens -- Exibição em tempo real da resposta do LLM.

Port de Luna src/skills/code_agent/streaming.py.

Arquitetura:
- Tokens são impressos na tela conforme chegam (visual)
- Buffer acumula texto completo para o parser (lógica)
- Impressão para ao detectar 'ACTION:' (parte estruturada)
"""

from __future__ import annotations

import logging
import re
import sys
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("nyx.streaming")

StreamTokenCallback = Callable[[str], None]

_ACTION_TRIGGER = re.compile(r"\bACTION\s*[:=]", re.IGNORECASE)


class StreamingCollector:
    def __init__(self, on_token: StreamTokenCallback | None = None) -> None:
        self._on_token = on_token
        self._buffer: list[str] = []
        self._char_count: int = 0
        self._action_detected: bool = False
        self._recent_window: str = ""

    def feed(self, token: str) -> None:
        """Alimenta um token ao collector."""
        self._buffer.append(token)
        self._char_count += len(token)
        self._recent_window += token
        if len(self._recent_window) > 50:
            self._recent_window = self._recent_window[-50:]

        if not self._action_detected:
            if _ACTION_TRIGGER.search(self._recent_window):
                self._action_detected = True
                if self._on_token:
                    self._on_token("\n")
            elif self._on_token:
                self._on_token(token)

    def get_text(self) -> str:
        return "".join(self._buffer)

    def reset(self) -> None:
        self._buffer.clear()
        self._char_count = 0
        self._action_detected = False
        self._recent_window = ""

    @property
    def char_count(self) -> int:
        return self._char_count

    @property
    def action_detected(self) -> bool:
        return self._action_detected


def create_streaming_callback(write_func: Callable[[str], None] | None = None) -> StreamTokenCallback:
    """Cria callback padrão que escreve no stdout."""

    def _default_write(token: str) -> None:
        sys.stdout.write(token)
        sys.stdout.flush()

    writer = write_func or _default_write

    def _on_token(token: str) -> None:
        writer(token)

    return _on_token


def create_rich_streaming_callback() -> StreamTokenCallback | None:
    """Cria callback Rich se disponível."""
    try:
        from rich.console import Console

        console = Console(highlight=False)

        def _on_token(token: str) -> None:
            console.print(token, end="", highlight=False)

        return _on_token
    except ImportError:
        return None


# "O rio que tudo arrasta é chamado violento, mas ninguém chama violentas
#  as margens que o comprimem." -- Bertolt Brecht
