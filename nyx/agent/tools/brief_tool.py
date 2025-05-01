"""Tool: Brief -- Gera resumo do contexto atual do agent."""

from __future__ import annotations

import logging
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.brief")


class BriefTool(RegisteredTool):
    action_type = ActionType.READ_FILE

    tool_def = ToolDef(
        name="brief",
        description=(
            "Gera um resumo do contexto atual: modelo, tools, "
            "arquivos no contexto, iterações e budget."
        ),
        parameters={},
        required=[],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        from nyx.agent.tools.registry import ToolRegistry

        try:
            reg = ToolRegistry(project_root)
            tool_names = sorted(t["function"]["name"] for t in reg.tool_defs)
        except Exception:
            tool_names = []

        lines = [
            "Resumo do contexto Nyx:",
            f"  Projeto: {project_root}",
            f"  Tools: {len(tool_names)} registradas",
            f"  Lista: {', '.join(tool_names[:15])}{'...' if len(tool_names) > 15 else ''}",
        ]

        return ActionResult(success=True, output="\n".join(lines))


# "A brevidade é a alma do espírito." -- Shakespeare
