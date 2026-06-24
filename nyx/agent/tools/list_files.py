"""Tool: List -- Lista arquivos de um diretório."""

from __future__ import annotations

from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import (
    RegisteredTool,
    ToolDef,
    display_path,
    get_active_project_root,
    validate_path,
)

logger = get_logger("nyx.tools.list_files")


class ListFilesTool(RegisteredTool):
    action_type = ActionType.LIST_FILES
    tool_def = ToolDef(
        name="list_files",
        description="Lista arquivos e diretórios de um caminho",
        parameters={
            "path": {
                "type": "string",
                "description": (
                    "Diretório a listar. Aceita caminho relativo (raiz do projeto) OU "
                    "qualquer caminho absoluto do disco (ex.: /etc, /home/user/outro-projeto)."
                ),
            },
        },
        required=[],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        target_path = params.get("path", ".")

        try:
            target = validate_path(target_path, project_root)
        except ValueError as e:
            return ActionResult(success=False, error=str(e))

        if not target.exists():
            return ActionResult(success=False, error=f"Diretório não encontrado: {target}")

        # FS-DISCOVERY-FREE-01: base de display = raiz ativa (segue /cd), via
        # display_path (fonte única com glob/search). Dentro dela mostra
        # relativo (idêntico ao comportamento anterior); fora, absoluto.
        base = get_active_project_root()

        try:
            entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name))
            lines = []
            for e in entries[:200]:
                prefix = "d " if e.is_dir() else "f "
                rel = display_path(e.resolve(), base)
                lines.append(f"{prefix}{rel}")
            result = "\n".join(lines)
            if len(entries) > 200:
                result += f"\n... e mais {len(entries) - 200} itens"
            return ActionResult(success=True, output=result + "\n[Analise e execute a próxima ação.]")
        except Exception as e:
            logger.error("Erro ao listar %s: %s", target, e)
            return ActionResult(success=False, error=str(e))


# "Listar é organizar o caos." -- Marie Kondo
