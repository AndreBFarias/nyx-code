#!/usr/bin/env python3
"""Atalho para `setup_desktop_entry.py --uninstall` (DEPLOY-02)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

if __name__ == "__main__":
    script = Path(__file__).resolve().parent / "setup_desktop_entry.py"
    sys.exit(subprocess.call([sys.executable, str(script), "--uninstall"]))
