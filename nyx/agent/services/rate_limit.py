"""RateLimitService -- Rate limiting local."""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger("nyx.services.rate_limit")

DATA_DIR = Path.home() / ".nyx" / "rate_limit"


class RateLimitService:
    """Service: Rate limiting local."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("RateLimitService inicializado")

    def status(self) -> dict:
        """Retorna estado do service."""
        return {"service": "rate_limit", "ativo": True}


# "Entre o estímulo e a resposta há um espaço." -- Viktor Frankl
