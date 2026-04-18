"""Tool: Search/Grep -- Busca texto em arquivos."""

from __future__ import annotations

import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef, validate_path

logger = logging.getLogger("nyx.tools.search")

EXCLUDE_DIRS = {"__pycache__", ".git", "node_modules", "venv", ".venv", "dist"}
_SEARCH_TIMEOUT = 30


class SearchTool(RegisteredTool):
    action_type = ActionType.SEARCH
    tool_def = ToolDef(
        name="search",
        description="Busca texto (regex) em arquivos do projeto (grep)",
        parameters={
            "pattern": {"type": "string", "description": "Regex para buscar"},
            "path": {"type": "string", "description": "Diretório ou arquivo (padrão: raiz)"},
        },
        required=["pattern"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        pattern = params.get("pattern", "")
        search_path = params.get("path", ".")
        root = Path(project_root)

        try:
            target = validate_path(search_path, project_root)
        except ValueError as e:
            return ActionResult(success=False, error=str(e))

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return ActionResult(success=False, error=f"Regex inválido: {e}")

        fast = self._search_fast(pattern, target, root)
        if fast is not None:
            return fast

        return self._search_walk(regex, target, root)

    def _search_fast(self, pattern: str, target: Path, root: Path) -> ActionResult | None:
        """Busca rápida via rg ou grep. Retorna None se indisponível."""
        for cmd in ("rg", "grep"):
            binary = shutil.which(cmd)
            if not binary:
                continue

            args: list[str] = []
            if cmd == "rg":
                args = [binary, "-in", "--max-count=100", "--no-heading", pattern, str(target)]
            else:
                args = [binary, "-rin", "--max-count=100", pattern, str(target)]

            try:
                proc = subprocess.run(
                    args,
                    capture_output=True,
                    text=True,
                    timeout=_SEARCH_TIMEOUT,
                    cwd=str(root),
                )
                if proc.returncode not in (0, 1):
                    continue

                output = proc.stdout.strip()
                if not output:
                    return ActionResult(success=True, output=f"Nenhum resultado para: {pattern}")

                lines = output.splitlines()[:100]
                result = "\n".join(lines)
                if len(lines) >= 100:
                    result += "\n... (limitado a 100 resultados)"
                logger.info("Busca rápida via %s: %d resultados", cmd, len(lines))
                return ActionResult(success=True, output=result + "\n[Analise e execute a próxima ação.]")
            except Exception as e:
                logger.debug("Busca rápida via %s falhou: %s", cmd, e)
                continue

        return None

    def _search_walk(self, regex: re.Pattern, target: Path, root: Path) -> ActionResult:
        """Busca lenta via walk Python (fallback)."""
        matches: list[str] = []
        try:
            files = [target] if target.is_file() else sorted(target.rglob("*"))
            for f in files:
                if not f.is_file():
                    continue
                rel = str(f.relative_to(root))
                if any(exc in rel.split("/") for exc in EXCLUDE_DIRS):
                    continue
                if f.suffix not in {
                    ".py",
                    ".sh",
                    ".md",
                    ".json",
                    ".yml",
                    ".toml",
                    ".txt",
                    ".css",
                    ".html",
                    ".js",
                    ".ts",
                }:
                    continue
                try:
                    for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                        if regex.search(line):
                            matches.append(f"{rel}:{i}: {line.strip()[:120]}")
                            if len(matches) >= 100:
                                break
                except Exception as e:
                    logger.debug("Falha ao ler %s: %s", f, e)
                if len(matches) >= 100:
                    break
        except Exception as e:
            return ActionResult(success=False, error=str(e))

        if not matches:
            return ActionResult(success=True, output=f"Nenhum resultado para: {regex.pattern}")

        result = "\n".join(matches)
        if len(matches) >= 100:
            result += "\n... (limitado a 100 resultados)"
        return ActionResult(success=True, output=result + "\n[Analise e execute a próxima ação.]")


# "Quem procura, encontra." -- Mateus 7:7
