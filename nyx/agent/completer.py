"""NyxCompleter -- Tab completion para o REPL.

Context-aware:
- Após '/' sem espaço -> completa nome do command (com headers por categoria).
- Após '/<cmd> '       -> completa argumento via provedor por command.
- Senão -> completa paths de arquivo.

Provedores de argumento (dispatch por nome do command):
- /model <prefix>          -> modelos instalados (HTTP /api/tags, cache TTL 30s)
- /theme <prefix>          -> temas do ThemeManager (cache TTL 30s)
- /session load <prefix>   -> sessões em ~/.nyx/sessions/session_*.json
- /session resume <prefix> -> idem (alias semântico)
- /session restore <prefix>-> idem (alias semântico)
- /recall <prefix>         -> nomes de memórias indexadas em MEMORY.md (NyxMemory)

Fonte canônica em todos os casos. Sem listas hardcoded. Sem shell-out.
Timeouts curtos + fallback gracioso para não bloquear o prompt.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import OLLAMA_URL as _OLLAMA_URL

logger = get_logger("nyx.completer")

try:
    from prompt_toolkit.completion import Completer, Completion
    from prompt_toolkit.document import Document
    from prompt_toolkit.formatted_text import FormattedText

    HAS_PROMPT_TOOLKIT = True
except ImportError:
    HAS_PROMPT_TOOLKIT = False

    class Completer:  # type: ignore[no-redef]
        pass

    class Completion:  # type: ignore[no-redef]
        pass

    class Document:  # type: ignore[no-redef]
        pass

    class FormattedText(list):  # type: ignore[no-redef]
        pass


_MAX_ARG_RESULTS = 50
_CACHE_TTL_SECONDS = 30.0
_HTTP_TIMEOUT_SECONDS = 2.0
_SESSIONS_DIR = Path.home() / ".nyx" / "sessions"


class NyxCompleter(Completer):
    """Completer context-aware: commands, args de slash, e paths."""

    def __init__(
        self,
        project_root: str,
        commands: list[dict] | None = None,
        tools: list[str] | None = None,
    ) -> None:
        self._root = Path(project_root)
        self._commands = commands or []
        self._tools = tools or []

        # Caches por provedor (TTL 30s, monotonic). Conteúdo: tuple[ts, value].
        self._models_cache: list[str] = []
        self._models_cached_at: float = 0.0
        self._themes_cache: list[str] = []
        self._themes_cached_at: float = 0.0
        self._memories_cache: list[str] = []
        self._memories_cached_at: float = 0.0

        # Dispatch por nome do comando (chave = name registrado no nyx_command).
        self._arg_providers: dict[str, Callable[[str], list[str]]] = {
            "model": self._list_models,
            "m": self._list_models,  # alias
            "theme": self._list_themes,
            "session": self._list_sessions_for_subcmd,
            "sess": self._list_sessions_for_subcmd,  # alias
            "resume": self._list_sessions_direct,
            "replay": self._list_sessions_direct,
            "recall": self._list_memories,
            "rec": self._list_memories,  # alias
        }

    def get_completions(self, document: Any, complete_event: Any) -> Any:
        text = document.text_before_cursor
        word = document.get_word_before_cursor(WORD=True)

        if not text.lstrip().startswith("/"):
            yield from self._complete_paths(word)
            return

        body = text.lstrip()[1:]  # remove o '/'
        if " " not in body:
            # Ainda digitando nome do comando -- preserva UX-BUG-01 + COMPLETER-SEPS-01.
            yield from self._complete_commands(word)
            return

        cmd_name, _, arg_part = body.partition(" ")
        provider = self._arg_providers.get(cmd_name.lower())
        if provider is None:
            return
        try:
            sugestoes = provider(arg_part)
        except Exception as exc:
            logger.warning("Provedor de args /%s falhou: %s", cmd_name, exc)
            return

        # arg_token: prefixo que o usuário está digitando agora (último whitespace).
        arg_token = arg_part.rsplit(" ", 1)[-1] if arg_part else ""
        for sug in sugestoes[:_MAX_ARG_RESULTS]:
            yield Completion(
                sug,
                start_position=-len(arg_token),
                display_meta=f"[arg /{cmd_name}]"[:60],
            )

    def _complete_commands(self, word: str) -> Any:
        prefix = word.lstrip("/").lower()
        matched: list[dict] = []
        for cmd in self._commands:
            name = cmd.get("name", "")
            if name.startswith(prefix):
                matched.append(cmd)
        # Ordena por (categoria, nome) para que o popup agrupe visualmente.
        matched.sort(key=lambda c: (c.get("category", "geral"), c.get("name", "")))

        last_cat: str | None = None
        for cmd in matched:
            name = cmd.get("name", "")
            desc = cmd.get("description", "")
            cat = cmd.get("category", "geral")
            aliases = cmd.get("aliases", []) or []

            # Separador de categoria -- só quando cat muda e há comando real a seguir.
            # Como o loop só emite header antes de um comando real do grupo,
            # cabeçalhos órfãos são impossíveis por construção.
            if cat != last_cat:
                header = FormattedText(
                    [("class:completion.header", f"---- [{cat}] ----")]
                )
                yield Completion(
                    text="",
                    start_position=0,
                    display=header,
                    display_meta="",
                )
                last_cat = cat

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

    # ─── Provedores de argumento ────────────────────────────────────────

    def _list_models(self, arg_part: str) -> list[str]:
        prefix = arg_part.strip()
        models = self._cached_models()
        return [m for m in models if m.startswith(prefix)]

    def _list_themes(self, arg_part: str) -> list[str]:
        prefix = arg_part.strip()
        themes = self._cached_themes()
        return [t for t in themes if t.startswith(prefix)]

    def _list_sessions_for_subcmd(self, arg_part: str) -> list[str]:
        # '/session <sub> <prefix>' -- só sugere arg quando sub é load/resume/restore.
        sub, _, sub_prefix = arg_part.partition(" ")
        sub = sub.strip().lower()
        if sub in ("load", "resume", "restore"):
            return self._list_session_files(sub_prefix.strip())
        if sub in ("", "list", "save"):
            # Sugerir subcomandos quando o usuário ainda não escolheu um.
            return [s for s in ("list", "save", "load", "resume") if s.startswith(sub)]
        return []

    def _list_sessions_direct(self, arg_part: str) -> list[str]:
        # /resume <prefix> e /replay <session_id> aceitam o id diretamente.
        return self._list_session_files(arg_part.strip())

    def _list_session_files(self, prefix: str) -> list[str]:
        # Filtro por substring (case-insensitive) -- o id real é
        # 'session_<projeto>_<epoch>', então o usuário tipicamente digita
        # parte do epoch (ano, mês) ou parte do projeto. Substring é o
        # comportamento útil; ordem por mtime desc (sessões recentes
        # primeiro). Cap em _MAX_ARG_RESULTS via caller.
        if not _SESSIONS_DIR.exists():
            return []
        try:
            files = sorted(
                _SESSIONS_DIR.glob("session_*.json"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        except OSError as exc:
            logger.warning("Falha ao listar sessões em %s: %s", _SESSIONS_DIR, exc)
            return []
        nomes = [p.stem for p in files]
        if not prefix:
            return nomes
        prefix_lower = prefix.lower()
        return [n for n in nomes if prefix_lower in n.lower()]

    def _list_memories(self, arg_part: str) -> list[str]:
        prefix = arg_part.strip()
        memorias = self._cached_memories()
        if not prefix:
            return memorias
        return [m for m in memorias if m.startswith(prefix)]

    # ─── Caches com TTL ─────────────────────────────────────────────────

    def _cached_models(self) -> list[str]:
        now = time.monotonic()
        if now - self._models_cached_at < _CACHE_TTL_SECONDS and self._models_cache:
            return self._models_cache
        try:
            import httpx

            resp = httpx.get(f"{_OLLAMA_URL}/api/tags", timeout=_HTTP_TIMEOUT_SECONDS)
            resp.raise_for_status()
            data = resp.json() or {}
        except Exception as exc:
            # Inclui httpx.TimeoutException, ConnectError, JSONDecodeError, ImportError.
            logger.warning(
                "Ollama /api/tags falhou: %s -- mantendo cache (%d itens)",
                exc, len(self._models_cache),
            )
            return self._models_cache
        modelos = sorted(
            {str(m.get("name", "")).strip() for m in data.get("models", []) if m.get("name")}
        )
        self._models_cache = modelos
        self._models_cached_at = now
        return modelos

    def _cached_themes(self) -> list[str]:
        now = time.monotonic()
        if now - self._themes_cached_at < _CACHE_TTL_SECONDS and self._themes_cache:
            return self._themes_cache
        try:
            from nyx.themes import ThemeManager

            tm = ThemeManager()
            temas = sorted(
                {str(t.get("id", "")).strip() for t in tm.list_themes() if t.get("id")}
            )
        except Exception as exc:
            logger.warning(
                "ThemeManager.list_themes falhou: %s -- mantendo cache (%d itens)",
                exc, len(self._themes_cache),
            )
            return self._themes_cache
        self._themes_cache = temas
        self._themes_cached_at = now
        return temas

    def _cached_memories(self) -> list[str]:
        now = time.monotonic()
        if now - self._memories_cached_at < _CACHE_TTL_SECONDS and self._memories_cache:
            return self._memories_cache
        try:
            from nyx.agent.memory import NyxMemory

            mem = NyxMemory(str(self._root))
            entries = mem.index()
            nomes = sorted({e.get("file", "") for e in entries if e.get("file")})
        except Exception as exc:
            logger.warning(
                "NyxMemory.index falhou: %s -- mantendo cache (%d itens)",
                exc, len(self._memories_cache),
            )
            return self._memories_cache
        self._memories_cache = nomes
        self._memories_cached_at = now
        return nomes

    # ─── Updates externos ───────────────────────────────────────────────

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
