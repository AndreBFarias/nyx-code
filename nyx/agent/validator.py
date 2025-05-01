"""PostValidator -- Validação pós-execução de tools."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from nyx.agent.models import ActionResult

logger = logging.getLogger("nyx.validator")


@dataclass
class ValidationResult:
    ok: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate(tool_name: str, args: dict[str, Any], result: ActionResult) -> ValidationResult:
    """Valida resultado após execução de tool."""
    vr = ValidationResult()

    if not result.success:
        return vr

    if tool_name == "write_file":
        content = args.get("content", "")
        if not content:
            vr.warnings.append("Arquivo criado sem conteúdo")
        output = result.output or ""
        if "0 bytes" in output:
            vr.warnings.append("Arquivo vazio criado")

    if tool_name == "run_command":
        output = result.output or ""
        error_markers = ["error", "traceback", "exception", "fatal"]
        lower_out = output.lower()
        for marker in error_markers:
            if marker in lower_out:
                vr.warnings.append(f"Output contém '{marker}' -- verificar resultado")
                break

    if tool_name == "edit_file":
        output = result.output or ""
        if "0 substituição" in output or "0 substituições" in output:
            vr.warnings.append("Nenhuma substituição realizada")

    if vr.errors:
        vr.ok = False

    return vr


# "Confiar mas verificar." -- Ronald Reagan
