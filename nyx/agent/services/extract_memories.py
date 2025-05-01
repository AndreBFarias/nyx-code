"""ExtractMemories -- Extração automática de memórias."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.extract_memories")

DATA_DIR = Path.home() / ".nyx" / "extract_memories"


class ExtractMemories:
    """Service: Extração automática de memórias."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("ExtractMemories inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "extract_memories", "ativo": True}


# "Paciência é a companheira da sabedoria." -- Santo Agostinho
