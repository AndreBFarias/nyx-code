"""NyxMemory -- memória persistente cross-session em ~/.nyx/memory/<project>/.

Cada projeto tem seu diretório isolado (slug derivado do path para evitar
colisão entre projetos com mesmo nome). Arquivos são markdown simples, um
por "memória". MEMORY.md mantém índice gerado automaticamente.
"""

from __future__ import annotations

import hashlib
import logging
import re
from pathlib import Path

logger = logging.getLogger("nyx.memory")

MEMORY_ROOT = Path.home() / ".nyx" / "memory"
MAX_FILE_BYTES = 4096
MAX_BUNDLE_BYTES = 8192
INDEX_NAME = "MEMORY.md"

_SAFE_FILENAME = re.compile(r"[^a-zA-Z0-9_\-]+")


def _slug_project(project_root: str) -> str:
    """Slug determinístico: nome + hash curto do path para isolamento."""
    p = Path(project_root).resolve()
    digest = hashlib.sha1(str(p).encode("utf-8")).hexdigest()[:8]
    name = _SAFE_FILENAME.sub("-", p.name).strip("-") or "project"
    return f"{name}-{digest}"


def _sanitize_filename(name: str) -> str:
    """Remove caracteres perigosos e força extensão .md."""
    stem = Path(name).stem
    safe = _SAFE_FILENAME.sub("_", stem).strip("_")
    if not safe:
        safe = "memoria"
    return f"{safe}.md"


class NyxMemory:
    """Gestor de memória persistente por projeto."""

    def __init__(self, project_root: str) -> None:
        self._project_root = project_root
        self._slug = _slug_project(project_root)
        self._dir = MEMORY_ROOT / self._slug

    @property
    def directory(self) -> Path:
        return self._dir

    def load(self) -> str:
        """Concatena todas as memórias .md em um único bundle (cap 8KB)."""
        if not self._dir.exists():
            return ""

        parts: list[str] = []
        total = 0
        files = sorted(p for p in self._dir.glob("*.md") if p.name != INDEX_NAME)
        for path in files:
            try:
                content = path.read_text(encoding="utf-8", errors="replace").strip()
            except OSError as e:
                logger.warning("Falha ao ler memória %s: %s", path, e)
                continue
            if not content:
                continue
            block = f"--- {path.name} ---\n{content}\n"
            if total + len(block) > MAX_BUNDLE_BYTES:
                remaining = MAX_BUNDLE_BYTES - total
                if remaining > 100:
                    parts.append(block[:remaining] + "\n[... truncado]")
                parts.append(f"[... {len(files) - len(parts)} memórias omitidas]")
                break
            parts.append(block)
            total += len(block)
        return "\n".join(parts)

    def write(self, file: str, content: str, reason: str) -> Path:
        """Grava uma memória. Valida tamanho, sanitiza nome, atualiza índice."""
        if not content or not content.strip():
            raise ValueError("Conteúdo vazio")
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise ValueError(
                f"Conteúdo excede {MAX_FILE_BYTES} bytes "
                f"(enviado: {len(content.encode('utf-8'))})"
            )

        self._dir.mkdir(parents=True, exist_ok=True)
        filename = _sanitize_filename(file)
        target = self._dir / filename

        header = f"<!-- reason: {reason.strip()[:200]} -->\n"
        target.write_text(header + content.strip() + "\n", encoding="utf-8")
        self._rebuild_index()
        logger.info("Memória gravada: %s", target)
        return target

    def index(self) -> list[dict[str, str]]:
        """Lê MEMORY.md e devolve entradas como lista de dicts."""
        idx = self._dir / INDEX_NAME
        if not idx.exists():
            return []
        entries: list[dict[str, str]] = []
        for line in idx.read_text(encoding="utf-8", errors="replace").splitlines():
            m = re.match(r"- \[(?P<file>[^\]]+)\]\((?P<href>[^)]+)\)(?: -- (?P<reason>.*))?$", line)
            if m:
                entries.append({
                    "file": m.group("file"),
                    "href": m.group("href"),
                    "reason": m.group("reason") or "",
                })
        return entries

    def _rebuild_index(self) -> None:
        """Reescreve MEMORY.md baseado nos arquivos existentes."""
        if not self._dir.exists():
            return
        lines = ["# Memória -- " + Path(self._project_root).name, ""]
        files = sorted(p for p in self._dir.glob("*.md") if p.name != INDEX_NAME)
        for path in files:
            reason = ""
            try:
                first = path.read_text(encoding="utf-8", errors="replace").splitlines()[0]
                m = re.match(r"<!-- reason:\s*(.*?)\s*-->", first)
                if m:
                    reason = m.group(1)
            except OSError:
                pass
            entry = f"- [{path.stem}]({path.name})"
            if reason:
                entry += f" -- {reason}"
            lines.append(entry)
        (self._dir / INDEX_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")


# "A memória é a guardiã de todas as coisas." -- Cícero
