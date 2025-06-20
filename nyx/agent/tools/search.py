"""Tool: Search/Grep -- Busca texto em arquivos."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

EXCLUDE_DIRS = {"__pycache__", ".git", "node_modules", "venv", ".venv", "dist"}


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
        target = root / search_path if not Path(search_path).is_absolute() else Path(search_path)

        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error as e:
            return ActionResult(success=False, error=f"Regex inválido: {e}")

        matches: list[str] = []
        try:
            files = [target] if target.is_file() else sorted(target.rglob("*"))
            for f in files:
                if not f.is_file():
                    continue
                rel = str(f.relative_to(root))
                if any(exc in rel.split("/") for exc in EXCLUDE_DIRS):
                    continue
                if f.suffix not in {".py", ".sh", ".md", ".json", ".yml", ".toml", ".txt", ".css", ".html", ".js", ".ts"}:
                    continue
                try:
                    for i, line in enumerate(f.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                        if regex.search(line):
                            matches.append(f"{rel}:{i}: {line.strip()[:120]}")
                            if len(matches) >= 100:
                                break
                except Exception:
                    pass
                if len(matches) >= 100:
                    break
        except Exception as e:
            return ActionResult(success=False, error=str(e))

        if not matches:
            return ActionResult(success=True, output=f"Nenhum resultado para: {pattern}")

        result = "\n".join(matches)
        if len(matches) >= 100:
            result += "\n... (limitado a 100 resultados)"
        return ActionResult(success=True, output=result + "\n[Analise e execute a próxima ação.]")


# "Quem procura, encontra." -- Mateus 7:7
