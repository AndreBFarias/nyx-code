"""Preflight -- Validação pré-execução de tools."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.preflight")


@dataclass
class PreflightResult:
    ok: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def check(
    tool_name: str,
    args: dict[str, Any],
    project_root: str,
    extra_roots: list[str] | None = None,
) -> PreflightResult:
    """Valida ação antes de executar.

    PROJECT-ROOTS-MULTI-01: ``extra_roots`` opcional só amplia a base de
    resolução para warnings de existência (read/edit) e diretório pai
    (write). O gate real de sandbox segue em ``tools/base.validate_path``.
    """
    result = PreflightResult()

    file_path = args.get("file_path", args.get("path", ""))

    # Bases candidatas para resolver paths relativos antes do warning.
    # project_root é sempre a primeira; extras só ampliam.
    _roots = [project_root, *(extra_roots or [])]

    def _resolve_first_existing(rel: str) -> Path:
        for r in _roots:
            cand = Path(r) / rel
            if cand.exists():
                return cand
        return Path(_roots[0]) / rel

    if tool_name in ("read_file", "edit_file") and file_path:
        path = (
            Path(file_path)
            if file_path.startswith("/")
            else _resolve_first_existing(file_path)
        )
        if not path.exists():
            result.warnings.append(f"Arquivo não existe: {file_path}")
        elif path.stat().st_size > 1_000_000:
            result.warnings.append(f"Arquivo grande: {path.stat().st_size / 1024:.0f}KB")

    if tool_name == "write_file" and file_path:
        path = (
            Path(file_path)
            if file_path.startswith("/")
            else _resolve_first_existing(file_path)
        )
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
