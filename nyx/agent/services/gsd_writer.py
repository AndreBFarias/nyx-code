"""GSD Writer -- progress.md write-through por sessão Nyx.

NYX-GSD-CHECKPOINTS-01: cada sessão mantem ~/.nyx/sessions/<id>/progress.md
em modo append-only com flush + fsync apos cada entry. Rotacao em 250 linhas
preservando header + ultimas 194.

Padrao Checkpoint.md do Nyx-Code aplicado ao runtime: write-through entre
tasks para sobreviver a OOM, kill ou exit acidental. /resume carrega ultimas
N linhas como contexto extra.
"""

from __future__ import annotations

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.gsd")

SESSIONS_DIR = Path.home() / ".nyx" / "sessions"
ROTATE_AT = 250
ROTATE_TAIL = 194
HEADER_LINES = 6
MAX_ARG_LEN = 30
MAX_RESULT_LEN = 80
MAX_MSG_LEN = 200
MAX_USER_SNIPPET = 120

_SECRET_KEY = re.compile(r"(pass|senha|secret|token|api[_-]?key|bearer|authorization)", re.IGNORECASE)


def _redact_value(v: Any) -> str:
    """Trunca valor preservando ate MAX_ARG_LEN; nunca leva multilinha."""
    s = str(v) if v is not None else ""
    s = s.replace("\n", " ").replace("\r", " ")
    return s[:MAX_ARG_LEN]


def _redact_args(args: dict[str, Any]) -> str:
    """Serializa args ocultando chaves sensiveis."""
    parts: list[str] = []
    for k, v in args.items():
        key = str(k)
        if _SECRET_KEY.search(key):
            parts.append(f"{key}=<redacted>")
        else:
            parts.append(f"{key}={_redact_value(v)}")
    return ", ".join(parts)


class GsdWriter:
    """Write-through de progress.md por sessão.

    Cada entry: timestamp + categoria + texto curto.
    Rotacao em 250 linhas mantendo header + ultimas 194.
    Best-effort: I/O falho NUNCA derruba o agente.
    """

    def __init__(self, session_id: str, project_name: str) -> None:
        self.session_id = session_id
        self.project_name = project_name
        self.path = SESSIONS_DIR / session_id / "progress.md"
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            if not self.path.is_file():
                self._init_file()
        except OSError as exc:
            logger.warning("gsd: falha ao preparar %s: %s", self.path, exc)

    def _init_file(self) -> None:
        header = (
            f"# Progress -- sessao {self.session_id}\n"
            f"\n"
            f"Projeto: {self.project_name}\n"
            f"Iniciada: {datetime.utcnow().isoformat()}Z\n"
            f"\n"
            f"## Append-only\n"
        )
        self.path.write_text(header, encoding="utf-8")

    def write(self, category: str, msg: str) -> None:
        """Append entry com timestamp; write-through (flush + fsync).

        Best-effort: falha de I/O não propaga; apenas log warning.
        """
        ts = datetime.utcnow().strftime("%H:%M:%S")
        safe_msg = msg.replace("\n", " ").replace("\r", " ")[:MAX_MSG_LEN]
        line = f"- [{ts}] **{category}** {safe_msg}\n"
        try:
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
                os.fsync(f.fileno())
            self._rotate()
        except OSError as exc:
            logger.warning("gsd: falha ao gravar entry em %s: %s", self.path, exc)

    def user_input(self, text: str) -> None:
        snippet = text.replace("\n", " ")[:MAX_USER_SNIPPET]
        self.write("user", f"`{snippet}`")

    def tool(self, name: str, args: dict[str, Any], result: str) -> None:
        argp = _redact_args(args or {})
        rsum = (result or "(sem output)").replace("\n", " ")[:MAX_RESULT_LEN]
        self.write("tool", f"{name}({argp}) -> {rsum}")

    def error(self, msg: str) -> None:
        self.write("err", msg[:MAX_MSG_LEN])

    def plan(self, msg: str) -> None:
        self.write("plan", msg[:MAX_MSG_LEN])

    def session(self, msg: str) -> None:
        self.write("session", msg[:MAX_MSG_LEN])

    def _rotate(self) -> None:
        """Trunca preservando header + ultimas ROTATE_TAIL linhas se exceder ROTATE_AT."""
        try:
            content = self.path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.warning("gsd: falha ao ler para rotacao %s: %s", self.path, exc)
            return
        lines = content.splitlines()
        if len(lines) <= ROTATE_AT:
            return
        header = lines[:HEADER_LINES]
        tail = lines[-ROTATE_TAIL:]
        try:
            self.path.write_text("\n".join(header + tail) + "\n", encoding="utf-8")
        except OSError as exc:
            logger.warning("gsd: falha na rotacao de %s: %s", self.path, exc)


def load_progress_tail(session_id: str, n: int = 50) -> str:
    """Carrega ultimas N linhas do progress.md da sessão. Vazio se ausente."""
    path = SESSIONS_DIR / session_id / "progress.md"
    if not path.is_file():
        return ""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        logger.warning("gsd: falha ao ler tail de %s: %s", path, exc)
        return ""
    return "\n".join(lines[-n:])


# "O cerebro esquece; o disco lembra." -- NYX-GSD-CHECKPOINTS-01
