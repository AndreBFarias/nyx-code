"""Rich Output -- Renderização formatada para o Nyx Agent.

Port de Luna src/skills/code_agent/rich_output.py.
Cores vêm de nyx.themes.design_tokens (fonte única, ADR-023).
Fallback: se Rich não estiver instalado, funciona com ANSI puro.
"""

from __future__ import annotations

import os
import re
import sys

from nyx.agent.services.logging_service import get_logger
from nyx.themes.design_tokens import (
    ANSI_ACCENT_FG,
    ANSI_DIM,
    ANSI_ERROR_FG,
    ANSI_MUTED_FG,
    ANSI_RESET,
    BOX_CHARS,
    BULLETS,
    NYX_ACCENT,
    SPINNER_FRAMES,
)

logger = get_logger("nyx.output")

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

TAG_STYLES: dict[str, str] = {
    "nyx": f"bold {NYX_ACCENT}",
    "ok": "bold green",
    "erro": "bold red",
    "aviso": "yellow",
    "tool": f"bold {NYX_ACCENT}",
    "skip": "dim",
    "sessão": f"bold {NYX_ACCENT}",
    "métricas": f"dim {NYX_ACCENT}",
    "contexto": "dim yellow",
}

TAG_LABELS: dict[str, str] = {
    "nyx": "nyx",
    "ok": "ok",
    "erro": "ERRO",
    "aviso": "aviso",
    "tool": "tool",
    "skip": "skip",
    "sessão": "sessão",
    "métricas": "métricas",
    "contexto": "ctx",
}

EXT_LANG_MAP: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".sh": "bash",
    ".md": "markdown",
    ".html": "html",
    ".css": "css",
    ".sql": "sql",
    ".rs": "rust",
    ".go": "go",
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

        nyx_theme = Theme(
            {
                "tag.nyx": f"bold {NYX_ACCENT}",
                "tag.ok": "bold green",
                "tag.erro": "bold red",
                "tag.aviso": "yellow",
                "diff.added": "green",
                "diff.removed": "red",
                "diff.header": f"bold {NYX_ACCENT}",
            }
        )
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

        if tag == "sessão":
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
                Panel(
                    table,
                    title=f"[bold {NYX_ACCENT}]sessão[/bold {NYX_ACCENT}]",
                    border_style=f"dim {NYX_ACCENT}",
                    expand=False,
                )
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


_SPINNER_ASCII: tuple[str, ...] = ("|", "/", "-", "\\")


def _spinner_frames() -> tuple[str, ...]:
    """Retorna frames Braille em locale UTF-8, ASCII caso contrário.

    Inspeciona LC_ALL + LANG em uppercase. Qualquer forma (UTF-8, UTF8,
    utf-8, utf8) ativa Braille. LANG=C ou outros locales legacy caem
    para ASCII |/-\\.
    """
    import os

    raw = (os.environ.get("LC_ALL", "") + os.environ.get("LANG", "")).upper()
    if "UTF-8" in raw or "UTF8" in raw:
        return SPINNER_FRAMES
    return _SPINNER_ASCII


class NyxSpinner:
    """Spinner com frames de SPINNER_FRAMES (Braille UTF-8) ou ASCII (ADR-023).

    Thread daemon rotaciona frames a cada 80ms. Escolha UTF-8 vs ASCII
    feita uma vez no start via _spinner_frames() (leitura de LC_ALL+LANG).
    Ao parar, emite ``\\r\\x1b[2K`` para limpar a linha antes que on_token
    escreva. Idempotente: ``stop()`` duplicado é no-op.
    """

    FRAME_INTERVAL_S = 0.08

    def __init__(self, message: str = "pensando...") -> None:
        import threading

        self._message = message
        self._stop_evt = threading.Event()
        self._thread: threading.Thread | None = None
        self._stopped = False

    def __enter__(self) -> NyxSpinner:
        import sys
        import threading

        frames = _spinner_frames()

        def _loop() -> None:
            idx = 0
            while not self._stop_evt.is_set():
                frame = frames[idx % len(frames)]
                sys.stdout.write(
                    f"\r  {ANSI_ACCENT_FG}{frame}{ANSI_RESET}  {ANSI_DIM}{self._message}{ANSI_RESET}"
                )
                sys.stdout.flush()
                idx += 1
                self._stop_evt.wait(self.FRAME_INTERVAL_S)

        self._thread = threading.Thread(target=_loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, *args: object) -> None:
        self.stop()

    def stop(self) -> None:
        """Idempotente. Limpa a linha do spinner com \\r\\x1b[2K."""
        if self._stopped:
            return
        self._stopped = True
        self._stop_evt.set()
        if self._thread is not None:
            self._thread.join(timeout=0.2)
        import sys

        sys.stdout.write("\r\x1b[2K")
        sys.stdout.flush()


def nyx_spinner(message: str = "pensando...") -> NyxSpinner:
    """Cria spinner Braille para uso como context manager."""
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
        except (ValueError, OSError) as e:
            logger.debug("shorten_path fallback para %s: %s", value, e)
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


