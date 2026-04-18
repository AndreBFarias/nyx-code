"""TodoWrite -- Gerencia lista de tarefas da sessão.

Gerencia lista de tarefas com persistência em ~/.nyx/todos.json.
Lista in-memory com persistência em ~/.nyx/todos.json.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.todo")

TODOS_FILE = Path.home() / ".nyx" / "todos.json"


class TodoWriteTool(RegisteredTool):
    action_type = ActionType.DONE

    tool_def = ToolDef(
        name="todo_write",
        description=(
            "Gerencia a lista de tarefas da sessão. "
            "Cada item tem: content (descrição), status (pending/in_progress/completed). "
            "Envie a lista completa atualizada a cada chamada."
        ),
        parameters={
            "todos": {
                "type": "array",
                "description": "Lista completa de tarefas atualizada",
                "items": {
                    "type": "object",
                    "properties": {
                        "content": {"type": "string", "description": "Descrição da tarefa"},
                        "status": {
                            "type": "string",
                            "enum": ["pending", "in_progress", "completed"],
                            "description": "Status atual",
                        },
                    },
                    "required": ["content", "status"],
                },
            },
        },
        required=["todos"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        todos = params.get("todos", [])
        if not isinstance(todos, list):
            return ActionResult(success=False, error="'todos' deve ser uma lista")

        old_todos = _load_todos()

        validated: list[dict[str, str]] = []
        for item in todos:
            if not isinstance(item, dict):
                continue
            content = str(item.get("content", "")).strip()
            status = str(item.get("status", "pending")).strip()
            if not content:
                continue
            if status not in ("pending", "in_progress", "completed"):
                status = "pending"
            validated.append({"content": content, "status": status})

        all_done = all(t["status"] == "completed" for t in validated) if validated else False
        final = [] if all_done else validated

        _save_todos(final)

        pending = sum(1 for t in validated if t["status"] == "pending")
        in_progress = sum(1 for t in validated if t["status"] == "in_progress")
        completed = sum(1 for t in validated if t["status"] == "completed")

        summary = (
            f"Tarefas atualizadas: {len(validated)} total "
            f"({pending} pendentes, {in_progress} em progresso, {completed} concluídas)"
        )
        if all_done:
            summary += ". Todas concluídas -- lista limpa."

        logger.info(summary)
        return ActionResult(success=True, output=summary)


def _load_todos() -> list[dict[str, str]]:
    if not TODOS_FILE.exists():
        return []
    try:
        data = json.loads(TODOS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception as e:
        logger.debug("Falha ao carregar todos: %s", e)
        return []


def _save_todos(todos: list[dict[str, str]]) -> None:
    try:
        TODOS_FILE.parent.mkdir(parents=True, exist_ok=True)
        TODOS_FILE.write_text(
            json.dumps(todos, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning("Falha ao salvar todos: %s", e)


# "A lista é a forma mais honesta de planejamento." -- Umberto Eco
