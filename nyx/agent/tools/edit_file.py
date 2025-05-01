"""Tool: Edit -- Substitui trecho de texto em arquivo."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef


class EditFileTool(RegisteredTool):
    action_type = ActionType.EDIT_FILE
    tool_def = ToolDef(
        name="edit_file",
        description="Substitui um trecho de texto em um arquivo existente",
        parameters={
            "file_path": {"type": "string", "description": "Caminho do arquivo"},
            "old_string": {"type": "string", "description": "Texto a ser substituído"},
            "new_string": {"type": "string", "description": "Texto substituto"},
        },
        required=["file_path", "old_string", "new_string"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        file_path = params.get("file_path", "")
        old_string = params.get("old_string", "")
        new_string = params.get("new_string", "")
        path = Path(project_root) / file_path if not Path(file_path).is_absolute() else Path(file_path)

        if not path.exists():
            return ActionResult(success=False, error=f"Arquivo não encontrado: {path}")

        try:
            content = path.read_text(encoding="utf-8")
            if old_string not in content:
                return ActionResult(success=False, error=f"Trecho não encontrado no arquivo: '{old_string[:60]}...'")

            count = content.count(old_string)
            if count > 1:
                return ActionResult(success=False, error=f"Trecho encontrado {count} vezes. Forneça mais contexto.")

            new_content = content.replace(old_string, new_string, 1)
            path.write_text(new_content, encoding="utf-8")
            return ActionResult(
                success=True,
                output=f"Editado: {path} (1 substituição)",
                files_modified=[str(path)],
            )
        except Exception as e:
            return ActionResult(success=False, error=str(e))


# "Editar é a arte de remover o desnecessário." -- Antoine de Saint-Exupéry
