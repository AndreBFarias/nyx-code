"""TipsService -- Dicas contextuais."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.tips")

DATA_DIR = Path.home() / ".nyx" / "tips"


class TipsService:
    """Service: Dicas contextuais."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("TipsService inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "tips", "ativo": True}


# "A preguiça é a mãe da invenção." -- Agatha Christie
