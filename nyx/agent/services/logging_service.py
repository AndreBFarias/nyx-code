"""InternalLogging -- Logging estruturado rotacionado para o Nyx."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

logger = logging.getLogger("nyx.services.logging_service")

LOGS_DIR = Path.home() / ".nyx" / "logs"
LOG_FILE = LOGS_DIR / "nyx.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3

_INITIALIZED = False


def get_logger(name: str) -> logging.Logger:
    """Retorna logger garantindo que InternalLogging foi inicializado.

    Idempotente: inicializa o handler rotacionado apenas na primeira chamada.
    Todos os módulos do nyx devem usar esta função em vez de logging.getLogger,
    exceto logging_service.py (self) e nyx/proxy.py (standalone, basicConfig próprio).
    """
    global _INITIALIZED
    if not _INITIALIZED:
        InternalLogging()
        _INITIALIZED = True
    return logging.getLogger(name)


class InternalLogging:
    """Logging rotacionado para ~/.nyx/logs/nyx.log."""

    def __init__(self) -> None:
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self._handler = RotatingFileHandler(
            str(LOG_FILE),
            maxBytes=MAX_BYTES,
            backupCount=BACKUP_COUNT,
            encoding="utf-8",
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(name)s] %(levelname)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self._handler.setFormatter(formatter)

        nyx_logger = logging.getLogger("nyx")
        if not any(isinstance(h, RotatingFileHandler) for h in nyx_logger.handlers):
            nyx_logger.addHandler(self._handler)
            nyx_logger.setLevel(logging.INFO)
        nyx_logger.propagate = False

        logger.info("Logging rotacionado ativo: %s", LOG_FILE)

    def status(self) -> dict:
        size_kb = LOG_FILE.stat().st_size / 1024 if LOG_FILE.exists() else 0
        backups = len(list(LOGS_DIR.glob("nyx.log.*")))
        return {
            "service": "logging",
            "ativo": True,
            "log_file": str(LOG_FILE),
            "size_kb": round(size_kb, 1),
            "backups": backups,
        }


# "A simplicidade é o último grau de sofisticação." -- Leonardo da Vinci
