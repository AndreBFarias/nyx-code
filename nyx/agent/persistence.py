"""Session Persistence -- Salvar/restaurar sessões do Nyx Agent.

Port de Luna src/skills/code_agent/persistence.py.
Sessões salvas em ~/.nyx/sessions/ como JSON.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from nyx.agent.services.logging_service import get_logger

from .session import CodeSession, HistoryEntry

logger = get_logger("nyx.persistence")

SESSIONS_DIR = Path.home() / ".nyx" / "sessions"
MAX_SESSION_AGE_DAYS = 7


def save_session(session: CodeSession, project_name: str = "") -> Path | None:
    """Salva sessão atual em JSON."""
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        name = f"session_{project_name}_{ts}.json" if project_name else f"session_{ts}.json"
        path = SESSIONS_DIR / name

        data = {
            "project": project_name,
            "timestamp": ts,
            "iteration": session.iteration,
            "summary": getattr(session, "summary", ""),
            "last_summarized_at": getattr(session, "last_summarized_at", 0),
            "files_read": sorted(session._files_read),
            "files_modified": sorted(session._files_modified),
            "history": [
                {
                    "role": e.role,
                    "content": e.content[:2000],
                    "tool_name": e.tool_name,
                    "tool_args": e.tool_args,
                }
                for e in session.history[-20:]
            ],
        }
        tmp_path = path.with_suffix(".tmp")
        tmp_path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp_path.rename(path)
        logger.info("Sessão salva: %s", path)
        return path
    except Exception as e:
        logger.warning("Falha ao salvar sessão: %s", e)
        return None


def load_latest_session(project_name: str = "") -> CodeSession | None:
    """Carrega sessão mais recente do projeto."""
    if not SESSIONS_DIR.exists():
        return None

    pattern = f"session_{project_name}_*.json" if project_name else "session_*.json"
    files = sorted(SESSIONS_DIR.glob(pattern), reverse=True)
    if not files:
        return None

    try:
        data = json.loads(files[0].read_text(encoding="utf-8"))
        session = CodeSession()
        session.iteration = data.get("iteration", 0)
        session._files_read = set(data.get("files_read", []))
        session._files_modified = set(data.get("files_modified", []))
        session.summary = data.get("summary", "")
        session.last_summarized_at = data.get("last_summarized_at", 0)

        for entry_data in data.get("history", []):
            session.history.append(
                HistoryEntry(
                    role=entry_data.get("role", "user"),
                    content=entry_data.get("content", ""),
                    tool_name=entry_data.get("tool_name", ""),
                    tool_args=entry_data.get("tool_args", {}),
                )
            )

        logger.info("Sessão restaurada: %s (%d entradas)", files[0].name, len(session.history))
        return session
    except Exception as e:
        logger.warning("Falha ao carregar sessão: %s", e)
        return None


def cleanup_old_sessions() -> int:
    """Remove sessões mais antigas que MAX_SESSION_AGE_DAYS."""
    if not SESSIONS_DIR.exists():
        return 0

    cutoff = time.time() - (MAX_SESSION_AGE_DAYS * 86400)
    removed = 0
    for f in SESSIONS_DIR.glob("session_*.json"):
        if f.stat().st_mtime < cutoff:
            f.unlink()
            removed += 1

    if removed:
        logger.info("Removidas %d sessões antigas", removed)
    return removed


# "O que não é registrado, não existiu." -- provérbio romano
