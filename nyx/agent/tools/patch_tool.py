"""Tool: Patch -- Aplica unified diff a um arquivo."""

from __future__ import annotations

import re
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import RegisteredTool, ToolDef, validate_path

logger = get_logger("nyx.tools.patch")


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
            # PATCH-HUNK-OFFSET-HONEST-01: segmenta o patch em hunks. O
            # cabeçalho @@ -a,b +c,d @@ carrega a linha-alvo; ignora-lo
            # (comportamento antigo) aplicava tudo no topo e retornava
            # success=True -> corrupção silenciosa.
            hunk_header = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")
            hunks: list[dict[str, Any]] = []
            current: dict[str, Any] | None = None
            for pline in patch_lines:
                if pline.startswith("---") or pline.startswith("+++"):
                    continue
                m = hunk_header.match(pline)
                if m:
                    current = {"start": int(m.group(1)) - 1, "body": []}
                    hunks.append(current)
                    continue
                if current is None:
                    current = {"start": None, "body": []}
                    hunks.append(current)
                if pline.startswith(("-", "+", " ")) or not pline.strip():
                    current["body"].append(pline)

            def _locate(lines: list[str], pre: list[str], hint: int | None) -> int | None:
                if not pre:
                    return hint if hint is not None else 0
                n = len(pre)

                def _match(i: int) -> bool:
                    return i >= 0 and i + n <= len(lines) and all(
                        lines[i + k].rstrip() == pre[k].rstrip() for k in range(n)
                    )

                if hint is not None and _match(hint):
                    return hint
                found = [i for i in range(len(lines) - n + 1) if _match(i)]
                if len(found) == 1:
                    return found[0]
                return None  # zero ou ambiguo -> falha honesta

            for hunk in hunks:
                body = hunk["body"]
                pre = [ln[1:] for ln in body if ln.startswith((" ", "-")) or not ln.strip()]
                pos = _locate(result_lines, pre, hunk["start"])
                if pos is None:
                    alvo = (hunk["start"] + 1) if hunk["start"] is not None else "?"
                    return ActionResult(
                        success=False,
                        error=(
                            f"hunk não casa no arquivo (alvo ~linha {alvo}). "
                            "Releia o arquivo com read_file e gere o diff de novo, "
                            "ou use edit_file com o trecho exato."
                        ),
                    )
                rebuilt: list[str] = []
                for ln in body:
                    if ln.startswith("+"):
                        rebuilt.append(ln[1:])
                        additions += 1
                    elif ln.startswith("-"):
                        removals += 1
                    else:
                        rebuilt.append(ln[1:] if ln.startswith(" ") else ln)
                result_lines[pos : pos + len(pre)] = rebuilt

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
