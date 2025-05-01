"""Tool: Read -- Lê conteúdo de arquivo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef


class ReadFileTool(RegisteredTool):
    action_type = ActionType.READ_FILE
    tool_def = ToolDef(
        name="read_file",
        description="Lê o conteúdo de um arquivo",
        parameters={
            "file_path": {"type": "string", "description": "Caminho do arquivo"},
        },
        required=["file_path"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        file_path = params.get("file_path", "")
        path = Path(project_root) / file_path if not Path(file_path).is_absolute() else Path(file_path)

        if not path.exists():
            return ActionResult(success=False, error=f"Arquivo não encontrado: {path}")
        if not path.is_file():
            return ActionResult(success=False, error=f"Não é um arquivo: {path}")

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            numbered = "\n".join(f"{i+1:4d}\t{line}" for i, line in enumerate(lines))
            return ActionResult(
                success=True,
                output=numbered,
                files_read=[str(path)],
            )
        except Exception as e:
            return ActionResult(success=False, error=str(e))


# "Ler é o primeiro passo para entender." -- Francis Bacon
