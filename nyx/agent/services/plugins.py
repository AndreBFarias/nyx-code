"""PluginsService -- Gerenciamento de plugins."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.plugins")

DATA_DIR = Path.home() / ".nyx" / "plugins"


class PluginsService:
    """Service: Gerenciamento de plugins."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("PluginsService inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "plugins", "ativo": True}


# "O terminal é o lar do programador." -- Ken Thompson
