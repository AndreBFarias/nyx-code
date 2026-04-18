"""Rich Output -- Renderização formatada para o Nyx Agent.

Port de Luna src/skills/code_agent/rich_output.py.
Cores adaptadas para paleta Nyx (#00D4AA accent, #E8E8E8 primary).
Fallback: se Rich não estiver instalado, funciona com ANSI puro.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger("nyx.output")

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    from rich.theme import Theme

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

_DIFF_LINE_PATTERN = re.compile(r"^[+-@]")

# Cores Nyx
NYX_ACCENT = "#00D4AA"
NYX_PRIMARY = "#E8E8E8"
NYX_BG = "#2A2C39"

TAG_STYLES: dict[str, str] = {
    "nyx": f"bold {NYX_ACCENT}",
    "ok": "bold green",
    "erro": "bold red",
    "aviso": "yellow",
    "tool": f"bold {NYX_ACCENT}",
    "skip": "dim",
    "sessao": f"bold {NYX_ACCENT}",
    "metricas": f"dim {NYX_ACCENT}",
    "contexto": "dim yellow",
}

TAG_LABELS: dict[str, str] = {
    "nyx": "nyx",
    "ok": "ok",
    "erro": "ERRO",
    "aviso": "aviso",
    "tool": "tool",
    "skip": "skip",
    "sessao": "sessão",
    "metricas": "métricas",
    "contexto": "ctx",
}

EXT_LANG_MAP: dict[str, str] = {
    ".py": "python", ".js": "javascript", ".ts": "typescript",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".sh": "bash", ".md": "markdown",
    ".html": "html", ".css": "css", ".sql": "sql",
    ".rs": "rust", ".go": "go",
}


def _looks_like_diff(text: str) -> bool:
    lines = text.strip().splitlines()
    if len(lines) < 2:
        return False
    return sum(1 for line in lines if _DIFF_LINE_PATTERN.match(line)) >= 2


def _detect_language(path: str) -> str:
    for ext, lang in EXT_LANG_MAP.items():
        if path.endswith(ext):
            return lang
    return "text"


class RichOutput:
    def __init__(self, console: Console | None = None) -> None:
        if not RICH_AVAILABLE:
            self._console = None
            return

        nyx_theme = Theme({
            "tag.nyx": f"bold {NYX_ACCENT}",
            "tag.ok": "bold green",
            "tag.erro": "bold red",
            "tag.aviso": "yellow",
            "diff.added": "green",
            "diff.removed": "red",
            "diff.header": f"bold {NYX_ACCENT}",
        })
        self._console = console or Console(theme=nyx_theme, highlight=False)

    def __call__(self, tag: str, message: str) -> None:
        if not self._console:
            _fallback_output(tag, message)
            return
        try:
            self._render(tag, message)
        except Exception as e:
            logger.warning("Rich output falhou, usando fallback: %s", e)
            _fallback_output(tag, message)

    def _render(self, tag: str, message: str) -> None:
        assert self._console is not None

        if tag == "nyx":
            self._console.print()
            self._console.print(f"  [bold {NYX_ACCENT}]Nyx[/bold {NYX_ACCENT}]: {message}")
            self._console.print()
            return

        if tag == "sessao":
            self._render_session_summary(message)
            return

        if tag in ("ok", "tool") and _looks_like_diff(message):
            self._render_diff(message)
            return

        if tag == "code":
            self._render_code(message)
            return

        style = TAG_STYLES.get(tag, "")
        label = TAG_LABELS.get(tag, tag)
        self._console.print(f"  [{style}][{label}][/{style}] {message}")

    def _render_session_summary(self, message: str) -> None:
        assert self._console is not None
        self._console.print()
        parts = message.split(" | ")
        if len(parts) >= 3:
            table = Table(show_header=False, show_edge=False, padding=(0, 2), expand=False)
            table.add_column(style=NYX_ACCENT)
            table.add_column(style="white")
            for part in parts:
                kv = part.strip().split(": ", 1)
                if len(kv) == 2:
                    table.add_row(kv[0], kv[1])
                else:
                    table.add_row(part.strip(), "")
            self._console.print(
                Panel(table, title=f"[bold {NYX_ACCENT}]sessão[/bold {NYX_ACCENT}]",
                      border_style=f"dim {NYX_ACCENT}", expand=False)
            )
        else:
            self._console.print(f"  [bold {NYX_ACCENT}][sessão][/bold {NYX_ACCENT}] {message}")
        self._console.print()

    def _render_diff(self, diff_text: str) -> None:
        assert self._console is not None
        text = Text()
        for line in diff_text.strip().splitlines():
            if line.startswith("+++") or line.startswith("---"):
                text.append(line + "\n", style=f"bold {NYX_ACCENT}")
            elif line.startswith("@@"):
                text.append(line + "\n", style="bold cyan")
            elif line.startswith("+"):
                text.append(line + "\n", style="green")
            elif line.startswith("-"):
                text.append(line + "\n", style="red")
            else:
                text.append(line + "\n")
        self._console.print(Panel(text, border_style="dim", expand=False))

    def _render_code(self, message: str, path: str = "", lang: str = "") -> None:
        assert self._console is not None
        if not lang and path:
            lang = _detect_language(path)
        syntax = Syntax(message, lang or "text", theme="monokai", line_numbers=True)
        self._console.print(syntax)

    @property
    def available(self) -> bool:
        return self._console is not None


class NyxSpinner:
    """Context manager para spinner durante operações longas."""

    def __init__(self, message: str = "Pensando...") -> None:
        self._message = message
        self._spinner = None
        self._console = None

    def __enter__(self) -> NyxSpinner:
        if RICH_AVAILABLE:
            try:
                from rich.console import Console
                from rich.spinner import Spinner
                from rich.live import Live

                self._console = Console(highlight=False)
                spinner = Spinner("dots", text=f"  [dim]{self._message}[/dim]")
                self._live = Live(spinner, console=self._console, refresh_per_second=10)
                self._live.start()
            except Exception as e:
                logger.debug("Rich spinner falhou: %s", e)
                import sys
                sys.stdout.write(f"  {self._message}")
                sys.stdout.flush()
        else:
            import sys
            sys.stdout.write(f"  {self._message}")
            sys.stdout.flush()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()

    def stop(self) -> None:
        """Idempotente: para o spinner se ainda ativo."""
        if getattr(self, "_stopped", False):
            return
        self._stopped = True
        if hasattr(self, "_live"):
            try:
                self._live.stop()
            except Exception as e:
                logger.debug("Erro ao parar spinner: %s", e)
        elif not RICH_AVAILABLE:
            import sys
            sys.stdout.write("\r" + " " * 40 + "\r")
            sys.stdout.flush()


def nyx_spinner(message: str = "Pensando...") -> NyxSpinner:
    """Cria spinner para uso como context manager."""
    return NyxSpinner(message)


PRIMARY_ARG_KEYS = ("file_path", "pattern", "path", "command", "url", "query")


def _shorten_path(value: str, project_root: str | None, max_len: int) -> str:
    if project_root and "://" not in value:
        try:
            from pathlib import Path as _Path
            p = _Path(value).resolve()
            root = _Path(project_root).resolve()
            if p == root or root in p.parents:
                value = str(p.relative_to(root))
        except (ValueError, OSError):
            pass
    if len(value) <= max_len:
        return value
    head_len = max_len // 2 - 1
    tail_len = max_len - head_len - 1
    return f"{value[:head_len]}…{value[-tail_len:]}"


def format_tool_call(
    name: str,
    args: dict,
    project_root: str | None = None,
    max_width: int = 60,
) -> str:
    """Formata uma tool call compacta: 'name(arg)' sem dict cru."""
    if not args:
        return f"{name}()"
    primary_value: str | None = None
    for key in PRIMARY_ARG_KEYS:
        if key in args and args[key] not in (None, ""):
            primary_value = str(args[key])
            break
    if primary_value is None:
        first_val = next(iter(args.values()), "")
        primary_value = str(first_val)
    primary_value = _shorten_path(primary_value, project_root, max_width)
    return f"{name}({primary_value})"


def render_tool_call(
    name: str,
    args: dict,
    project_root: str | None = None,
) -> None:
    """Imprime tool call estilo Claude Code: '⏺ nome(arg)' em accent color."""
    formatted = format_tool_call(name, args, project_root=project_root)
    ACCENT_FG = "\033[38;2;0;212;170m"
    NC_FG = "\033[0m"
    print(f"  {ACCENT_FG}⏺{NC_FG} {formatted}")


_ERROR_PREFIXES = (
    "Fora do projeto",
    "Acesso negado",
    "Erro:",
    "ERRO:",
    "Falha",
    "Bloqueado",
    "Permissão negada",
    "Timeout",
    "Argumentos inválidos",
    "Path vazio",
    "Tool desconhecida",
)


def render_tool_result(result: str, max_chars: int = 110) -> None:
    """Imprime resumo colapsado do resultado de uma tool: '    └─ 1ª linha'.

    Erros (prefixos conhecidos) saem em âmbar; sucesso sai em dim.
    """
    if not result:
        return
    first_line = next(
        (line.strip() for line in result.splitlines() if line.strip()),
        "",
    )
    if not first_line:
        return
    if len(first_line) > max_chars:
        first_line = first_line[: max_chars - 1] + "…"
    NC_FG = "\033[0m"
    AMBER_FG = "\033[38;2;255;176;0m"
    DIM_FG = "\033[2m"
    is_error = any(first_line.startswith(p) for p in _ERROR_PREFIXES)
    color = AMBER_FG if is_error else DIM_FG
    print(f"    {color}└─ {first_line}{NC_FG}")


USER_INPUT_COLLAPSE_LINES = 8


def render_user_input(text: str, console_width: int | None = None) -> None:
    """Imprime eco da mensagem do usuário num box '╭─ você ─╮'.

    Se o input tem mais de USER_INPUT_COLLAPSE_LINES linhas (paste longo),
    colapsa pra 3 primeiras + contagem.

    Fallback pra '> texto' se terminal <80 cols ou sem suporte a Rich.
    """
    import shutil
    if console_width is None:
        console_width = shutil.get_terminal_size(fallback=(80, 24)).columns

    lines = text.splitlines() or [text]
    if len(lines) > USER_INPUT_COLLAPSE_LINES:
        head = "\n".join(lines[:3])
        display_text = f"{head}\n... [{len(lines) - 3} linhas ocultas do paste]"
    else:
        display_text = text

    if console_width < 80 or not RICH_AVAILABLE:
        ACCENT_FG = "\033[38;2;0;212;170m"
        NC_FG = "\033[0m"
        print()
        for line in display_text.splitlines() or [display_text]:
            print(f"  {ACCENT_FG}>{NC_FG} {line}")
        print()
        return
    try:
        console = Console(highlight=False)
        console.print()
        console.print(
            Panel(
                display_text,
                title="você",
                title_align="left",
                border_style=f"{NYX_ACCENT}",
                expand=False,
            )
        )
        console.print()
    except Exception as e:
        logger.debug("Rich user input render falhou: %s", e)


def render_assistant_start() -> None:
    """Imprime header 'Nyx\\n───' antes do streaming da resposta."""
    ACCENT_FG = "\033[38;2;0;212;170m"
    BOLD = "\033[1m"
    NC_FG = "\033[0m"
    print(f"\n  {ACCENT_FG}{BOLD}Nyx{NC_FG}")
    print(f"  {ACCENT_FG}───{NC_FG}")


def render_assistant_end() -> None:
    """Imprime linha em branco após fim da resposta do assistant."""
    print()


def render_footer(
    pct: int,
    model: str,
    iteration: int,
    reads: int,
    mods: int,
) -> None:
    """Imprime footer 1 linha acima do prompt: '── ctx X% ── modelo ── iter N ──'.

    Degradação por largura:
      ≥80 cols: completo (ctx, modelo, iter, lidos, modif)
      60-79:   'ctx X% · modelo · iter N'
      <60:     'ctx X%'
    """
    import shutil
    width = shutil.get_terminal_size(fallback=(80, 24)).columns
    ACCENT_FG = "\033[38;2;0;212;170m"
    DIM_FG = "\033[2m"
    NC_FG = "\033[0m"
    if width >= 80:
        body = (
            f"ctx {pct}% · {model} · iter {iteration} · "
            f"lidos {reads} · modif {mods}"
        )
        padding = max(width - len(body) - 8, 3)
        line = f"── {body} " + "─" * padding
    elif width >= 60:
        body = f"ctx {pct}% · {model} · iter {iteration}"
        padding = max(width - len(body) - 5, 2)
        line = f"── {body} " + "─" * padding
    else:
        line = f"ctx {pct}%"
    print(f"{DIM_FG}{ACCENT_FG}{line}{NC_FG}")


def render_diff(old: str, new: str, path: str = "") -> str:
    """Gera diff formatado entre duas strings."""
    import difflib
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=path, tofile=path)
    return "".join(diff)


def _fallback_output(tag: str, message: str) -> None:
    """Fallback ANSI puro quando Rich não está disponível."""
    ACCENT = "\033[38;2;0;212;170m"
    NC = "\033[0m"
    label = TAG_LABELS.get(tag, tag)
    print(f"  {ACCENT}[{label}]{NC} {message}")


# "A forma segue a função." -- Louis Sullivan
