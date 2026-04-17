"""Tool: MultiEdit -- Edição atômica de múltiplos arquivos."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef, validate_path

logger = logging.getLogger("nyx.tools.multi_edit")


class MultiEditTool(RegisteredTool):
    action_type = ActionType.EDIT_FILE

    tool_def = ToolDef(
        name="multi_edit",
        description=(
            "Aplica múltiplas edições atomicamente. "
            "Se uma falhar, reverte todas as anteriores."
        ),
        parameters={
            "edits": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "old_string": {"type": "string"},
                        "new_string": {"type": "string"},
                    },
                    "required": ["file_path", "old_string", "new_string"],
                },
                "description": "Lista de edições: [{file_path, old_string, new_string}]",
            },
        },
        required=["edits"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        edits = params.get("edits", [])
        if not edits:
            return ActionResult(success=False, error="Lista de edições vazia")

        if isinstance(edits, str):
            import json
            try:
                edits = json.loads(edits)
            except Exception as e:
                logger.warning("Formato de edições inválido: %s", e)
                return ActionResult(success=False, error="Formato de edições inválido")

        backups: list[tuple[Path, str]] = []
        modified: list[str] = []

        try:
            for i, edit in enumerate(edits):
                fp = str(edit.get("file_path", "")).strip()
                old = str(edit.get("old_string", ""))
                new = str(edit.get("new_string", ""))

                if not fp or not old:
                    raise ValueError(f"Edição #{i+1}: file_path ou old_string vazio")

                path = validate_path(fp, project_root)
                if not path.exists():
                    raise FileNotFoundError(f"Arquivo não encontrado: {fp}")

                content = path.read_text(encoding="utf-8")
                backups.append((path, content))

                if old not in content:
                    raise ValueError(f"Edição #{i+1}: old_string não encontrada em {fp}")

                new_content = content.replace(old, new, 1)
                path.write_text(new_content, encoding="utf-8")
                modified.append(fp)

            logger.info("MultiEdit: %d arquivos editados", len(modified))
            return ActionResult(
                success=True,
                output=f"Editados {len(modified)} arquivos: {', '.join(modified)}",
                files_modified=[str(p) for p, _ in backups],
            )

        except Exception as e:
            for path, original in backups:
                try:
                    path.write_text(original, encoding="utf-8")
                except Exception as e:
                    logger.warning("Falha ao reverter %s: %s", path, e)
            logger.warning("MultiEdit revertido: %s", e)
            return ActionResult(success=False, error=f"Revertido: {e}")


# "Atomicidade: tudo ou nada." -- princípio ACID
