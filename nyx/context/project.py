"""ProjectContext -- Detecta tipo de projeto automaticamente."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("nyx.context.project")

MARKERS = {
    "pyproject.toml": ("Python", ""),
    "setup.py": ("Python", ""),
    "requirements.txt": ("Python", ""),
    "Pipfile": ("Python", "pipenv"),
    "package.json": ("JavaScript/TypeScript", ""),
    "tsconfig.json": ("TypeScript", ""),
    "Cargo.toml": ("Rust", ""),
    "go.mod": ("Go", ""),
    "pom.xml": ("Java", "maven"),
    "build.gradle": ("Java/Kotlin", "gradle"),
    "Gemfile": ("Ruby", "bundler"),
    "composer.json": ("PHP", "composer"),
    "Makefile": ("C/C++", "make"),
    "CMakeLists.txt": ("C/C++", "cmake"),
}

FRAMEWORK_MARKERS = {
    "next.config.js": "Next.js",
    "next.config.ts": "Next.js",
    "nuxt.config.ts": "Nuxt",
    "angular.json": "Angular",
    "svelte.config.js": "Svelte",
    "manage.py": "Django",
    "app.py": "Flask/FastAPI",
    "Dockerfile": "Docker",
    "docker-compose.yml": "Docker Compose",
}


@dataclass
class ProjectInfo:
    language: str = "desconhecido"
    framework: str = ""
    build_tool: str = ""
    entry_points: list[str] = field(default_factory=list)
    structure: dict[str, int] = field(default_factory=dict)


def detect(project_root: str | Path) -> ProjectInfo:
    """Detecta tipo de projeto pelo conteúdo do diretório raiz."""
    root = Path(project_root)
    info = ProjectInfo()

    for marker, (lang, tool) in MARKERS.items():
        if (root / marker).exists():
            info.language = lang
            if tool:
                info.build_tool = tool
            break

    for marker, framework in FRAMEWORK_MARKERS.items():
        if (root / marker).exists():
            info.framework = framework
            break

    common_entries = ["main.py", "app.py", "index.ts", "index.js", "main.go", "main.rs", "src/main.py"]
    for entry in common_entries:
        if (root / entry).exists():
            info.entry_points.append(entry)

    ext_counts: dict[str, int] = {}
    try:
        for f in root.rglob("*"):
            if f.is_file() and not any(p.startswith(".") for p in f.parts):
                ext = f.suffix.lower()
                if ext:
                    ext_counts[ext] = ext_counts.get(ext, 0) + 1
    except PermissionError:
        pass

    info.structure = dict(sorted(ext_counts.items(), key=lambda x: -x[1])[:10])

    logger.info("Projeto detectado: %s %s", info.language, info.framework)
    return info


def format_context(info: ProjectInfo) -> str:
    """Formata para injeção no system prompt."""
    parts = [f"Linguagem: {info.language}"]
    if info.framework:
        parts.append(f"Framework: {info.framework}")
    if info.build_tool:
        parts.append(f"Build: {info.build_tool}")
    if info.entry_points:
        parts.append(f"Entry points: {', '.join(info.entry_points)}")
    return " | ".join(parts)


# "Contexto é tudo." -- Wittgenstein
