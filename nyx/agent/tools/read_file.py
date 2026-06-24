"""Tool: Read -- Lê conteúdo de arquivo."""

from __future__ import annotations

from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import MAX_FILE_SIZE, RegisteredTool, ToolDef, validate_path

logger = get_logger("nyx.tools.read_file")


class ReadFileTool(RegisteredTool):
    action_type = ActionType.READ_FILE
    tool_def = ToolDef(
        name="read_file",
        description="Lê o conteúdo de um arquivo",
        parameters={
            "file_path": {
                "type": "string",
                "description": (
                    "Caminho do arquivo. Aceita caminho relativo (raiz do projeto) OU "
                    "qualquer caminho absoluto do disco (ex.: /etc/hosts, /home/user/outro-projeto/x.py)."
                ),
            },
        },
        required=["file_path"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        file_path = params.get("file_path", "")

        try:
            path = validate_path(file_path, project_root)
        except ValueError as e:
            return ActionResult(success=False, error=str(e))

        if not path.exists():
            return ActionResult(success=False, error=f"Arquivo não encontrado: {path}")
        if not path.is_file():
            return ActionResult(success=False, error=f"Não é um arquivo: {path}")

        file_size = path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            size_mb = file_size / 1_048_576
            return ActionResult(
                success=False,
                error=f"Arquivo muito grande: {size_mb:.1f}MB (limite: {MAX_FILE_SIZE // 1_048_576}MB)",
            )

        try:
            content = path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()
            numbered = "\n".join(f"{i + 1:4d}\t{line}" for i, line in enumerate(lines))
            return ActionResult(
                success=True,
                output=f"{numbered}\n[{len(lines)} linhas lidas. Analise e execute a próxima ação.]",
                files_read=[str(path)],
            )
        except Exception as e:
            logger.error("Erro ao ler %s: %s", path, e)
            return ActionResult(success=False, error=str(e))


# "Ler é o primeiro passo para entender." -- Francis Bacon