def is_tool_error(text: str) -> bool:
    """Detecta se o output de uma tool é erro por prefixo conhecido."""
    if not text:
        return False
    return any(text.startswith(p) for p in _ERROR_PREFIXES)


def _format_duration(duration_ms: int) -> str:
    """Formata duração em ms ou s (>=1000ms)."""
    if duration_ms < 1000:
        return f"{duration_ms}ms"
    return f"{duration_ms / 1000:.1f}s"


def format_args_preview(args: dict, max_total: int = 100) -> str:
    """Formata dict de args como 'k=v · k=v' para exibição compacta."""
    if not args:
        return ""
    parts_list: list[str] = []
    for k, v in args.items():
        val = str(v)
        if len(val) > 40:
            val = val[:37] + "…"
        parts_list.append(f"{k}={val}")
        if sum(len(p) for p in parts_list) > max_total:
            break
    return " · ".join(parts_list)


def render_tool_card_start(
    name: str,
    args_preview: str,
    spinner_frame: str = "",
) -> None:
    """Abre card de tool em execução.

    Usado quando se quer mostrar progresso antes do resultado. Não todos
    os call-sites usam — tools rápidas (<200ms) podem ir direto ao end.
    """
    h = BOX_CHARS["h"]
    tl = BOX_CHARS["tl"]
    tr = BOX_CHARS["tr"]
    v = BOX_CHARS["v"]
    frame = f"{spinner_frame} " if spinner_frame else ""
    header = f" {frame}{name} "
    tail_pad = max(2, 66 - len(header) - len(" executando "))
    line1 = f"  {ANSI_ACCENT_FG}{tl}{h}{header}{h * tail_pad}{h} executando {h}{tr}{ANSI_RESET}"
    args_line = f"  {ANSI_ACCENT_FG}{v}{ANSI_RESET}  {ANSI_DIM}{args_preview}{ANSI_RESET}"
    print(line1)
    print(args_line)


def render_tool_card_end(
    name: str,
    duration_ms: int,
    summary_line: str,
    is_error: bool = False,
    extra_lines: list[str] | None = None,
) -> None:
    """Fecha card de tool com duração e primeira linha do resultado.

    Call-site principal (cli.py on_tool_result) chama sempre este — o
    card é de linha única quando o start não foi chamado (tool rápida).
    """
    h = BOX_CHARS["h"]
    tl = BOX_CHARS["tl"]
    tr = BOX_CHARS["tr"]
    bl = BOX_CHARS["bl"]
    br = BOX_CHARS["br"]
    v = BOX_CHARS["v"]
    border = ANSI_ERROR_FG if is_error else ANSI_ACCENT_FG
    label = "ERRO" if is_error else "ok"
    duration = _format_duration(duration_ms)

    header = f" {BULLETS['tool']} {name} "
    tail = f" {label} · {duration} "
    pad = max(2, 66 - len(header) - len(tail))
    top = f"  {border}{tl}{h}{header}{h * pad}{h}{tail}{h}{tr}{ANSI_RESET}"
    body_lines: list[str] = []
    if summary_line:
        body_lines.append(f"  {border}{v}{ANSI_RESET}  {summary_line[:110]}")
    for extra in extra_lines or []:
        body_lines.append(f"  {border}{v}{ANSI_RESET}  {ANSI_DIM}{extra[:110]}{ANSI_RESET}")
    if not body_lines:
        body_lines.append(f"  {border}{v}{ANSI_RESET}")
    bottom = f"  {border}{bl}{h * 70}{br}{ANSI_RESET}"

    print(top)
    for line in body_lines:
        print(line)
    print(bottom)


def make_ask_permission(state: dict) -> "callable":
    """Factory do callback on_permission. Respeita state['bypass'].

    Extraído de cli.py para manter o arquivo abaixo de 800 linhas
    (CLAUDE.md §6). Permanece aqui porque é render layer (ADR-024).
    """
    from nyx.themes.design_tokens import ANSI_BOLD

    def _ask(level: str, tool_name: str, args: dict) -> bool:
        if state.get("bypass"):
            logger.info("[bypass] auto-aprovado: %s", tool_name)
            print(
                f"  {ANSI_DIM}{BULLETS['bypass_on']} bypass · {tool_name} "
                f"auto-aprovado{ANSI_RESET}"
            )
            return True
        args_preview = str(args)[:80]
        level_label = {
            "confirm_once": "uma vez",
            "always_confirm": "sempre",
        }.get(level, level)
        try:
            resp = (
                input(
                    f"  {ANSI_ACCENT_FG}[permissão: {level_label}]{ANSI_RESET} "
                    f"Executar {ANSI_BOLD}{tool_name}{ANSI_RESET}"
                    f"({args_preview})? [S/n] "
                )
                .strip()
                .lower()
            )
            return resp in ("", "s", "sim", "y", "yes")
        except (EOFError, KeyboardInterrupt):
            return False

    return _ask


