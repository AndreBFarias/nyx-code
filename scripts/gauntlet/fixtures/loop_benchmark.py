#!/usr/bin/env python3
"""Benchmark do loop de feedback (UX-LOOP-01, ADR-025).

Mede 3 tempos críticos:
- ack_ms (input echo): meta < 100 ms.
- tool_start_ms (glyph visível em tool call): meta < 300 ms.
- streaming_first_token_ms (primeiro token): meta < 500 ms.

Não substitui validação visual humana; é proxy automatizável.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

ACK_LIMIT_MS = 100
TOOL_START_LIMIT_MS = 300
STREAMING_LIMIT_MS = 500


def bench_ack() -> float:
    """Simula echo de input via render_user_input. Mede tempo até stdout flush."""
    from nyx.agent.output import render_user_input

    t0 = time.monotonic()
    render_user_input("Olá, isto é um benchmark")
    return (time.monotonic() - t0) * 1000


def bench_tool_start() -> float:
    """Simula render_tool_card_start (glifo + label visível)."""
    from nyx.agent.output import render_tool_card_start

    t0 = time.monotonic()
    render_tool_card_start("read_file", {"file_path": "README.md"})
    return (time.monotonic() - t0) * 1000


def bench_streaming() -> float:
    """Mede tempo para iniciar spinner Braille."""
    from nyx.agent.output import nyx_spinner

    t0 = time.monotonic()
    sp = nyx_spinner("pensando...")
    sp.__enter__()
    elapsed = (time.monotonic() - t0) * 1000
    sp.stop()
    return elapsed


def main() -> int:
    ack = bench_ack()
    tool_start = bench_tool_start()
    streaming = bench_streaming()

    print(f"ack_ms             = {ack:.2f}  (limite {ACK_LIMIT_MS})")
    print(f"tool_start_ms      = {tool_start:.2f}  (limite {TOOL_START_LIMIT_MS})")
    print(f"streaming_first_ms = {streaming:.2f}  (limite {STREAMING_LIMIT_MS})")

    fails: list[str] = []
    if ack > ACK_LIMIT_MS:
        fails.append(f"ack {ack:.0f}ms > {ACK_LIMIT_MS}ms")
    if tool_start > TOOL_START_LIMIT_MS:
        fails.append(f"tool_start {tool_start:.0f}ms > {TOOL_START_LIMIT_MS}ms")
    if streaming > STREAMING_LIMIT_MS:
        fails.append(f"streaming {streaming:.0f}ms > {STREAMING_LIMIT_MS}ms")

    if fails:
        print("FAIL: " + "; ".join(fails))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
