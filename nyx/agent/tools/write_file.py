"""Tool: Write -- Cria ou sobrescreve arquivo."""

from __future__ import annotations

import logging
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef, validate_path

logger = logging.getLogger("nyx.tools.write_file")


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

        try:
            path = validate_path(file_path, project_root)
        except ValueError as e:
            return ActionResult(success=False, error=str(e))

        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return ActionResult(
                success=True,
                output=f"OK: Arquivo criado: {path} ({len(content)} bytes). Se a tarefa está completa, chame done().",
                files_modified=[str(path)],
            )
        except Exception as e:
            logger.error("Erro ao escrever %s: %s", path, e)
            return ActionResult(success=False, error=str(e))


# "Criar é dar forma ao que ainda não existe." -- Platão