def render_compaction_event(
    level: int,
    tokens_removed: int,
    pct_before: float,
    pct_after: float,
) -> None:
    """Linha discreta informando compactação automática (OBSERVABILITY-01 hook).

    Formato: '  · compactação nível N: -Ktok (ctx B% → A%)' em muted.
    """
    before_pct = int(pct_before * 100) if pct_before <= 1 else int(pct_before)
    after_pct = int(pct_after * 100) if pct_after <= 1 else int(pct_after)
    print(
        f"  {ANSI_MUTED_FG}{BULLETS['note']} compactação nível {level}: "
        f"-{tokens_removed} tokens (ctx {before_pct}% → {after_pct}%){ANSI_RESET}"
    )


USER_INPUT_COLLAPSE_LINES = 8


def render_user_input(
    text: str,
    console_width: int | None = None,
    expanded: bool = False,
) -> None:
    """Imprime eco da mensagem do usuário num box '╭─ você ─╮'.

    Se o input tem mais de USER_INPUT_COLLAPSE_LINES linhas (paste longo)
    e ``expanded=False`` (default), colapsa para a primeira linha seguida
    de hint explicando Ctrl+O para expandir. Limiar é estritamente maior
    (> 8): paste com exatamente 8 linhas renderiza integralmente.

    Fallback pra '> texto' se terminal <80 cols ou sem suporte a Rich.
    """
    import shutil

    if console_width is None:
        console_width = shutil.get_terminal_size(fallback=(80, 24)).columns

    lines = text.splitlines() or [text]
    if not expanded and len(lines) > USER_INPUT_COLLAPSE_LINES:
        hidden = len(lines) - 1
        display_text = (
            f"{lines[0]}\n"
            f"... [{hidden} linhas ocultas -- Ctrl+O para expandir]"
        )
    else:
        display_text = text

    if console_width < 80 or not RICH_AVAILABLE:
        print()
        for line in display_text.splitlines() or [display_text]:
            print(f"  {ANSI_ACCENT_FG}>{ANSI_RESET} {line}")
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
    from nyx.themes.design_tokens import ANSI_BOLD

    print(f"\n  {ANSI_ACCENT_FG}{ANSI_BOLD}Nyx{ANSI_RESET}")
    print(f"  {ANSI_ACCENT_FG}───{ANSI_RESET}")


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
    if width >= 80:
        body = f"ctx {pct}% · {model} · iter {iteration} · lidos {reads} · modif {mods}"
        padding = max(width - len(body) - 8, 3)
        line = f"── {body} " + "─" * padding
    elif width >= 60:
        body = f"ctx {pct}% · {model} · iter {iteration}"
        padding = max(width - len(body) - 5, 2)
        line = f"── {body} " + "─" * padding
    else:
        line = f"ctx {pct}%"
    print(f"{ANSI_DIM}{ANSI_ACCENT_FG}{line}{ANSI_RESET}")


def render_diff(old: str, new: str, path: str = "") -> str:
    """Gera diff formatado entre duas strings."""
    import difflib

    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=path, tofile=path)
    return "".join(diff)


def _fallback_output(tag: str, message: str) -> None:
    """Fallback ANSI puro quando Rich não está disponível."""
    label = TAG_LABELS.get(tag, tag)
    print(f"  {ANSI_ACCENT_FG}[{label}]{ANSI_RESET} {message}")


def print_error(
    msg: str,
    hint: str | None = None,
    debug_detail: str | None = None,
) -> None:
    """Imprime mensagem de erro canônica do REPL (ERROR-MSG-01).

    Contrato:
      - Prefixo ``[erro]`` em vermelho (ANSI_ERROR_FG) via design_tokens.
      - Corpo da mensagem em PT-BR, cor padrão do terminal.
      - ``hint`` (opcional) em ANSI_DIM -- verbo imperativo acionável.
      - ``debug_detail`` (opcional) só aparece se ``NYX_DEBUG=1`` -- tipo e
        linha da exceção subjacente, para troubleshooting sem poluir o UX.

    Formato renderizado:
      ``[erro] <mensagem>. <hint em dim>``
      ``  detalhe: <debug_detail>``   (somente com NYX_DEBUG=1)
    """
    prefix = f"{ANSI_ERROR_FG}[erro]{ANSI_RESET}"
    body = f"  {prefix} {msg}"
    if hint:
        body += f" {ANSI_DIM}{hint}{ANSI_RESET}"
    sys.stdout.write(body + "\n")
    if debug_detail and os.environ.get("NYX_DEBUG") == "1":
        sys.stdout.write(f"  {ANSI_DIM}detalhe: {debug_detail}{ANSI_RESET}\n")
    sys.stdout.flush()


def render_ask_user(question: str, options: list[dict[str, str]] | None = None) -> None:
    """Renderiza pergunta do agent ao usuário, com opções numeradas se existirem."""
    print()
    print(f"  {ANSI_ACCENT_FG}[pergunta]{ANSI_RESET} {question}")
    for i, opt in enumerate(options or [], 1):
        label = opt.get("label", "")
        desc = opt.get("description", "")
        if desc:
            print(f"    {ANSI_ACCENT_FG}{i}.{ANSI_RESET} {label} {ANSI_DIM}-- {desc}{ANSI_RESET}")
        else:
            print(f"    {ANSI_ACCENT_FG}{i}.{ANSI_RESET} {label}")
    print()


# "A forma segue a função." -- Louis Sullivan
