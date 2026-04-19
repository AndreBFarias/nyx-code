"""Tool: Glob -- Busca arquivos por padrão."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import RegisteredTool, ToolDef, validate_path

logger = get_logger("nyx.tools.glob")


class GlobTool(RegisteredTool):
    action_type = ActionType.GLOB
    tool_def = ToolDef(
        name="glob",
        description="Busca arquivos por padrão glob (ex: **/*.py, src/**/*.ts)",
        parameters={
            "pattern": {"type": "string", "description": "Padrão glob"},
            "path": {"type": "string", "description": "Diretório base (padrão: raiz do projeto)"},
        },
        required=["pattern"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        pattern = params.get("pattern", "")
        base_path = params.get("path", ".")

        try:
            root = validate_path(base_path, project_root)
        except ValueError as e:
            return ActionResult(success=False, error=str(e))

        project = Path(project_root).resolve()

        try:
            matches = sorted(
                str(p.relative_to(project))
                for p in root.glob(pattern)
                if p.is_file() and p.resolve().is_relative_to(project)
            )
            if not matches:
                return ActionResult(success=True, output=f"Nenhum arquivo encontrado para: {pattern}")
            result = "\n".join(matches[:200])
            if len(matches) > 200:
                result += f"\n... e mais {len(matches) - 200} arquivos"
            return ActionResult(success=True, output=result + "\n[Analise e execute a próxima ação.]")
        except Exception as e:
            logger.error("Erro no glob %s: %s", pattern, e)
            return ActionResult(success=False, error=str(e))


# "Buscar é o começo de encontrar." -- Heráclito
