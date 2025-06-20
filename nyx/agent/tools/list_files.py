"""Tool: List -- Lista arquivos de um diretório."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef


class ListFilesTool(RegisteredTool):
    action_type = ActionType.LIST_FILES
    tool_def = ToolDef(
        name="list_files",
        description="Lista arquivos e diretórios de um caminho",
        parameters={
            "path": {"type": "string", "description": "Diretório a listar (padrão: raiz)"},
        },
        required=[],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        target_path = params.get("path", ".")
        root = Path(project_root)
        target = root / target_path if not Path(target_path).is_absolute() else Path(target_path)

        if not target.exists():
            return ActionResult(success=False, error=f"Diretório não encontrado: {target}")

        try:
            entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            lines = []
            for e in entries[:200]:
                prefix = "d " if e.is_dir() else "f "
                rel = str(e.relative_to(root)) if e.is_relative_to(root) else str(e)
                lines.append(f"{prefix}{rel}")
            result = "\n".join(lines)
            if len(entries) > 200:
                result += f"\n... e mais {len(entries) - 200} itens"
            return ActionResult(success=True, output=result + "\n[Analise e execute a próxima ação.]")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


# "Listar é organizar o caos." -- Marie Kondo
