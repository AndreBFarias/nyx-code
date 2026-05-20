#!/usr/bin/env python3
"""SESSION-RESUME-01: gera/atualiza ~/.nyx/sessions/index.json a partir
das sessões existentes. Idempotente — rodar 2x produz zero diff."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from nyx.agent.persistence import (  # noqa: E402
    INDEX_PATH,
    SESSIONS_DIR,
    _save_index,
    _session_id_from_path,
)


def _read_session_meta(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"  [warn] {path.name}: {exc}")
        return None

    history = data.get("history", []) or []
    first_user = ""
    for entry in history:
        if entry.get("role") == "user" and entry.get("content"):
            text = entry["content"].strip().replace("\n", " ")
            first_user = text if len(text) <= 80 else text[:79] + "…"
            break
    n_turnos = sum(1 for e in history if e.get("role") == "user")

    return {
        "id": _session_id_from_path(path),
        "ts_inicio": int(data.get("ts_inicio") or data.get("timestamp") or path.stat().st_mtime),
        "ts_fim": int(data.get("timestamp") or path.stat().st_mtime),
        "primeiro_prompt": first_user,
        "n_turnos": n_turnos,
        "projeto": data.get("project") or "",
    }


def main() -> int:
    if not SESSIONS_DIR.exists():
        print(f"[migrate] {SESSIONS_DIR} ausente — nada a migrar.")
        return 0

    files = sorted(SESSIONS_DIR.glob("session_*.json"))
    if not files:
        print("[migrate] nenhuma sessão encontrada.")
        return 0

    entries: list[dict] = []
    for path in files:
        meta = _read_session_meta(path)
        if meta:
            entries.append(meta)

    entries.sort(key=lambda e: e["ts_fim"])
    if len(entries) > 200:
        entries = entries[-200:]

    before = ""
    if INDEX_PATH.exists():
        before = INDEX_PATH.read_text(encoding="utf-8")

    _save_index(entries)
    after = INDEX_PATH.read_text(encoding="utf-8")
    changed = (before != after)

    print(
        f"[migrate] {len(entries)} sessões indexadas em {INDEX_PATH}. "
        f"diff={'sim' if changed else 'idempotente (zero diff)'}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
