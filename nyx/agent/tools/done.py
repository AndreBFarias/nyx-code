"""Tool: Done -- Sinaliza fim da tarefa."""

from __future__ import annotations

from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef


class DoneTool(RegisteredTool):
    action_type = ActionType.DONE
    tool_def = ToolDef(
        name="done",
        description="Sinaliza que a tarefa foi concluída. Use SUMMARY para resumir o que foi feito.",
        parameters={
            "summary": {"type": "string", "description": "Resumo do que foi realizado"},
        },
        required=["summary"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        summary = params.get("summary", "Tarefa concluída.")
        return ActionResult(success=True, output=summary)


# "Saber parar é tão importante quanto saber começar." -- Sêneca
