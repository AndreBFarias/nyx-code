"""InternalLogging -- Logging estruturado rotacionado."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.logging_service")

DATA_DIR = Path.home() / ".nyx" / "logging_service"


class InternalLogging:
    """Service: Logging estruturado rotacionado."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("InternalLogging inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "logging_service", "ativo": True}


# "A simplicidade é o último grau de sofisticação." -- Leonardo da Vinci
