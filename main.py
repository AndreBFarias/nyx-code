"""Nyx-Code -- Entry point."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from nyx.config.settings import load_settings


def _setup_logging(debug: bool) -> None:
    """Configura logging rotacionado."""
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)

    handlers: list[logging.Handler] = []

    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler(
        log_dir / "nyx.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    handlers.append(file_handler)

    if debug:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        handlers.append(console_handler)

    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )


def main() -> int:
    """Ponto de entrada principal."""
    parser = argparse.ArgumentParser(description="Nyx-Code - Agente de código local")
    parser.add_argument("--model", default="qwen2.5-coder:3b", help="Modelo Ollama")
    parser.add_argument("--port", type=int, default=11435, help="Porta do Ollama")
    parser.add_argument("--debug", action="store_true", help="Modo debug")
    parser.add_argument("--headless", action="store_true", help="Modo headless (integração Luna)")
    args = parser.parse_args()

    settings = load_settings(args)
    _setup_logging(settings.debug)

    logger = logging.getLogger("nyx")
    logger.info(f"Nyx-Code iniciando: model={settings.model}, port={settings.ollama_port}")

    # Sprint 2: importar e iniciar NyxApp
    # Por agora, apenas confirma que o esqueleto funciona
    logger.info("Esqueleto funcional. Agente será implementado no Sprint 2.")
    return 0


if __name__ == "__main__":
    sys.exit(main())


# "O homem é condenado a ser livre." -- Jean-Paul Sartre
