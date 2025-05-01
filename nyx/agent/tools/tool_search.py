"""Tool: ToolSearch -- Busca tools por nome ou descrição."""

from __future__ import annotations

import logging
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.tool_search")


class ToolSearchTool(RegisteredTool):
    action_type = ActionType.READ_FILE

    tool_def = ToolDef(
        name="tool_search",
        description=(
            "Busca tools disponíveis por nome ou descrição. "
            "Retorna lista de matches com nome e descrição."
        ),
        parameters={
            "query": {"type": "string", "description": "Termo de busca"},
            "max_results": {
                "type": "integer",
                "description": "Máximo de resultados (padrão 10)",
            },
        },
        required=["query"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        query = str(params.get("query", "")).strip().lower()
        if not query:
            return ActionResult(success=False, error="Query vazia")

        max_results = int(params.get("max_results", 10))

        from nyx.agent.tools.registry import ToolRegistry
        reg = ToolRegistry(project_root)

        matches: list[tuple[str, str]] = []
        for tool_def in reg.tool_defs:
            fn = tool_def.get("function", {})
            name = fn.get("name", "")
            desc = fn.get("description", "")

            if query in name.lower() or query in desc.lower():
                matches.append((name, desc[:100]))

        if not matches:
            return ActionResult(
                success=True,
                output=f"Nenhuma tool encontrada para '{query}'. {reg.tool_count} tools disponíveis.",
            )

        matches = matches[:max_results]
        lines = [f"Resultados para '{query}' ({len(matches)} encontradas):"]
        for name, desc in matches:
            lines.append(f"  - {name}: {desc}")

        return ActionResult(success=True, output="\n".join(lines))


# "Quem busca, encontra." -- Mateus 7:7
