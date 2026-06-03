"""RepoMap -- índice de símbolos Python via AST, injetado no prompt.

Inspirado no aider: evita que o modelo precise de list_files + grep_files +
read_file pra descobrir onde está definida uma classe ou função. O mapa é
regenerado por arquivo (com cache por mtime) e recortado a um orçamento de
bytes antes de entrar no system prompt.
"""

from __future__ import annotations

import ast
import json
import time
from pathlib import Path
from typing import Iterable

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.repomap")

CACHE_FILE = Path.home() / ".nyx" / "cache" / "repomap.json"
DEFAULT_BUDGET_BYTES = 2048
EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "venv",
    ".venv",
    "env",
    ".env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    "dist",
    "build",
    ".tox",
    "openclaud",
    "logs",
    ".nyx",
}


def _looks_like_flat_entry(value: dict) -> bool:
    """True se `value` é uma entrada de arquivo (formato de cache antigo, flat).

    No formato antigo o top-level era {rel_path: {mtime, symbols}}; no novo é
    {root_abs: {rel_path: {mtime, symbols}}}. Uma entrada flat tem `mtime` direto;
    um bucket de root não. Usado para descartar o cache legado na primeira gravação.
    """
    return "mtime" in value or "symbols" in value


def _is_excluded(path: Path, root: Path) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in EXCLUDE_DIRS for part in rel.parts)


def _extract_symbols(source: str) -> list[str]:
    """Extrai classes e funções top-level (e métodos top-level das classes)."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    symbols: list[str] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)) and not child.name.startswith("_")
            ][:6]
            if methods:
                symbols.append(f"class {node.name}({', '.join(methods)})")
            else:
                symbols.append(f"class {node.name}")
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                symbols.append(f"def {node.name}")
    return symbols


def _priority(rel_path: str, touched: set[str]) -> int:
    """Prioridade (menor = mais importante) para ordenar no render."""
    if rel_path in touched:
        return 0
    if rel_path.startswith("nyx/agent/"):
        return 1
    if rel_path.startswith("nyx/services/") or rel_path.startswith("nyx/tools/"):
        return 2
    if rel_path.startswith("nyx/"):
        return 3
    return 4


class RepoMap:
    """Gerador de mapa de símbolos com cache por mtime."""

    def __init__(self, root: Path | str) -> None:
        self._root = Path(root).resolve()
        self._cache: dict[str, dict] = {}
        self._load_cache()

    @property
    def root(self) -> Path:
        return self._root

    @property
    def cache_path(self) -> Path:
        return CACHE_FILE

    def _load_cache(self) -> None:
        # CD-REPOMAP-REPOINT-01: o cache em disco é namespiado pelo root absoluto
        # ({root: {rel: {mtime, symbols}}}). Sem isto, dois projetos com arquivos
        # de mesmo path relativo (ex.: ambos com "modulo.py") colidem: a chave
        # relativa é a mesma e, no mesmo segundo de mtime, o build de um serve os
        # símbolos do outro. Em memória, self._cache continua {rel: {...}} do root
        # atual (contrato preservado para invalidate/render).
        if not CACHE_FILE.exists():
            return
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Cache de repomap corrompido (%s), reiniciando", e)
            self._cache = {}
            return
        if not isinstance(data, dict):
            return
        bucket = data.get(str(self._root))
        if isinstance(bucket, dict):
            self._cache = {k: v for k, v in bucket.items() if isinstance(v, dict)}

    def save_cache(self) -> None:
        # Mescla preservando os buckets de outros roots já persistidos.
        try:
            CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
            store: dict[str, dict] = {}
            if CACHE_FILE.exists():
                try:
                    existing = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
                    if isinstance(existing, dict):
                        store = {
                            k: v
                            for k, v in existing.items()
                            if isinstance(v, dict) and not _looks_like_flat_entry(v)
                        }
                except (OSError, json.JSONDecodeError):
                    store = {}
            store[str(self._root)] = self._cache
            CACHE_FILE.write_text(
                json.dumps(store, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as e:
            logger.warning("Falha ao salvar cache repomap: %s", e)

    def _iter_py_files(self) -> Iterable[Path]:
        for path in self._root.rglob("*.py"):
            if not path.is_file():
                continue
            if _is_excluded(path, self._root):
                continue
            yield path

    def build(self) -> dict[str, list[str]]:
        """Reindexa respeitando cache por mtime. Retorna {rel_path: [symbols]}."""
        t0 = time.monotonic()
        result: dict[str, list[str]] = {}
        live_keys: set[str] = set()

        for path in self._iter_py_files():
            try:
                mtime = int(path.stat().st_mtime)
            except OSError:
                continue
            rel = str(path.relative_to(self._root))
            live_keys.add(rel)

            cached = self._cache.get(rel)
            if cached and cached.get("mtime") == mtime:
                result[rel] = list(cached.get("symbols", []))
                continue

            try:
                source = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            symbols = _extract_symbols(source)
            result[rel] = symbols
            self._cache[rel] = {"mtime": mtime, "symbols": symbols}

        for stale in set(self._cache.keys()) - live_keys:
            self._cache.pop(stale, None)

        self.save_cache()
        dt = time.monotonic() - t0
        logger.info("repomap: %d arquivos indexados em %.2fs", len(result), dt)
        return result

    def invalidate(self, path: str | Path) -> None:
        """Marca um arquivo como stale. Próximo build reindexa só ele."""
        try:
            p = Path(path).resolve()
            rel = str(p.relative_to(self._root))
        except (OSError, ValueError):
            return
        self._cache.pop(rel, None)

    def render(
        self,
        budget_bytes: int = DEFAULT_BUDGET_BYTES,
        touched: set[str] | None = None,
    ) -> str:
        """Renderiza mapa compacto respeitando orçamento de bytes."""
        symbols_by_path = (
            self.build() if not self._cache else {k: list(v.get("symbols", [])) for k, v in self._cache.items()}
        )
        touched = touched or set()

        ordered = sorted(
            symbols_by_path.items(),
            key=lambda item: (_priority(item[0], touched), item[0]),
        )

        lines: list[str] = []
        total = 0
        omitted = 0
        for rel, symbols in ordered:
            if not symbols:
                continue
            line = f"{rel}: " + "; ".join(symbols)
            candidate = len(line) + 1
            if total + candidate > budget_bytes:
                omitted = len(ordered) - len(lines)
                break
            lines.append(line)
            total += candidate

        if omitted > 0:
            tail = f"... {omitted} arquivos omitidos"
            if total + len(tail) + 1 <= budget_bytes + 80:
                lines.append(tail)
        return "\n".join(lines)


# "Um mapa não é o território." -- Alfred Korzybski
