"""Auto-Compact -- Compactação automática do histórico.

Monitora o budget de contexto e compacta automaticamente
quando o threshold é ultrapassado.
"""

from __future__ import annotations

import logging

from nyx.agent.context import ContextBudget
from nyx.agent.session import CodeSession

logger = logging.getLogger("nyx.services.compact")

AUTO_COMPACT_THRESHOLD = 0.6


class AutoCompactService:
    """Serviço que monitora e compacta histórico automaticamente."""

    def __init__(self, budget: ContextBudget) -> None:
        self._budget = budget
        self._compactions: int = 0
        self._last_level: int = 0

    def check_and_compact(self, session: CodeSession, system_prompt: str) -> bool:
        """Verifica budget e compacta se necessário. Retorna True se compactou."""
        if not self._budget.should_compact(session):
            return False

        level = self._budget.get_compaction_level(session)
        if level <= self._last_level and self._compactions > 0:
            return False

        history = self._budget.compact_history(session)
        self._compactions += 1
        self._last_level = level

        logger.info(
            "[auto-compact] nível %d, compactação #%d, histórico: %d chars",
            level,
            self._compactions,
            len(history),
        )
        return True

    @property
    def compaction_count(self) -> int:
        return self._compactions

    @property
    def last_level(self) -> int:
        return self._last_level

    def get_status(self) -> dict:
        return {
            "compactions": self._compactions,
            "last_level": self._last_level,
        }


# "Compactar é a arte de dizer mais com menos." -- Antoine de Saint-Exupéry
