"""SummaryExpanded -- Resumo expandido de sessão."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.summary_expanded")

DATA_DIR = Path.home() / ".nyx" / "summary_expanded"


class SummaryExpanded:
    """Service: Resumo expandido de sessão."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("SummaryExpanded inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "summary_expanded", "ativo": True}


# "O terminal é o lar do programador." -- Ken Thompson
