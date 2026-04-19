"""Tool: write_memory -- grava memória persistente cross-session."""

from __future__ import annotations

from typing import Any

from nyx.agent.memory import NyxMemory
from nyx.agent.models import ActionResult, ActionType
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = get_logger("nyx.tools.write_memory")


class WriteMemoryTool(RegisteredTool):
    action_type = ActionType.WRITE_MEMORY
    tool_def = ToolDef(
        name="write_memory",
        description=(
            "Grava memória persistente sobre o projeto ou o desenvolvedor "
            "(convenções, preferências, decisões estáveis). Armazena em "
            "~/.nyx/memory/<projeto>/. Use só para fatos que continuam válidos "
            "entre sessões."
        ),
        parameters={
            "file": {
                "type": "string",
                "description": "Nome curto do arquivo (sem extensão, ex: 'preferencias_teste')",
            },
            "content": {
                "type": "string",
                "description": "Conteúdo markdown da memória, máximo 4KB",
            },
            "reason": {
                "type": "string",
                "description": "Motivo curto (1 linha) que vai no índice",
            },
        },
        required=["file", "content", "reason"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        file = params.get("file", "")
        content = params.get("content", "")
        reason = params.get("reason", "")

        if not file:
            return ActionResult(success=False, error="Parâmetro 'file' é obrigatório")
        if not content:
            return ActionResult(success=False, error="Parâmetro 'content' é obrigatório")
        if not reason:
            return ActionResult(success=False, error="Parâmetro 'reason' é obrigatório")

        try:
            memory = NyxMemory(project_root)
            path = memory.write(file, content, reason)
        except ValueError as e:
            return ActionResult(success=False, error=str(e))
        except OSError as e:
            logger.error("Erro ao gravar memória: %s", e)
            return ActionResult(success=False, error=f"Falha de I/O: {e}")

        return ActionResult(
            success=True,
            output=f"OK: Memória gravada em {path} ({len(content)} bytes).",
            files_modified=[str(path)],
        )


# "Quem não se lembra do passado está condenado a repeti-lo." -- Santayana
