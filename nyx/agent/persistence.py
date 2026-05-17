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
INDEX_PATH = SESSIONS_DIR / "index.json"
INDEX_SCHEMA_VERSION = 1
MAX_SESSION_AGE_DAYS = 7


def _session_id_from_path(path: Path) -> str:
    """Deriva id curto e estável a partir do filename (sem .json)."""
    return path.stem


def _first_user_prompt(session: CodeSession, max_chars: int = 80) -> str:
    """Primeira mensagem do usuário, truncada."""
    for entry in session.history:
        if entry.role == "user" and entry.content:
            text = entry.content.strip().replace("\n", " ")
            return text if len(text) <= max_chars else text[: max_chars - 1] + "…"
    return ""


def _atomic_write(path: Path, data: str) -> None:
    """Escreve via .tmp + replace para não corromper em crash."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(data, encoding="utf-8")
    tmp.replace(path)


def load_index() -> list[dict]:
    """Carrega índice de sessões; retorna [] se ausente/corrompido."""
    if not INDEX_PATH.exists():
        return []
    try:
        raw = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "entries" in raw:
            return list(raw["entries"])
        return []
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("índice de sessões corrompido (%s) — retornando vazio", exc)
        return []


def _save_index(entries: list[dict]) -> None:
    payload = {"version": INDEX_SCHEMA_VERSION, "entries": entries}
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        _atomic_write(INDEX_PATH, json.dumps(payload, ensure_ascii=False, indent=2))
    except OSError as exc:
        logger.warning("falha ao gravar índice de sessões: %s", exc)


def _update_index(path: Path, session: CodeSession, project_name: str = "") -> None:
    """Insere/atualiza entrada do índice; mantém últimas 200 entradas."""
    entry = {
        "id": _session_id_from_path(path),
        "ts_inicio": getattr(session, "ts_inicio", int(time.time())),
        "ts_fim": int(time.time()),
        "primeiro_prompt": _first_user_prompt(session),
        "n_turnos": sum(1 for e in session.history if e.role == "user"),
        "projeto": project_name,
    }
    entries = [e for e in load_index() if e.get("id") != entry["id"]]
    entries.append(entry)
    entries.sort(key=lambda e: e.get("ts_fim", 0))
    if len(entries) > 200:
        entries = entries[-200:]
    _save_index(entries)


def load_session_by_id(session_id: str) -> CodeSession | None:
    """Restaura sessão por id exato ou prefixo único (SESSION-RESUME-01).

    Se prefixo casa múltiplas sessões, retorna None — UI deve pedir desambiguação.
    """
    if not SESSIONS_DIR.exists():
        return None
    matches = [p for p in SESSIONS_DIR.glob("session_*.json") if _session_id_from_path(p).startswith(session_id) or _session_id_from_path(p) == session_id]
    if len(matches) != 1:
        return None
    return _load_session_file(matches[0])


def _load_session_file(path: Path) -> CodeSession | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("falha ao ler sessão %s: %s", path.name, exc)
        return None
    session = CodeSession()
    session.iteration = data.get("iteration", 0)
    session._files_read = set(data.get("files_read", []))
    session._files_modified = set(data.get("files_modified", []))
    session.summary = data.get("summary", "")
    session.last_summarized_at = data.get("last_summarized_at", 0)
    session.ts_inicio = data.get("ts_inicio", data.get("timestamp", int(time.time())))
    for entry_data in data.get("history", []):
        session.history.append(
            HistoryEntry(
                role=entry_data.get("role", "user"),
                content=entry_data.get("content", ""),
                tool_name=entry_data.get("tool_name", ""),
                tool_args=entry_data.get("tool_args", {}),
            )
        )
    logger.info("Sessão restaurada: %s (%d entradas)", path.name, len(session.history))
    return session


def save_session(session: CodeSession, project_name: str = "") -> Path | None:
    """Salva sessão atual em JSON e atualiza o índice (SESSION-RESUME-01)."""
    try:
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
        ts = int(time.time())
        name = f"session_{project_name}_{ts}.json" if project_name else f"session_{ts}.json"
        path = SESSIONS_DIR / name

        if not hasattr(session, "ts_inicio") or not session.ts_inicio:
            session.ts_inicio = ts

        data = {
            "project": project_name,
            "timestamp": ts,
            "ts_inicio": session.ts_inicio,
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
        _atomic_write(path, json.dumps(data, indent=2, ensure_ascii=False))
        _update_index(path, session, project_name)
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
