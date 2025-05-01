"""DiagnosticTracking -- Tracking de erros e warnings."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.diagnostics")

DATA_DIR = Path.home() / ".nyx" / "diagnostics"


class DiagnosticTracking:
    """Service: Tracking de erros e warnings."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("DiagnosticTracking inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "diagnostics", "ativo": True}


# "Entre o estímulo e a resposta há um espaço." -- Viktor Frankl
