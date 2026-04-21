"""NyxCompleter -- Tab completion para o REPL.

Context-aware:
- Após '/' -> completa commands
- Senão -> completa paths de arquivo
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.completer")

try:
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.document import Document

    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

    class Completer:  # type: ignore[no-redef]
        pass

    class Completion:  # type: ignore[no-redef]
        pass

    class Document:  # type: ignore[no-redef]
        pass


class NyxCompleter(Completer):
    """Completer context-aware: commands, tools e paths."""

    def __init__(self, project_root: str, commands: list[dict] | None = None, tools: list[str] | None = None) -> None:
        self._root = Path(project_root)
        self._commands = commands or []
        self._tools = tools or []

    def get_completions(self, document: Any, complete_event: Any) -> Any:
        text = document.text_before_cursor
        word = document.get_word_before_cursor(WORD=True)

        if text.lstrip().startswith("/"):
            yield from self._complete_commands(word)
        else:
            yield from self._complete_paths(word)

    def _complete_commands(self, word: str) -> Any:
        prefix = word.lstrip("/").lower()
        matched: list[dict] = []
        for cmd in self._commands:
            name = cmd.get("name", "")
            if name.startswith(prefix):
                matched.append(cmd)
        # Ordena por (categoria, nome) para que o popup agrupe visualmente.
        matched.sort(key=lambda c: (c.get("category", "geral"), c.get("name", "")))
        for cmd in matched:
            name = cmd.get("name", "")
            desc = cmd.get("description", "")
            cat = cmd.get("category", "geral")
            aliases = cmd.get("aliases", []) or []
            alias_str = (
                f" ({', '.join('/' + a for a in aliases)})" if aliases else ""
            )
            display_meta_text = f"[{cat}] {desc}{alias_str}"[:60]
            yield Completion(
                f"/{name}",
                start_position=-len(word),
                display_meta=display_meta_text,
            )

    def _complete_paths(self, word: str) -> Any:
        if not word:
            return

        try:
            base = self._root / word
            parent = base.parent if not base.is_dir() else base
            pattern = base.name + "*" if not base.is_dir() else "*"

            if not parent.exists():
                return

            for path in sorted(parent.glob(pattern))[:20]:
                if path.name.startswith("."):
                    continue
                rel = str(path.relative_to(self._root))
                suffix = "/" if path.is_dir() else ""
                yield Completion(
                    rel + suffix,
                    start_position=-len(word),
                    display_meta="dir" if path.is_dir() else path.suffix,
                )
        except Exception as e:
            logger.debug("Erro no completer de paths: %s", e)
            return

    def update_commands(self, commands: list[dict]) -> None:
        self._commands = commands

    def update_tools(self, tools: list[str]) -> None:
        self._tools = tools


def create_completer(project_root: str) -> NyxCompleter | None:
    """Cria completer se prompt_toolkit disponível."""
    if not HAS_PROMPT_TOOLKIT:
        return None

    from nyx.agent.commands import list_commands

    cmds = [
        {
            "name": c.name,
            "description": c.description,
            "category": c.category,
            "aliases": list(c.aliases),
        }
        for c in list_commands()
    ]

    return NyxCompleter(project_root, commands=cmds)


# "A boa ferramenta antecipa a necessidade." -- Miyamoto Musashi
