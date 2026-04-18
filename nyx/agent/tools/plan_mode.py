"""PlanMode -- Modo planejamento (somente leitura).

Quando ativo, bloqueia tools de escrita (write, edit, run_command).
Permite: read, search, list, glob, analyze, done.
"""

from __future__ import annotations

import logging
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.plan_mode")

PLAN_MODE_BLOCKED = {"write_file", "edit_file", "run_command", "create_file", "patch"}
PLAN_MODE_ALLOWED = {
    "read_file",
    "search",
    "list_files",
    "glob",
    "analyze",
    "done",
    "web_search",
    "web_fetch",
    "task_create",
    "task_update",
    "task_list",
    "todo_write",
}

_plan_mode_active: bool = False


def is_plan_mode() -> bool:
    return _plan_mode_active


def set_plan_mode(active: bool) -> None:
    global _plan_mode_active
    _plan_mode_active = active
    logger.info("Plan mode: %s", "ATIVO" if active else "DESATIVADO")


def is_tool_allowed_in_plan_mode(tool_name: str) -> bool:
    if not _plan_mode_active:
        return True
    return tool_name not in PLAN_MODE_BLOCKED


class EnterPlanModeTool(RegisteredTool):
    action_type = ActionType.ANALYZE

    tool_def = ToolDef(
        name="enter_plan_mode",
        description=(
            "Entra no modo planejamento. Neste modo, apenas tools de leitura "
            "e busca são permitidas. Use para explorar o código antes de implementar. "
            "Chame exit_plan_mode quando estiver pronto para executar."
        ),
        parameters={},
        required=[],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        if is_plan_mode():
            return ActionResult(success=True, output="Já está em modo planejamento.")

        set_plan_mode(True)
        return ActionResult(
            success=True,
            output=(
                "Modo planejamento ativo. Regras:\n"
                "1. Explore o código com read_file, search, glob, list_files\n"
                "2. Identifique padrões e dependências\n"
                "3. Planeje a implementação\n"
                "4. Use exit_plan_mode quando estiver pronto para executar\n\n"
                "Tools bloqueadas: write_file, edit_file, run_command"
            ),
        )


class ExitPlanModeTool(RegisteredTool):
    action_type = ActionType.ANALYZE

    tool_def = ToolDef(
        name="exit_plan_mode",
        description=("Sai do modo planejamento e volta ao modo normal. Todas as tools ficam disponíveis novamente."),
        parameters={
            "plan_summary": {
                "type": "string",
                "description": "Resumo do plano elaborado durante o modo planejamento",
            },
        },
        required=[],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        if not is_plan_mode():
            return ActionResult(success=True, output="Não está em modo planejamento.")

        plan = str(params.get("plan_summary", "")).strip()
        set_plan_mode(False)

        output = "Modo planejamento desativado. Todas as tools disponíveis."
        if plan:
            output += f"\n\nPlano:\n{plan}"

        return ActionResult(success=True, output=output)


# "Planejar é pensar no futuro sem ansiedade." -- Sêneca
