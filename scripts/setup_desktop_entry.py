#!/usr/bin/env python3
"""Setup Desktop Entry para Nyx-Code (DEPLOY-02).

Cria:
- ~/.local/share/icons/hicolor/256x256/apps/nyx.png  (cópia de assets/nyx-icon.png)
- ~/.local/share/applications/nyx.desktop

Chama update-desktop-database se disponível.

Flags:
  --dry-run    mostra o que faria sem escrever
  --uninstall  remove entry + ícone
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess as _sp
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ICON_SRC = PROJECT_ROOT / "assets" / "nyx-icon.png"
RUN_SH = PROJECT_ROOT / "run.sh"

ICON_DST_DIR = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"
ICON_DST = ICON_DST_DIR / "nyx.png"

APPS_DIR = Path.home() / ".local" / "share" / "applications"
DESKTOP_FILE = APPS_DIR / "nyx.desktop"


def detect_terminal_exec() -> str:
    """Retorna a linha Exec= preferindo kitty (fallback gnome-terminal, konsole, xterm)."""
    run_sh = str(RUN_SH)
    if shutil.which("kitty"):
        return f"kitty --class Nyx --title Nyx-Code -e {run_sh}"
    term = os.environ.get("TERMINAL", "")
    if term and shutil.which(term):
        return f"{term} -e {run_sh}"
    if shutil.which("gnome-terminal"):
        return f"gnome-terminal -- {run_sh}"
    if shutil.which("konsole"):
        return f"konsole -e {run_sh}"
    if shutil.which("xterm"):
        return f"xterm -e {run_sh}"
    return run_sh


def desktop_contents(exec_line: str) -> str:
    return f"""[Desktop Entry]
Version=1.0
Type=Application
Name=Nyx
GenericName=Code Agent Local
Comment=Agente de código offline, 100% local
Exec={exec_line}
Icon=nyx
Terminal=false
Categories=Development;
StartupWMClass=Nyx
"""


def _refresh_database() -> bool:
    """Chama update-desktop-database se disponível."""
    if shutil.which("update-desktop-database") is None:
        return False
    _sp.call(
        ["update-desktop-database", str(APPS_DIR)],
        stdout=_sp.DEVNULL,
        stderr=_sp.DEVNULL,
    )
    return True


def install(dry_run: bool) -> int:
    if not ICON_SRC.is_file():
        print(f"[erro] ícone não encontrado: {ICON_SRC}", file=sys.stderr)
        return 1
    if not RUN_SH.is_file():
        print(f"[erro] run.sh não encontrado: {RUN_SH}", file=sys.stderr)
        return 1

    print(f"[install] ícone: {ICON_SRC} -> {ICON_DST}")
    if not dry_run:
        ICON_DST_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ICON_SRC, ICON_DST)

    exec_line = detect_terminal_exec()
    content = desktop_contents(exec_line)
    print(f"[install] .desktop: {DESKTOP_FILE}")
    print(f"[install] Exec: {exec_line}")
    if not dry_run:
        APPS_DIR.mkdir(parents=True, exist_ok=True)
        DESKTOP_FILE.write_text(content, encoding="utf-8")
        DESKTOP_FILE.chmod(0o755)

    if not dry_run and _refresh_database():
        print("[install] update-desktop-database chamado")
    elif shutil.which("update-desktop-database") is None:
        print("[skip] update-desktop-database ausente -- pode requerer logout/login")

    print("[ok] Nyx instalado no launcher" if not dry_run else "[dry-run] nada escrito")
    return 0


def uninstall() -> int:
    removed = False
    if DESKTOP_FILE.exists():
        DESKTOP_FILE.unlink()
        removed = True
        print(f"[remove] {DESKTOP_FILE}")
    if ICON_DST.exists():
        ICON_DST.unlink()
        removed = True
        print(f"[remove] {ICON_DST}")
    if not removed:
        print("[skip] nada para remover")
    _refresh_database()
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Setup Desktop Entry para Nyx (DEPLOY-02)")
    p.add_argument("--dry-run", action="store_true", help="Mostra o que faria sem escrever")
    p.add_argument("--uninstall", action="store_true", help="Remove entry + ícone")
    args = p.parse_args()
    return uninstall() if args.uninstall else install(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
