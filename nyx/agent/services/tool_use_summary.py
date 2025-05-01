"""ToolUseSummary -- Resumo de uso de tools."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.tool_use_summary")

DATA_DIR = Path.home() / ".nyx" / "tool_use_summary"


class ToolUseSummary:
    """Service: Resumo de uso de tools."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("ToolUseSummary inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "tool_use_summary", "ativo": True}


# "A ordem é o primeiro passo para a liberdade." -- Aristóteles
