"""Analytics -- Métricas locais de uso."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.analytics")

DATA_DIR = Path.home() / ".nyx" / "analytics"


class Analytics:
    """Service: Métricas locais de uso."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Analytics inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "analytics", "ativo": True}


# "Medir é o primeiro passo para controlar." -- H. James Harrington
