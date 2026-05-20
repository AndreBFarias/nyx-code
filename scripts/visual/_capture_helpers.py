"""Helpers de captura visual para scripts/visual/.

Duas estratégias canônicas:
- capture_terminal: xdotool localiza janela kitty, import salva PNG da janela.
- capture_web: google-chrome --headless --screenshot salva PNG da URL.

Ambas honram delay_sec antes de capturar para permitir frame intermediário
em animações (midframe). Sem dependência nova; usa subprocess + binários
já presentes no sistema (xdotool, import, google-chrome).

Uso típico:
    from scripts.visual._capture_helpers import capture_terminal, should_capture_midframe
    if should_capture_midframe(50):
        capture_terminal("kitty", "/tmp/teste_midframe.png", delay_sec=0.5)
    capture_terminal("kitty", "/tmp/teste_final.png", delay_sec=1.0)
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

MIDFRAME_PCT_DEFAULT = 50


def should_capture_midframe(pct: int) -> bool:
    """Midframe ativo apenas em 1..99 (exclui extremos)."""
    return 0 < pct < 100


def capture_terminal(window_name: str, out_path: str, delay_sec: float) -> int:
    """Captura janela de terminal via xdotool+import.

    Retorna exit code (0 = ok). Em caso de DISPLAY vazio ou binário ausente,
    imprime erro literal e retorna != 0 (sem raise, para não derrubar o pipeline).
    """
    time.sleep(max(0.0, delay_sec))
    try:
        result = subprocess.run(
            ["xdotool", "search", "--name", window_name],
            capture_output=True, text=True, check=True,
        )
        wids = result.stdout.strip().splitlines()
        if not wids:
            print(
                f"ERRO captura terminal: janela '{window_name}' não encontrada",
                file=sys.stderr,
            )
            return 1
        target = wids[0]
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["import", "-window", target, out_path],
            check=True,
        )
        return 0
    except FileNotFoundError as e:
        print(f"ERRO captura terminal: binario ausente ({e})", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print(f"ERRO captura terminal: comando falhou ({e})", file=sys.stderr)
        return 3


def capture_web(url: str, out_path: str, delay_sec: float) -> int:
    """Captura URL via google-chrome --headless --screenshot.

    delay_sec é traduzido em --virtual-time-budget (ms) para frame
    determinístico em animação. Retorna exit code (0 = ok).
    """
    try:
        Path(out_path).parent.mkdir(parents=True, exist_ok=True)
        ms = int(max(0.0, delay_sec) * 1000)
        subprocess.run(
            [
                "google-chrome",
                "--headless",
                "--disable-gpu",
                "--no-sandbox",
                f"--screenshot={out_path}",
                f"--virtual-time-budget={ms}",
                "--window-size=1280,800",
                url,
            ],
            check=True,
            capture_output=True,
        )
        return 0
    except FileNotFoundError as e:
        print(f"ERRO captura web: binario ausente ({e})", file=sys.stderr)
        return 2
    except subprocess.CalledProcessError as e:
        print(f"ERRO captura web: chrome falhou ({e})", file=sys.stderr)
        return 3
