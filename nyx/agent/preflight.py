"""Preflight -- Validação pré-execução de tools."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("nyx.preflight")


@dataclass
class PreflightResult:
    ok: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def check(tool_name: str, args: dict[str, Any], project_root: str) -> PreflightResult:
    """Valida ação antes de executar."""
    result = PreflightResult()

    file_path = args.get("file_path", args.get("path", ""))

    if tool_name in ("read_file", "edit_file") and file_path:
        path = Path(file_path) if file_path.startswith("/") else Path(project_root) / file_path
        if not path.exists():
            result.warnings.append(f"Arquivo não existe: {file_path}")
        elif path.stat().st_size > 1_000_000:
            result.warnings.append(f"Arquivo grande: {path.stat().st_size / 1024:.0f}KB")

    if tool_name == "write_file" and file_path:
        path = Path(file_path) if file_path.startswith("/") else Path(project_root) / file_path
        parent = path.parent
        if not parent.exists():
            result.warnings.append(f"Diretório pai não existe: {parent}")

    if tool_name == "run_command":
        command = args.get("command", "")
        dangerous = [
            "rm -rf /",
            "rm -rf /*",
            "sudo ",
            "mkfs",
            "dd if=/dev/",
            "> /dev/sda",
            "> /dev/null >",
            "chmod 777 /",
            "chown root",
            "curl | sh",
            "curl | bash",
            "wget -O- | sh",
            "wget -O- | bash",
            ":(){ :|:& };:",
        ]
        for d in dangerous:
            if d in command:
                result.errors.append(f"Comando potencialmente destrutivo: {d}")
                result.ok = False

    if tool_name == "edit_file":
        old_string = args.get("old_string", "")
        if not old_string:
            result.warnings.append("old_string vazio -- edição pode falhar")

    if result.errors:
        result.ok = False

    return result


# "Prevenir é melhor que remediar." -- Erasmo de Rotterdam
