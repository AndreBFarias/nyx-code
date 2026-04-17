"""TaskManager -- Criação e gestão de tarefas com status.

Sistema de tarefas com status e persistência.
Tarefas persistidas em ~/.nyx/tasks.json.
Suporta: create, update, get, list.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.tasks")

TASKS_FILE = Path.home() / ".nyx" / "tasks.json"


@dataclass
class Task:
    id: str
    subject: str
    description: str = ""
    status: str = "pending"
    created_at: float = 0.0
    updated_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


def _load_tasks() -> list[Task]:
    if not TASKS_FILE.exists():
        return []
    try:
        data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))
        return [Task(**t) for t in data if isinstance(t, dict)]
    except Exception as e:
        logger.debug("Falha ao carregar tasks: %s", e)
        return []


def _save_tasks(tasks: list[Task]) -> None:
    try:
        TASKS_FILE.parent.mkdir(parents=True, exist_ok=True)
        TASKS_FILE.write_text(
            json.dumps([asdict(t) for t in tasks], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    except Exception as e:
        logger.warning("Falha ao salvar tasks: %s", e)


class TaskCreateTool(RegisteredTool):
    action_type = ActionType.TODO_WRITE

    tool_def = ToolDef(
        name="task_create",
        description=(
            "Cria uma nova tarefa no sistema de tarefas. "
            "Retorna o ID da tarefa criada."
        ),
        parameters={
            "subject": {"type": "string", "description": "Título breve da tarefa"},
            "description": {"type": "string", "description": "Descrição detalhada"},
        },
        required=["subject"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        subject = str(params.get("subject", "")).strip()
        if not subject:
            return ActionResult(success=False, error="Subject vazio")

        description = str(params.get("description", "")).strip()
        now = time.time()

        task = Task(
            id=uuid.uuid4().hex[:8],
            subject=subject,
            description=description,
            status="pending",
            created_at=now,
            updated_at=now,
        )

        tasks = _load_tasks()
        tasks.append(task)
        _save_tasks(tasks)

        logger.info("Task criada: #%s %s", task.id, subject)
        return ActionResult(success=True, output=f"Task #{task.id} criada: {subject}")


class TaskUpdateTool(RegisteredTool):
    action_type = ActionType.TODO_WRITE

    tool_def = ToolDef(
        name="task_update",
        description=(
            "Atualiza status de uma tarefa existente. "
            "Status: pending, in_progress, completed."
        ),
        parameters={
            "task_id": {"type": "string", "description": "ID da tarefa"},
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed"],
                "description": "Novo status",
            },
        },
        required=["task_id", "status"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        task_id = str(params.get("task_id", "")).strip()
        new_status = str(params.get("status", "")).strip()

        if not task_id:
            return ActionResult(success=False, error="task_id vazio")
        if new_status not in ("pending", "in_progress", "completed"):
            return ActionResult(success=False, error=f"Status inválido: {new_status}")

        tasks = _load_tasks()
        found = None
        for t in tasks:
            if t.id == task_id:
                found = t
                break

        if not found:
            return ActionResult(success=False, error=f"Task #{task_id} não encontrada")

        old_status = found.status
        found.status = new_status
        found.updated_at = time.time()
        _save_tasks(tasks)

        logger.info("Task #%s: %s -> %s", task_id, old_status, new_status)
        return ActionResult(
            success=True,
            output=f"Task #{task_id} atualizada: {old_status} -> {new_status}",
        )


class TaskListTool(RegisteredTool):
    action_type = ActionType.LIST_FILES

    tool_def = ToolDef(
        name="task_list",
        description="Lista todas as tarefas com seus status.",
        parameters={},
        required=[],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        tasks = _load_tasks()
        if not tasks:
            return ActionResult(success=True, output="Nenhuma tarefa registrada.")

        lines = []
        for t in tasks:
            marker = {"pending": "[ ]", "in_progress": "[~]", "completed": "[x]"}.get(t.status, "[ ]")
            lines.append(f"{marker} #{t.id} {t.subject}")

        pending = sum(1 for t in tasks if t.status == "pending")
        in_progress = sum(1 for t in tasks if t.status == "in_progress")
        completed = sum(1 for t in tasks if t.status == "completed")
        lines.append(f"\nTotal: {len(tasks)} ({pending} pendentes, {in_progress} em progresso, {completed} concluídas)")

        return ActionResult(success=True, output="\n".join(lines))


class TaskGetTool(RegisteredTool):
    action_type = ActionType.READ_FILE

    tool_def = ToolDef(
        name="task_get",
        description="Retorna detalhes de uma tarefa específica por ID.",
        parameters={
            "task_id": {"type": "string", "description": "ID da tarefa"},
        },
        required=["task_id"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        task_id = str(params.get("task_id", "")).strip()
        if not task_id:
            return ActionResult(success=False, error="task_id vazio")

        tasks = _load_tasks()
        found = next((t for t in tasks if t.id == task_id), None)
        if not found:
            return ActionResult(success=False, error=f"Task #{task_id} não encontrada")

        from datetime import datetime
        created = datetime.fromtimestamp(found.created_at).strftime("%Y-%m-%d %H:%M") if found.created_at else "N/A"
        updated = datetime.fromtimestamp(found.updated_at).strftime("%Y-%m-%d %H:%M") if found.updated_at else "N/A"

        lines = [
            f"Task #{found.id}",
            f"  Subject: {found.subject}",
            f"  Status: {found.status}",
            f"  Descrição: {found.description or '(vazio)'}",
            f"  Criada: {created}",
            f"  Atualizada: {updated}",
        ]
        if found.metadata:
            lines.append(f"  Output: {found.metadata.get('output', '(nenhum)')}")

        return ActionResult(success=True, output="\n".join(lines))


class TaskOutputTool(RegisteredTool):
    action_type = ActionType.READ_FILE

    tool_def = ToolDef(
        name="task_output",
        description="Retorna o output/log de uma tarefa específica.",
        parameters={
            "task_id": {"type": "string", "description": "ID da tarefa"},
        },
        required=["task_id"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        task_id = str(params.get("task_id", "")).strip()
        if not task_id:
            return ActionResult(success=False, error="task_id vazio")

        tasks = _load_tasks()
        found = next((t for t in tasks if t.id == task_id), None)
        if not found:
            return ActionResult(success=False, error=f"Task #{task_id} não encontrada")

        output = found.metadata.get("output", "")
        if not output:
            return ActionResult(success=True, output=f"Task #{task_id}: sem output registrado.")

        return ActionResult(success=True, output=f"Output de #{task_id}:\n{output}")


class TaskStopTool(RegisteredTool):
    action_type = ActionType.TODO_WRITE

    tool_def = ToolDef(
        name="task_stop",
        description="Cancela uma tarefa em execução. Muda status para 'cancelled'.",
        parameters={
            "task_id": {"type": "string", "description": "ID da tarefa"},
        },
        required=["task_id"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        task_id = str(params.get("task_id", "")).strip()
        if not task_id:
            return ActionResult(success=False, error="task_id vazio")

        tasks = _load_tasks()
        found = next((t for t in tasks if t.id == task_id), None)
        if not found:
            return ActionResult(success=False, error=f"Task #{task_id} não encontrada")

        old_status = found.status
        found.status = "cancelled"
        found.updated_at = time.time()
        found.metadata["cancelled_at"] = time.time()
        _save_tasks(tasks)

        logger.info("Task #%s cancelada: %s -> cancelled", task_id, old_status)
        return ActionResult(
            success=True,
            output=f"Task #{task_id} cancelada: {old_status} -> cancelled",
        )


# "Planejar é trazer o futuro para o presente." -- Alan Lakein
