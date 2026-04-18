"""Tool: Analyze -- Análise estrutural de código."""

from __future__ import annotations

import ast
import logging
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.analyze")


class AnalyzeTool(RegisteredTool):
    action_type = ActionType.READ_FILE

    tool_def = ToolDef(
        name="analyze",
        description=(
            "Analisa estrutura de um arquivo: imports, classes, funções, linhas, complexidade. Suporta Python via AST."
        ),
        parameters={
            "file_path": {"type": "string", "description": "Caminho do arquivo"},
        },
        required=["file_path"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        file_path = str(params.get("file_path", "")).strip()
        if not file_path:
            return ActionResult(success=False, error="file_path vazio")

        path = Path(file_path) if file_path.startswith("/") else Path(project_root) / file_path
        if not path.exists():
            return ActionResult(success=False, error=f"Arquivo não encontrado: {file_path}", files_read=[str(path)])

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            return ActionResult(success=False, error=f"Erro ao ler: {e}")

        lines = content.split("\n")
        total_lines = len(lines)
        blank_lines = sum(1 for l in lines if not l.strip())

        if path.suffix == ".py":
            return self._analyze_python(content, path, total_lines, blank_lines)

        return self._analyze_generic(content, path, total_lines, blank_lines)

    def _analyze_python(self, content: str, path: Path, total: int, blank: int) -> ActionResult:
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return ActionResult(
                success=True,
                output=f"Análise de {path.name} ({total} linhas, {blank} vazias)\nErro de sintaxe: {e}",
                files_read=[str(path)],
            )

        imports: list[str] = []
        classes: list[str] = []
        functions: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                imports.append(f"{node.module}")
            elif isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                classes.append(f"{node.name} ({len(methods)} métodos)")
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not any(isinstance(p, ast.ClassDef) for p in ast.walk(tree)):
                    functions.append(node.name)

        # Recalcular funções top-level corretamente
        functions = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)

        lines = [
            f"Análise de {path.name}:",
            f"  Linhas: {total} ({blank} vazias)",
            f"  Imports: {len(imports)}",
        ]
        if imports:
            lines.append(f"    {', '.join(imports[:10])}")
        lines.append(f"  Classes: {len(classes)}")
        for c in classes:
            lines.append(f"    - {c}")
        lines.append(f"  Funções top-level: {len(functions)}")
        for f in functions[:15]:
            lines.append(f"    - {f}")

        return ActionResult(success=True, output="\n".join(lines), files_read=[str(path)])

    def _analyze_generic(self, content: str, path: Path, total: int, blank: int) -> ActionResult:
        import re

        func_pattern = re.compile(r"(?:def |function |fn |func )\s*(\w+)")
        class_pattern = re.compile(r"(?:class |struct |interface )\s*(\w+)")

        functions = func_pattern.findall(content)
        classes = class_pattern.findall(content)

        lines = [
            f"Análise de {path.name} ({path.suffix}):",
            f"  Linhas: {total} ({blank} vazias)",
            f"  Funções encontradas: {len(functions)}",
        ]
        if functions:
            lines.append(f"    {', '.join(functions[:15])}")
        lines.append(f"  Classes/structs: {len(classes)}")
        if classes:
            lines.append(f"    {', '.join(classes[:10])}")

        return ActionResult(success=True, output="\n".join(lines), files_read=[str(path)])


# "Analisar é decompor para compreender." -- Descartes
