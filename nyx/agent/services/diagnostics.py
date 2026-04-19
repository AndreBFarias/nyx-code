"""DiagnosticTracking -- Tracking de erros, warnings e falhas."""

from __future__ import annotations

import time
from dataclasses import dataclass

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.services.diagnostics")


@dataclass
class DiagnosticEntry:
    level: str
    source: str
    message: str
    timestamp: float = 0.0


class DiagnosticTracking:
    """Rastreia erros e falhas para alimentar /doctor."""

    def __init__(self) -> None:
        self._entries: list[DiagnosticEntry] = []
        self._error_count: int = 0
        self._warning_count: int = 0

    def record_error(self, source: str, message: str) -> None:
        self._entries.append(
            DiagnosticEntry(
                level="error",
                source=source,
                message=message,
                timestamp=time.time(),
            )
        )
        self._error_count += 1
        logger.error("[diag] %s: %s", source, message)

    def record_warning(self, source: str, message: str) -> None:
        self._entries.append(
            DiagnosticEntry(
                level="warning",
                source=source,
                message=message,
                timestamp=time.time(),
            )
        )
        self._warning_count += 1
        logger.warning("[diag] %s: %s", source, message)

    def get_recent(self, n: int = 10) -> list[DiagnosticEntry]:
        return self._entries[-n:]

    def get_summary(self) -> str:
        if not self._entries:
            return "  Nenhum diagnóstico registrado."
        lines = [f"  Diagnósticos ({self._error_count} erros, {self._warning_count} avisos):"]
        for e in self._entries[-5:]:
            lines.append(f"    [{e.level}] {e.source}: {e.message[:80]}")
        return "\n".join(lines)

    def status(self) -> dict:
        return {
            "service": "diagnostics",
            "ativo": True,
            "errors": self._error_count,
            "warnings": self._warning_count,
            "total_entries": len(self._entries),
        }


# "Entre o estímulo e a resposta há um espaço." -- Viktor Frankl
