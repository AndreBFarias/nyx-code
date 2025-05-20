"""Analytics -- Métricas locais de uso do Nyx."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger("nyx.services.analytics")

DATA_DIR = Path.home() / ".nyx" / "analytics"
METRICS_FILE = DATA_DIR / "metrics.json"


class Analytics:
    """Métricas locais: sessões, tools usadas, tempo."""

    def __init__(self) -> None:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        self._data = self._load()
        self._session_start = time.time()

    def _load(self) -> dict:
        if METRICS_FILE.exists():
            try:
                return json.loads(METRICS_FILE.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                logger.warning("Falha ao carregar métricas, reiniciando")
        return {"sessions": 0, "total_time_s": 0, "tool_calls": {}, "commands_used": {}}

    def _save(self) -> None:
        try:
            METRICS_FILE.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            logger.error("Falha ao salvar métricas: %s", e)

    def track_tool(self, tool_name: str) -> None:
        counts = self._data.setdefault("tool_calls", {})
        counts[tool_name] = counts.get(tool_name, 0) + 1

    def track_command(self, cmd_name: str) -> None:
        counts = self._data.setdefault("commands_used", {})
        counts[cmd_name] = counts.get(cmd_name, 0) + 1

    def end_session(self) -> None:
        elapsed = time.time() - self._session_start
        self._data["sessions"] = self._data.get("sessions", 0) + 1
        self._data["total_time_s"] = self._data.get("total_time_s", 0) + elapsed
        self._save()
        logger.info("Sessão encerrada: %.1fs, total: %d sessões", elapsed, self._data["sessions"])

    def status(self) -> dict:
        top_tools = sorted(
            self._data.get("tool_calls", {}).items(),
            key=lambda x: x[1], reverse=True,
        )[:5]
        return {
            "service": "analytics",
            "ativo": True,
            "sessions": self._data.get("sessions", 0),
            "total_time_s": round(self._data.get("total_time_s", 0), 1),
            "top_tools": top_tools,
        }


# "Medir é o primeiro passo para controlar." -- H. James Harrington
