"""PreventSleep -- Previne sleep durante operações longas."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.prevent_sleep")

DATA_DIR = Path.home() / ".nyx" / "prevent_sleep"


class PreventSleep:
    """Service: Previne sleep durante operações longas."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("PreventSleep inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "prevent_sleep", "ativo": True}


# "A ordem é o primeiro passo para a liberdade." -- Aristóteles
