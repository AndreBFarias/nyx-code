"""Path Resolver -- Resolução de caminhos relativos + índice de arquivos.

Port de Luna src/skills/code_agent/path_resolver.py.
Constrói índice do projeto e resolve caminhos por basename ou fuzzy match.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.path_resolver")

INDEXED_EXTENSIONS = {
    ".py",
    ".js",
    ".ts",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".cfg",
    ".txt",
    ".md",
    ".sh",
    ".css",
    ".html",
}

BLACKLIST_DIRS = {
    "__pycache__",
    ".git",
    "node_modules",
    ".venv",
    "venv",
    "logs",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "legacy",
    "dist",
    "models",
}

_PATH_REGEX = re.compile(
    r"((?:src|tests|scripts|app|lib|utils|config|nyx|docs)[\w/]*\.\w+|"
    r"[\w./]+\.(?:py|js|ts|json|yaml|yml|toml|cfg|txt|md|sh|css|html))",
)


@dataclass
class ResolvedPath:
    mention: str
    resolved: str | None
    candidates: list[str] = field(default_factory=list)
    exists: bool = False


class PathResolver:
    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._basename_index: dict[str, list[str]] = {}
        self._all_dirs: set[str] = set()

    def build_index(self) -> None:
        self._basename_index.clear()
        self._all_dirs.clear()

        for path in self._root.rglob("*"):
            rel = path.relative_to(self._root)
            parts = rel.parts
            if any(p in BLACKLIST_DIRS for p in parts):
                continue

            if path.is_dir():
                self._all_dirs.add(str(rel))
                continue

            if path.suffix not in INDEXED_EXTENSIONS:
                continue

            basename = path.name
            rel_str = str(rel)
            if basename not in self._basename_index:
                self._basename_index[basename] = []
            self._basename_index[basename].append(rel_str)

        total = sum(len(v) for v in self._basename_index.values())
        logger.debug("[PATH] Indexados %d arquivos, %d dirs", total, len(self._all_dirs))

    def resolve(self, mention: str) -> ResolvedPath:
        mention = mention.strip().strip("'\"")
        if "/" in mention:
            return self._resolve_full_path(mention)
        return self._resolve_basename(mention)

    def resolve_all(self, request: str) -> list[ResolvedPath]:
        mentions = _PATH_REGEX.findall(request)
        if not mentions:
            return []
        seen: set[str] = set()
        results: list[ResolvedPath] = []
        for mention in mentions:
            if mention in seen:
                continue
            seen.add(mention)
            results.append(self.resolve(mention))
        return results

    def get_project_summary(self, max_chars: int = 800) -> str:
        dir_files: dict[str, list[str]] = {}
        for basename, paths in self._basename_index.items():
            for rel_path in paths:
                parent = str(Path(rel_path).parent)
                if parent == ".":
                    parent = "."
                dir_files.setdefault(parent, []).append(basename)

        lines: list[str] = []
        root_files = sorted(dir_files.pop(".", []))

        for dir_path in sorted(dir_files.keys()):
            files = sorted(dir_files[dir_path])
            ext_counts: dict[str, int] = {}
            for f in files:
                ext = Path(f).suffix or "other"
                ext_counts[ext] = ext_counts.get(ext, 0) + 1
            ext_summary = ", ".join(f"{c} {e}" for e, c in sorted(ext_counts.items(), key=lambda x: -x[1]))
            lines.append(f"{dir_path}/ ({ext_summary})")

        if root_files:
            lines.append(", ".join(root_files))

        result = "\n".join(lines)
        if len(result) > max_chars:
            result = result[: max_chars - 20] + "\n[... truncado]"
        return result

    def _resolve_full_path(self, mention: str) -> ResolvedPath:
        full = self._root / mention
        if full.exists():
            return ResolvedPath(mention=mention, resolved=mention, exists=True)
        basename = Path(mention).name
        return self._resolve_basename(basename, original_mention=mention)

    def _resolve_basename(self, basename: str, original_mention: str | None = None) -> ResolvedPath:
        mention = original_mention or basename
        candidates = self._basename_index.get(basename, [])

        if len(candidates) == 1:
            return ResolvedPath(mention=mention, resolved=candidates[0], candidates=candidates, exists=True)
        if len(candidates) > 1:
            return ResolvedPath(mention=mention, resolved=None, candidates=candidates, exists=True)

        # Fuzzy: mesmo stem, extensão diferente
        stem = Path(basename).stem
        if stem and "." not in stem:
            fuzzy: list[str] = []
            for key, paths in self._basename_index.items():
                if Path(key).stem == stem:
                    fuzzy.extend(paths)
            if len(fuzzy) == 1:
                return ResolvedPath(mention=mention, resolved=fuzzy[0], candidates=fuzzy, exists=True)
            if fuzzy:
                return ResolvedPath(mention=mention, resolved=None, candidates=fuzzy, exists=True)

        if basename in self._all_dirs:
            return ResolvedPath(mention=mention, resolved=basename, exists=True)

        return ResolvedPath(mention=mention, resolved=None, exists=False)


# "Quem não sabe para onde vai, qualquer caminho serve." -- Lewis Carroll
