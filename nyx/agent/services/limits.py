"""LimitsService -- Controle de limites de uso."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.limits")

DATA_DIR = Path.home() / ".nyx" / "limits"


class LimitsService:
    """Service: Controle de limites de uso."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("LimitsService inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "limits", "ativo": True}


# "A preguiça é a mãe da invenção." -- Agatha Christie
