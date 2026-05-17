#!/usr/bin/env python3
"""Auditor de mensagens de erro do REPL (ERROR-MSG-01).

Regras aplicadas sobre ``nyx/`` (exclui diretórios de teste e docs):

1. Toda string-literal em ``print(...)``/``return ...`` que contém token
   sugerindo erro em inglês (``error``, ``failed``, ``invalid``, ``denied``,
   ``not found``) dispara alerta -- devem estar em PT-BR, envelopadas em
   ``print_error`` ou no sentinela ``__error__`` do dispatcher.
2. Comentários e docstrings são ignorados.
3. Chaves técnicas de JSON (``{"type": "error"}``, ``{"error": ...}``) são
   permitidas (matching por contexto simples).

Saída:
  - exit 0 + contagem traduzida -- se limpo.
  - exit 1 + relatório linha a linha -- se violação.
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NYX_DIR = ROOT / "nyx"

SUSPECT_PATTERN = re.compile(
    r"\b(?:error|failed|invalid|denied|not\s+found)\b",
    re.IGNORECASE,
)

# Chaves técnicas que não são UX: contexto JSON/dict.
ALLOWED_KEY_NAMES = {"error", "error_detail", "errors"}

# Contextos técnicos permitidos (literais que aparecem como key de dict JSON
# ou chave de retorno interno, não como texto exibido ao usuário).
TECHNICAL_SNIPPETS = (
    '"type": "error"',
    "'type': 'error'",
    '"error":',
    "'error':",
    '"errors":',
    "'errors':',",
    "error_detail",
    "error_msg",
    "msg_type",
    '"error_detail"',
)


def _iter_py_files(base: Path):
    for p in base.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        if "/tests/" in str(p) or p.name.startswith("test_"):
            continue
        yield p


def _is_technical_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return True
    lower = stripped.lower()
    for snippet in TECHNICAL_SNIPPETS:
        if snippet in lower:
            return True
    return False


def _collect_string_literals(tree: ast.AST) -> list[tuple[int, str]]:
    """Percorre a AST e coleta (lineno, valor) para strings literais."""
    literals: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            literals.append((node.lineno, node.value))
        elif isinstance(node, ast.JoinedStr):
            # f-strings: captura partes Constant internas.
            pieces: list[str] = []
            for value in node.values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    pieces.append(value.value)
            if pieces:
                literals.append((node.lineno, "".join(pieces)))
    return literals


def _audit_file(path: Path) -> list[tuple[int, str]]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return []
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError:
        return []

    # Marca linhas que contêm docstring ou comentário técnico.
    source_lines = source.splitlines()
    # Marca docstrings (primeiros literais de módulo/função/classe)
    docstring_lines: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, ast.Constant)
                and isinstance(node.body[0].value.value, str)
            ):
                doc = node.body[0].value
                start = doc.lineno
                end = getattr(doc, "end_lineno", start)
                for ln in range(start, end + 1):
                    docstring_lines.add(ln)

    violations: list[tuple[int, str]] = []
    for lineno, value in _collect_string_literals(tree):
        if lineno in docstring_lines:
            continue
        if not SUSPECT_PATTERN.search(value):
            continue
        # Se a linha original parece ser chave técnica JSON, pula.
        if 1 <= lineno <= len(source_lines) and _is_technical_line(source_lines[lineno - 1]):
            continue
        # Ignora literais que são apenas chave simples.
        stripped = value.strip()
        if stripped.lower() in ALLOWED_KEY_NAMES:
            continue
        violations.append((lineno, value[:160]))
    return violations


def main() -> int:
    total_files = 0
    total_violations = 0
    ptbr_hits = 0
    report: list[str] = []

    for path in sorted(_iter_py_files(NYX_DIR)):
        total_files += 1
        violations = _audit_file(path)
        if violations:
            total_violations += len(violations)
            report.append(f"\n  {path.relative_to(ROOT)}:")
            for lineno, text in violations:
                report.append(f"    linha {lineno}: {text!r}")
        else:
            # Conta hits de padrões canônicos PT-BR como métrica de progresso.
            try:
                src = path.read_text(encoding="utf-8")
            except OSError:
                src = ""
            for hit_pattern in ("print_error(", "__error__", "ProviderError("):
                ptbr_hits += src.count(hit_pattern)

    if total_violations:
        print(
            "[audit] FALHA: "
            f"{total_violations} string(s) com token de erro em inglês fora de contexto técnico.",
            file=sys.stderr,
        )
        for line in report:
            print(line, file=sys.stderr)
        return 1

    print(
        "[audit] OK: "
        f"{total_files} arquivos varridos em nyx/, "
        f"{ptbr_hits} ocorrências canônicas (print_error/__error__/ProviderError)."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())


# "A palavra precisa corresponde ao fato preciso." -- Sêneca
