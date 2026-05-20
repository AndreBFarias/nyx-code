#!/usr/bin/env python3
"""Detector de VRAM livre + enumeração de processos GPU.

Uso programático:
    from scripts.gauntlet.vram_check import probe, VRAM_MIN_FREE_MIB, is_nyx_owned
    snap = probe()
    # snap == {
    #     "free_mib": 423,
    #     "processes": [{"pid": 956798, "name": "...", "mib": 3678}],
    #     "nvidia_smi_ok": True,
    # }

Uso CLI:
    python3 scripts/gauntlet/vram_check.py
    NYX_FAKE_VRAM_FREE=500 python3 scripts/gauntlet/vram_check.py

Limite VRAM_MIN_FREE_MIB = 1500 (RTX 3050 4 GB; abaixo disso, modelo Nyx
não cabe na pre-carga + overhead Ollama).

K08-VRAM-RUNNER-ISOLATION-01: este modulo e importado por scripts.gauntlet.
nyx_gauntlet no pre-flight da fase performance (K-08) para distinguir
contaminacao externa de regressao real do Nyx.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

VRAM_MIN_FREE_MIB: int = 1500

# Hints para filtrar processos do proprio Nyx -- nunca propor matar.
NYX_PROCESS_HINTS: tuple[str, ...] = (
    "nyx/proxy.py",
    "nyx/cli.py",
    "ollama serve",
    "ollama runner",
    "ollama_runner",
)


def _query_free_mib() -> int:
    """VRAM livre em MiB. -1 se nvidia-smi indisponivel."""
    fake = os.environ.get("NYX_FAKE_VRAM_FREE")
    if fake is not None:
        try:
            return int(fake)
        except ValueError:
            return -1
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-gpu=memory.free",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=3,
        ).strip()
        return int(out.splitlines()[0])
    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        ValueError,
        OSError,
    ):
        return -1


def _query_processes() -> list[dict[str, Any]]:
    """Lista (pid, name, mib) ocupando VRAM. Vazia se nvidia-smi indisponivel."""
    fake = os.environ.get("NYX_FAKE_VRAM_FREE")
    if fake is not None:
        # Modo CI: simula 1 processo externo de 3000 MiB se fake < threshold.
        try:
            free = int(fake)
        except ValueError:
            return []
        if free < VRAM_MIN_FREE_MIB:
            return [{"pid": 999999, "name": "fake-ext-process", "mib": 3000}]
        return []
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,process_name,used_memory",
                "--format=csv,noheader,nounits",
            ],
            text=True,
            timeout=3,
        ).strip()
    except (
        FileNotFoundError,
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        OSError,
    ):
        return []
    procs: list[dict[str, Any]] = []
    for line in out.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[0])
            mib = int(parts[2])
        except ValueError:
            continue
        procs.append({"pid": pid, "name": parts[1], "mib": mib})
    return procs


def is_nyx_owned(proc: dict[str, Any]) -> bool:
    """True se o processo pertence ao proprio Nyx (não candidato a kill)."""
    name = proc.get("name", "") or ""
    return any(hint in name for hint in NYX_PROCESS_HINTS)


def probe() -> dict[str, Any]:
    """Snapshot completo: VRAM livre + processos."""
    free = _query_free_mib()
    procs = _query_processes()
    return {
        "free_mib": free,
        "processes": procs,
        "nvidia_smi_ok": free >= 0,
    }


def main() -> int:
    snap = probe()
    print(json.dumps(snap, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
