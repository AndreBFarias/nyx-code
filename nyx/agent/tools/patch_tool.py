"""Tool: Patch -- Aplica unified diff a um arquivo."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef, validate_path

logger = logging.getLogger("nyx.tools.patch")


class PatchTool(RegisteredTool):
    action_type = ActionType.EDIT_FILE

    tool_def = ToolDef(
        name="patch",
        description=(
            "Aplica um patch em formato unified diff a um arquivo. "
            "O patch deve ter linhas começando com +, -, ou espaço."
        ),
        parameters={
            "file_path": {"type": "string", "description": "Caminho do arquivo"},
            "patch": {"type": "string", "description": "Conteúdo do patch (unified diff)"},
        },
        required=["file_path", "patch"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        file_path = str(params.get("file_path", "")).strip()
        patch_content = str(params.get("patch", "")).strip()

        if not file_path:
            return ActionResult(success=False, error="file_path vazio")
        if not patch_content:
            return ActionResult(success=False, error="patch vazio")

        try:
            path = validate_path(file_path, project_root)
        except ValueError as e:
            return ActionResult(success=False, error=str(e))

        if not path.exists():
            return ActionResult(success=False, error=f"Arquivo não encontrado: {file_path}")

        try:
            original = path.read_text(encoding="utf-8")
        except Exception as e:
            return ActionResult(success=False, error=f"Erro ao ler: {e}")

        original_lines = original.split("\n")
        patch_lines = patch_content.split("\n")

        additions = 0
        removals = 0
        result_lines = list(original_lines)

        try:
            line_idx = 0
            for pline in patch_lines:
                if pline.startswith("---") or pline.startswith("+++") or pline.startswith("@@"):
                    continue
                if pline.startswith("-"):
                    content = pline[1:]
                    if line_idx < len(result_lines) and result_lines[line_idx].rstrip() == content.rstrip():
                        result_lines.pop(line_idx)
                        removals += 1
                    else:
                        line_idx += 1
                elif pline.startswith("+"):
                    content = pline[1:]
                    result_lines.insert(line_idx, content)
                    additions += 1
                    line_idx += 1
                elif pline.startswith(" ") or not pline.strip():
                    line_idx += 1

            new_content = "\n".join(result_lines)
            path.write_text(new_content, encoding="utf-8")

            logger.info("Patch aplicado: %s (+%d -%d)", file_path, additions, removals)
            return ActionResult(
                success=True,
                output=f"Patch aplicado: {file_path} (+{additions} -{removals} linhas)",
                files_modified=[str(path)],
            )

        except Exception as e:
            return ActionResult(success=False, error=f"Falha ao aplicar patch: {e}")


# "A parte é mais complexa que o todo." -- Blaise Pascal
