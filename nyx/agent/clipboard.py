"""Clipboard -- capturar imagem ou texto via xclip.

Ctrl+Shift+V não chega na app (terminal captura). Usamos Ctrl+V +
xclip pra detectar imagem no clipboard. Se ausente, faz paste de texto
normal. Se xclip não instalado, degrada silencioso.
"""

from __future__ import annotations

import subprocess
import time
from pathlib import Path

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.clipboard")

PASTES_DIR = Path.home() / ".nyx" / "pastes"
XCLIP_TIMEOUT = 2

_xclip_missing = False


def _run_xclip(args: list[str], *, binary: bool) -> subprocess.CompletedProcess | None:
    global _xclip_missing
    if _xclip_missing:
        return None
    try:
        return subprocess.run(
            ["xclip", *args],
            capture_output=True,
            timeout=XCLIP_TIMEOUT,
            text=not binary,
        )
    except FileNotFoundError:
        _xclip_missing = True
        logger.warning("xclip não instalado -- paste de imagem desativado")
        return None
    except subprocess.TimeoutExpired:
        logger.debug("xclip timeout")
        return None


def capture_image() -> Path | None:
    """Retorna caminho salvo em ~/.nyx/pastes/ ou None se clipboard não tem imagem."""
    r = _run_xclip(
        ["-selection", "clipboard", "-t", "image/png", "-o"],
        binary=True,
    )
    if r is None or r.returncode != 0 or not r.stdout:
        return None

    try:
        PASTES_DIR.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y-%m-%d_%H%M%S")
        idx = 1
        while (PASTES_DIR / f"{ts}_{idx}.png").exists():
            idx += 1
        path = PASTES_DIR / f"{ts}_{idx}.png"
        path.write_bytes(r.stdout)
        logger.info("imagem colada: %s (%d bytes)", path, len(r.stdout))
        return path
    except OSError as e:
        logger.warning("Falha ao gravar imagem colada: %s", e)
        return None


def capture_text() -> str | None:
    """Retorna texto do clipboard ou None."""
    r = _run_xclip(["-selection", "clipboard", "-o"], binary=False)
    if r is None or r.returncode != 0:
        return None
    return r.stdout if r.stdout else None


def is_available() -> bool:
    return not _xclip_missing


# "A ferramenta se adapta à mão, não a mão à ferramenta." -- provérbio artesão
