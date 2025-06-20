"""Tool: Glob -- Busca arquivos por padrão."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef


class GlobTool(RegisteredTool):
    action_type = ActionType.GLOB
    tool_def = ToolDef(
        name="glob",
        description="Busca arquivos por padrão glob (ex: **/*.py, src/**/*.ts)",
        parameters={
            "pattern": {"type": "string", "description": "Padrão glob"},
        },
        required=["pattern"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        pattern = params.get("pattern", "")
        root = Path(project_root)

        try:
            matches = sorted(str(p.relative_to(root)) for p in root.glob(pattern) if p.is_file())
            if not matches:
                return ActionResult(success=True, output=f"Nenhum arquivo encontrado para: {pattern}")
            result = "\n".join(matches[:200])
            if len(matches) > 200:
                result += f"\n... e mais {len(matches) - 200} arquivos"
            return ActionResult(success=True, output=result + "\n[Analise e execute a próxima ação.]")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


# "Buscar é o começo de encontrar." -- Heráclito
