"""Tool: Write -- Cria ou sobrescreve arquivo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef


class WriteFileTool(RegisteredTool):
    action_type = ActionType.WRITE_FILE
    tool_def = ToolDef(
        name="write_file",
        description="Cria ou sobrescreve um arquivo com o conteúdo fornecido",
        parameters={
            "file_path": {"type": "string", "description": "Caminho do arquivo"},
            "content": {"type": "string", "description": "Conteúdo a escrever"},
        },
        required=["file_path", "content"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        file_path = params.get("file_path", "")
        content = params.get("content", "")
        path = Path(project_root) / file_path if not Path(file_path).is_absolute() else Path(file_path)

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return ActionResult(
                success=True,
                output=f"OK: Arquivo criado: {path} ({len(content)} bytes). Se a tarefa está completa, chame done().",
                files_modified=[str(path)],
            )
        except Exception as e:
            return ActionResult(success=False, error=str(e))


# "Criar é dar forma ao que ainda não existe." -- Platão
