"""Notifier -- Notificações desktop via notify-send."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.notifier")

DATA_DIR = Path.home() / ".nyx" / "notifier"


class Notifier:
    """Service: Notificações desktop via notify-send."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Notifier inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "notifier", "ativo": True}


# "A abstração é a arma mais poderosa do programador." -- Edsger Dijkstra
