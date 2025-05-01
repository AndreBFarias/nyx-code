"""AwaySummary -- Resumo de atividades ausentes."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.away_summary")

DATA_DIR = Path.home() / ".nyx" / "away_summary"


class AwaySummary:
    """Service: Resumo de atividades ausentes."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("AwaySummary inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "away_summary", "ativo": True}


# "A abstração é a arma mais poderosa do programador." -- Edsger Dijkstra
