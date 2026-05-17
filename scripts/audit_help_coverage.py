#!/usr/bin/env python3
"""HELP-EXAMPLES-01: verifica cobertura de examples em @nyx_command."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

# Força import dos módulos de commands para popular o registry
import nyx.agent.commands  # noqa: F401
from nyx.agent.commands._registry import _COMMANDS  # type: ignore[attr-defined]


def main() -> int:
    seen: dict[str, object] = {}
    for name, cmd in _COMMANDS.items():
        # Aliases apontam para o mesmo CommandDef; deduplicar por id().
        if id(cmd) not in seen:
            seen[id(cmd)] = (name, cmd)

    total = len(seen)
    faltantes_low: list[tuple[str, int]] = []
    faltantes_high: list[tuple[str, int]] = []
    for _, (name, cmd) in seen.items():
        n = len(cmd.examples)
        if n < 2:
            faltantes_low.append((cmd.name, n))
        elif n > 3:
            faltantes_high.append((cmd.name, n))

    ok = total - len(faltantes_low) - len(faltantes_high)
    print(f"{ok}/{total} OK")
    if faltantes_low:
        print("\n  Faltam exemplos (mínimo 2):")
        for name, n in sorted(faltantes_low):
            print(f"    /{name}: {n} exemplo(s)")
    if faltantes_high:
        print("\n  Excesso de exemplos (máximo 3):")
        for name, n in sorted(faltantes_high):
            print(f"    /{name}: {n} exemplos")
    if faltantes_low or faltantes_high:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
