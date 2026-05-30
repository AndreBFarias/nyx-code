"""Rich Output -- Renderização formatada para o Nyx Agent.

Port de Luna src/skills/code_agent/rich_output.py.
Cores vêm de nyx.themes.design_tokens (fonte única, ADR-023).
Fallback: se Rich não estiver instalado, funciona com ANSI puro.

Convenção boot vs sessão (TUI-REDESIGN-25-02):
  Boot (run.sh, log_boot, log_nyx) usa prefixo [nyx] -- diagnóstico,
  monológico. Sessão REPL usa Nyx standalone (render_assistant_start
  imprime "Nyx" sem brackets) -- diálogo. Catálogos canônicos vivem em
  design_tokens.py: GLYPHS_BOOT, GLYPHS_SESSAO, PREFIX_NYX. Aplicação
  fina dos glifos em cada bloco é responsabilidade das sprints 25-06
  até 25-14. Ver MICROCOPY.md seção "Vocabulário visual".
"""

from __future__ import annotations

import os
import re
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

from nyx.agent.services.logging_service import get_logger
from nyx.themes.design_tokens import (
    ANSI_DIM,
    ANSI_RESET,
    BOX_CHARS,
    BULLETS,
    SPINNER_FRAMES,
)
from nyx.themes.theme_manager import current_accent_hex, current_ansi

# VISUAL-LAYOUT-CLI-CONSUME-01: accent/muted/error resolvidos em import-time
# via theme_manager. Honra NYX_AESTHETIC + NYX_ENTITY do ambiente. Default
# (paleta D) preservado quando vars ausentes.
_ANSI = current_ansi()
ANSI_ACCENT_FG = _ANSI["accent"]
ANSI_MUTED_FG = _ANSI["muted"]
ANSI_ERROR_FG = _ANSI["error"]
NYX_ACCENT = current_accent_hex()

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

# UX-BUG-03: Console singleton. Cache lazy do Console(highlight=False)
# para evitar nova instância a cada render (render_user_input e streaming
# eram call-sites quentes). Reset feito via _reset_console_cache() em
# casos extremos (SIGWINCH futuro). Sem theme aqui: o RichOutput tem
# seu próprio Console com theme Nyx; este singleton é o "padrão" sem
# theme usado por call-sites neutros (render_user_input, streaming).
_console_cache: "Console | None" = None


def _get_console() -> "Console | None":
    """Retorna Console singleton (highlight=False, sem theme) ou None.

    Lazy: cria na primeira chamada e cacheia. Idempotente. Se Rich não
    estiver disponível, retorna None — caller deve fallback para ANSI.
    """
    global _console_cache
    if _console_cache is None and RICH_AVAILABLE:
        _console_cache = Console(highlight=False)
    return _console_cache


def _reset_console_cache() -> None:
    """Reset do cache do Console singleton.

    Útil em testes e em handlers SIGWINCH (futuro ADR). Não é chamado
    no path normal — o Console é leve depois de criado.
    """
    global _console_cache
    _console_cache = None


# TUI-DEFAULT-FLIP-LEGACY-RM-01 (ONDA-32): routing buffer prompt_toolkit
# removido. NyxTUI Textual gerencia próprio output via ChatMessage widgets;
# render_* helpers daqui ficam para o caminho legacy não-TTY (input() fallback
# em cli.py) e --headless (cli_headless.py). Ambos escrevem direto em stdout.


def _emit(text: str, *, end: str = "") -> None:
    """Routing helper: escreve em stdout.

    Após ONDA-32 a Application full_screen do prompt_toolkit não existe mais;
    sys.stdout sempre está disponível para os render_* helpers. NyxTUI Textual
    NÃO chama _emit -- usa pipeline próprio de mounting de ChatMessage.
    """
    payload = text + end
    if not payload:
        return
    sys.stdout.write(payload)
    try:
        sys.stdout.flush()
    except Exception as exc:
        logger.debug("_emit flush falhou: %s", exc)


def _eprint(*args: object, sep: str = " ", end: str = "\n") -> None:
    """Equivalente a print() roteado via _emit (TUI-REDESIGN-28-08c).

    Usado em render_* migrados: mantém semântica do print() embutindo
    sep+end e fazendo routing para output_buffer ou stdout via _emit.
    """
    text = sep.join(str(a) for a in args) + end
    _emit(text)


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

    UX-LOOP-VISIBILITY-01: ``message`` aceita também ``Callable[[], str]``;
    quando callable, o thread daemon resolve a cada frame, permitindo label
    contextual (estado warming/warm, duração crescente) sem invadir o
    prompt-toolkit.
    """

    FRAME_INTERVAL_S = 0.08

    def __init__(self, message: "str | Callable[[], str]" = "pensando...") -> None:
        import threading

        self._message = message
        self._stop_evt = threading.Event()
        self._thread: threading.Thread | None = None
        self._stopped = False

    def __enter__(self) -> NyxSpinner:
        import sys
        import threading

        # TUI-SPINNER-IN-NYX-BOX-01 (sprint 227): spinner ganha afixo PURPLE
        # `│ ` à esquerda para criar coerência visual com o balão da Nyx
        # (sprint 224) e com a side-rule do streaming. TUI-DEFAULT-FLIP-LEGACY-RM-01
        # (ONDA-32): branch buffer_mode removido junto com routing prompt_toolkit;
        # spinner agora sempre anima via raw stdout (NyxTUI usa pipeline próprio).
        from nyx.themes.design_tokens import ANSI_PURPLE_FG

        frames = _spinner_frames()

        def _resolve_message() -> str:
            msg = self._message
            if callable(msg):
                try:
                    return msg()
                except Exception:  # noqa: BLE001 -- spinner não pode quebrar render
                    return "pensando..."
            return msg

        def _loop() -> None:
            idx = 0
            while not self._stop_evt.is_set():
                frame = frames[idx % len(frames)]
                label = _resolve_message()
                # Afixo PURPLE `│ ` casa com a borda esquerda do balão pós-turno
                # da Nyx (sprint 224) e com a side-rule do streaming. Indentação
                # de 2 espaços preservada (paridade com bullets e tool chips).
                sys.stdout.write(
                    f"\r\x1b[2K  {ANSI_PURPLE_FG}│{ANSI_RESET} "
                    f"{ANSI_ACCENT_FG}{frame}{ANSI_RESET}  "
                    f"{ANSI_DIM}{label}{ANSI_RESET}"
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


def nyx_spinner(message: "str | Callable[[], str]" = "pensando...") -> NyxSpinner:
    """Cria spinner Braille para uso como context manager.

    UX-LOOP-VISIBILITY-01: aceita callable para label dinâmico.
    """
    return NyxSpinner(message)


def render_progress_bar(label: str, current: int, total: int, width: int = 30) -> None:
    """[MORTO — zero chamadores; mantido por GUIDE #3] Barra de progresso discreta (VISION-01, absorve O-01).

    Formato: '  ████████░░░░░░░░░░░░░░░░░░░░░░  42% label'.

    Idempotente no mesmo line via ``\\r\\x1b[2K``; chamar
    :func:`render_progress_end` quando terminar para pular linha.
    """
    # Reaproveita modulo-level constants resolvidas via theme_manager
    # (VISUAL-LAYOUT-CLI-CONSUME-01). Import local removido.
    pct = 0.0 if total <= 0 else min(current / total, 1.0)
    filled = int(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    sys.stdout.write(
        f"\r\x1b[2K  {ANSI_ACCENT_FG}{bar}{ANSI_RESET} {int(pct * 100):3d}% "
        f"{ANSI_MUTED_FG}{label}{ANSI_RESET}"
    )
    sys.stdout.flush()


def render_progress_end() -> None:
    """Termina a barra de progresso com nova linha (VISION-01)."""
    sys.stdout.write("\n")
    sys.stdout.flush()


def build_warming_label(model_state: str, started_monotonic: float) -> str:
    """Constrói label contextual do spinner durante request (UX-LOOP-VISIBILITY-01).

    Lógica por janela de duração, baseada em ADR-025 §"Tempos de feedback":
      0-3s:   " aquecendo modelo..."     (warming explícito, glifo ◐)
      3-10s:  "pensando..."                (cold→warm, mid-flight)
      10s+:   "pensando... (Ns)"           (cronômetro discreto)

    Se o estado é "warm" ou "cold", encurta para "pensando...".

    Glifo  (U+25D0) protegido pelo invariante #14 (sprint_invariants.sh).
    """
    import time

    elapsed = time.monotonic() - started_monotonic
    if model_state == "warming" and elapsed < 3.0:
        return " aquecendo modelo..."
    if elapsed < 10.0:
        return "pensando..."
    return f"pensando... ({int(elapsed)}s)"


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
    _eprint(line1)
    _eprint(args_line)


# TUI-REDESIGN-25-11: classificação de erros conhecidos -> ações sugeridas.
# Cada entrada: (regex_or_substring, lambda(error_msg) -> list[(key, label, cmd)]).
# Aplicação fica no call-site (cli.py on_tool_result) que usa classify_error_actions.

def classify_error_actions(error_msg: str) -> list[tuple[str, str, str]]:
    """Retorna [(key, label, cmd)] sugeridas para erro conhecido (TUI-REDESIGN-25-11)."""
    if not error_msg:
        return []
    low = error_msg.lower()
    # Sandbox/fora do projeto
    if "fora do projeto" in low or "outside project" in low:
        return [
            ("a", "adicionar pasta ao sandbox", "/sandbox add <caminho>"),
            ("b", "trocar diretório de trabalho", "/cd <caminho>"),
            ("c", "colar conteúdo aqui", "(paste manual)"),
        ]
    # Permissão
    if "permissão" in low or "permission denied" in low or "permissao" in low:
        return [
            ("a", "adicionar permissão", "/permissions add <tool>"),
            ("b", "executar mesmo assim", "/bypass on"),
            ("c", "pular esta ação", "(skip)"),
        ]
    # Arquivo não encontrado
    if "não encontrado" in low or "not found" in low or "nao encontrado" in low:  # noqa-acento
        return [
            ("a", "criar arquivo", "/edit <caminho> (cria)"),
            ("b", "trocar diretório", "/cd <pasta>"),
            ("c", "descartar", "(skip)"),
        ]
    # Syntax error
    if "syntax" in low or "sintaxe" in low:
        return [
            ("a", "editar trecho", "/edit <caminho>"),
            ("b", "reler arquivo", "(re-Read)"),
            ("c", "ignorar", "(skip)"),
        ]
    return []


def render_error_with_actions(
    msg: str,
    actions: list[tuple[str, str, str]] | None = None,
) -> None:
    """Renderiza erro + ações sugeridas (TUI-REDESIGN-25-11).

    Formato:
      [erro] msg
        (a) label  → comando
        (b) ...

    Se ``actions`` é None, tenta classificar via classify_error_actions(msg).
    """
    from nyx.themes.design_tokens import ANSI_ERROR_FG

    if actions is None:
        actions = classify_error_actions(msg)
    print(f"  {ANSI_ERROR_FG}[erro]{ANSI_RESET} {msg}")
    for key, label, cmd in actions:
        print(
            f"      {ANSI_ACCENT_FG}({key}){ANSI_RESET} {label}  "
            f"{ANSI_DIM}→ {cmd}{ANSI_RESET}"
        )


_TODO_PATTERN = re.compile(r"^\s*-\s*\[([x ])\]\s*(.+?)\s*$", re.IGNORECASE)


def parse_todo_lines(text: str) -> list[tuple[bool, str]]:
    """Detecta linhas markdown '- [ ] X' e '- [x] X' em texto (TUI-REDESIGN-25-12).

    Retorna lista [(done: bool, label: str)] na ordem encontrada. Texto não
    matchando é ignorado — caller decide o que fazer com linhas restantes.
    """
    items: list[tuple[bool, str]] = []
    for line in text.splitlines():
        m = _TODO_PATTERN.match(line)
        if not m:
            continue
        done = m.group(1).lower() == "x"
        items.append((done, m.group(2)))
    return items


def render_todo_block(items: list[tuple[bool, str]]) -> None:
    """[MORTO — zero chamadores; mantido por GUIDE #3] Lista de todos com checkboxes geometric shapes (TUI-REDESIGN-25-12).

    Done: ◼ (U+25FC, ◼) + texto em muted (visual strikethrough sutil).
    Pending: ◻ (U+25FB, ◻) + texto em ink. Glifos ADR-004 ok (não-emoji).
    """
    if not items:
        return
    for done, label in items:
        if done:
            glyph = "◼"  # ◼ filled small square
            print(f"      {ANSI_ACCENT_FG}{glyph}{ANSI_RESET} {ANSI_MUTED_FG}{label}{ANSI_RESET}")
        else:
            glyph = "◻"  # ◻ empty small square
            print(f"      {ANSI_ACCENT_FG}{glyph}{ANSI_RESET} {label}")


def _format_session_duration(seconds: float) -> str:
    """Formata duração da sessão como '1m32s' ou '47s' (TUI-REDESIGN-25-14)."""
    if seconds < 60:
        return f"{int(seconds)}s"
    minutes = int(seconds // 60)
    sec = int(seconds % 60)
    return f"{minutes}m{sec:02d}s"


def _render_stats_inline(
    iterations: int,
    files_read: int,
    files_modified: int,
    duration_lbl: str,
    tokens_str: str,
    short_id: str,
    saved_path: str | None,
    project_root: str | None,
) -> None:
    """Versão linhas-inline para terminais < 80 cols (fallback 25-14)."""
    _eprint()
    _eprint(f"  {ANSI_ACCENT_FG}Última Sessão{ANSI_RESET}")
    _eprint(f"  {ANSI_ACCENT_FG}{'─' * 14}{ANSI_RESET}")
    _eprint(
        f"  {ANSI_MUTED_FG}Iterações{ANSI_RESET}  {ANSI_DIM}{iterations:<5}{ANSI_RESET}"
        f"  {ANSI_MUTED_FG}Lidos{ANSI_RESET}  {ANSI_DIM}{files_read:<4}{ANSI_RESET}"
        f"  {ANSI_MUTED_FG}Modificados{ANSI_RESET}  {ANSI_DIM}{files_modified}{ANSI_RESET}"
    )
    _eprint(
        f"  {ANSI_MUTED_FG}Tempo     {ANSI_RESET} {ANSI_DIM}{duration_lbl:<5}{ANSI_RESET}"
        f"  {ANSI_MUTED_FG}Tokens         {ANSI_RESET} {ANSI_DIM}{tokens_str:<4}{ANSI_RESET}"
        f"  {ANSI_MUTED_FG}Sessão         {ANSI_RESET} {ANSI_DIM}{short_id}{ANSI_RESET}"
    )
    if saved_path:
        short = _shorten_path(saved_path, project_root, 60)
        _eprint(f"  {ANSI_MUTED_FG}salvo em  {ANSI_RESET} {ANSI_DIM}{short}{ANSI_RESET}")
    _eprint()
    _eprint(f"  {ANSI_ACCENT_FG}até.{ANSI_RESET}")
    _eprint()


def render_session_stats_card(
    iterations: int,
    files_read: int,
    files_modified: int,
    duration_s: float,
    tokens: int | None = None,
    session_id: str | None = None,
    saved_path: str | None = None,
    project_root: str | None = None,
) -> None:
    """Card de encerramento com stats em grid 3×2 com bordas (TUI-REDESIGN-26-04).

    Layout (≥ 80 cols):
      Última Sessão
      ╭─────────────────┬─────────────────┬─────────────────╮
      │ Iterações     3 │ Lidos         2 │ Modificados   0 │
      ├─────────────────┼─────────────────┼─────────────────┤
      │ Tempo     1m32s │ Tokens     1487 │ Sessão abc12345 │
      ╰─────────────────┴─────────────────┴─────────────────╯
      salvo em ~/.nyx/sessions/abc12
      até.

    Fallback < 80 cols: render_stats_inline (versão 25-14, 3 linhas).
    """
    import shutil

    duration_lbl = _format_session_duration(duration_s)
    short_id = (session_id[:8] if session_id else "—")
    tokens_str = str(tokens) if tokens is not None else "—"
    cols = shutil.get_terminal_size(fallback=(80, 24)).columns
    if cols < 80:
        _render_stats_inline(
            iterations, files_read, files_modified,
            duration_lbl, tokens_str, short_id, saved_path, project_root,
        )
        return

    # Grid 3×2: cada célula tem largura fixa CELL_W. Layout: rótulo dim
    # + valor accent à direita, padding interno 1 char cada lado.
    # CELL_W=17 cobre pior caso "Sessão" (6) + short_id de 8 chars + gap 1 + padding 2.
    CELL_W = 17
    accent = ANSI_ACCENT_FG
    muted = ANSI_MUTED_FG
    dim = ANSI_DIM
    reset = ANSI_RESET

    def cell(label: str, value: str) -> str:
        # Texto visível (sem ANSI) usa CELL_W - 2 (padding 1 cada lado).
        inner = CELL_W - 2
        # Calcula espaço entre rótulo e valor.
        gap = max(1, inner - len(label) - len(value))
        body = f"{muted}{label}{reset}{' ' * gap}{dim}{value}{reset}"
        return f" {body} "

    top = "╭" + ("─" * CELL_W + "┬") * 2 + "─" * CELL_W + "╮"
    mid = "├" + ("─" * CELL_W + "┼") * 2 + "─" * CELL_W + "┤"
    bot = "╰" + ("─" * CELL_W + "┴") * 2 + "─" * CELL_W + "╯"

    row1_cells = [
        cell("Iterações", str(iterations)),
        cell("Lidos", str(files_read)),
        cell("Modificados", str(files_modified)),
    ]
    row2_cells = [
        cell("Tempo", duration_lbl),
        cell("Tokens", tokens_str),
        cell("Sessão", short_id),
    ]

    _eprint()
    _eprint(f"  {accent}Última Sessão{reset}")
    _eprint(f"  {accent}{top}{reset}")
    _eprint(f"  {accent}│{reset}{row1_cells[0]}{accent}│{reset}{row1_cells[1]}{accent}│{reset}{row1_cells[2]}{accent}│{reset}")  # noqa: E501
    _eprint(f"  {accent}{mid}{reset}")
    _eprint(f"  {accent}│{reset}{row2_cells[0]}{accent}│{reset}{row2_cells[1]}{accent}│{reset}{row2_cells[2]}{accent}│{reset}")  # noqa: E501
    _eprint(f"  {accent}{bot}{reset}")
    if saved_path:
        short = _shorten_path(saved_path, project_root, 60)
        _eprint(f"  {muted}salvo em  {reset} {dim}{short}{reset}")
    _eprint()
    _eprint(f"  {accent}até.{reset}")
    _eprint()


def render_thinking_block(
    text: str,
    duration_s: float | None = None,
    expanded: bool = False,
    preview_chars: int = 60,
) -> None:
    """Renderiza chain-of-thought recolhível (TUI-REDESIGN-25-09).

    Collapsed (expanded=False): ' pensando · {d}s · {text[:60]}...'
    Expanded (expanded=True): bloco completo entre divisores PURPLE.

    Texto único linha (preview): chama com expanded=False; texto longo
    cabe quando expanded=True. Integração com loop/_iteration (captura
    automática do response.message.thinking) e Tab keybinding ficam
    para TUI-REDESIGN-25-09-PARTE-2.
    """
    from nyx.themes.design_tokens import ANSI_PURPLE_FG

    if not text:
        return
    duration_lbl = f"{duration_s:.1f}s" if duration_s is not None else "—"
    if not expanded:
        clean = " ".join(text.strip().split())
        preview = clean[:preview_chars]
        if len(clean) > preview_chars:
            preview += "…"
        # HOTFIX-GLYPHS-01: ▶ = ▶ (collapsed indicator)
        _eprint(
            f"  {ANSI_PURPLE_FG}▶{ANSI_RESET} {ANSI_DIM}pensando · "
            f"{duration_lbl} · {preview}{ANSI_RESET}"
        )
        return
    # Expanded: bloco entre divisores PURPLE.
    rule = "─" * 60
    # HOTFIX-GLYPHS-01: ▼ = ▼ (expanded indicator)
    _eprint(f"  {ANSI_PURPLE_FG}{rule}{ANSI_RESET}")
    _eprint(f"  {ANSI_PURPLE_FG}▼{ANSI_RESET} {ANSI_DIM}pensando · {duration_lbl}{ANSI_RESET}")
    for line in text.splitlines() or [text]:
        _eprint(f"  {ANSI_PURPLE_FG}│{ANSI_RESET} {line}")
    _eprint(f"  {ANSI_PURPLE_FG}{rule}{ANSI_RESET}")


def _visible_len(text: str) -> int:
    """Comprimento visível ignorando escapes ANSI (TUI-REDESIGN-26-03-PARTE-2)."""
    return len(re.sub(r"\033\[[0-9;]*[A-Za-z]", "", text))


# Alias retrocompatível (OUTPUT-VISIBLE-LEN-RENAME-01).
# Nome antigo `_strip_ansi` era enganoso (retorna int, não str). Mantido até
# callsites internos migrarem em sprint futura.
_strip_ansi = _visible_len


def render_tool_chip(
    name: str,
    args: dict,
    status: str,
    duration_ms: int,
    error_preview: str | None = None,
    project_root: str | None = None,
    error_actions: list[tuple[str, str, str]] | None = None,
) -> None:
    """Renderiza tool call como chip de 1 linha (TUI-REDESIGN-25-10 + 26-03 PARTE-2).

    Formato: '{glyph} {name} {arg_preview}  {Nms}  {status}' em verde/vermelho.
    Path encurtado via _shorten_path (~/.../basename ou … no meio).
    Se ``error_preview`` informado, adiciona linha extra de preview muted.

    TUI-REDESIGN-26-03-PARTE-2: ``error_actions`` (lista [(key, label, cmd)])
    renderiza chips à direita da MESMA linha se cols >= 80 e há largura
    suficiente. Fallback: render abaixo via render_error_with_actions.
    """
    import shutil

    from nyx.themes.design_tokens import (
        ANSI_ERROR_FG,
        ANSI_SUCCESS_FG,
        TOOL_GLYPHS,
    )

    # TUI-REDESIGN-26-03: glyph por tool. Fallback "●" (geometric, ADR-004 ok).
    glyph = TOOL_GLYPHS.get(name, "●")
    color = ANSI_ERROR_FG if status != "ok" else ANSI_SUCCESS_FG
    arg_preview = ""
    for key in PRIMARY_ARG_KEYS:
        if key in args and args[key] not in (None, ""):
            arg_preview = _shorten_path(str(args[key]), project_root, 50)
            break
    duration = _format_duration(duration_ms)
    # TUI-REDESIGN-26-03-PARTE-2: layout 2-col [left] [right pad-aligned].
    left_parts = [
        f"  {color}{glyph}{ANSI_RESET}",
        f"{ANSI_ACCENT_FG}{name}{ANSI_RESET}",
    ]
    if arg_preview:
        left_parts.append(f"{ANSI_DIM}{arg_preview}{ANSI_RESET}")
    left = " ".join(left_parts)
    right = (
        f"{ANSI_MUTED_FG}{duration}{ANSI_RESET} "
        f"{color}{status}{ANSI_RESET}"
    )

    cols = shutil.get_terminal_size(fallback=(80, 24)).columns
    left_visible = _strip_ansi(left)
    right_visible = _strip_ansi(right)
    # Margem mínima de 2 colunas entre left e right.
    pad_calc = cols - left_visible - right_visible - 2
    if pad_calc >= 1:
        chip_line = left + (" " * pad_calc) + "  " + right
    else:
        # Fallback terminal estreito: concatena com espaço único (layout antigo).
        chip_line = left + " " + right

    # TUI-REDESIGN-26-03-PARTE-2: chips de ações à direita sobrescrevem o
    # lado direito (substituem duration+status quando presentes).
    actions_chip = ""
    actions_above = False
    if error_actions:
        chips_parts = [
            f"{ANSI_ACCENT_FG}[{k}]{ANSI_RESET} {ANSI_DIM}{lbl}{ANSI_RESET}"
            for k, lbl, _cmd in error_actions
        ]
        actions_chip = "  ".join(chips_parts)
        chip_visible = _strip_ansi(chip_line)
        actions_visible = _strip_ansi(actions_chip)
        # Precisa de pelo menos 4 chars de gap.
        if cols >= chip_visible + actions_visible + 4:
            pad = " " * (cols - chip_visible - actions_visible - 2)
            chip_line = chip_line + pad + actions_chip
        else:
            actions_above = True

    print(chip_line)
    if error_preview:
        print(f"      {ANSI_DIM}{error_preview[:120]}{ANSI_RESET}")
    if actions_above and error_actions:
        # Fallback: chips em linha separada abaixo, indentado.
        chips_parts = [
            f"{ANSI_ACCENT_FG}[{k}]{ANSI_RESET} {ANSI_DIM}{lbl}{ANSI_RESET}"
            for k, lbl, _cmd in error_actions
        ]
        print("      " + "  ".join(chips_parts))


def render_tool_card_end(
    name: str,
    duration_ms: int,
    summary_line: str,
    is_error: bool = False,
    extra_lines: list[str] | None = None,
) -> None:
    """[DEPRECATED em TUI-REDESIGN-25-10; MORTO — zero chamadores] Use render_tool_chip.

    Fecha card de tool com duração e primeira linha do resultado.
    Mantido para callers legados; novos call-sites devem usar render_tool_chip.
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

    _eprint(top)
    for line in body_lines:
        _eprint(line)
    _eprint(bottom)


def make_ask_permission(state: dict) -> "callable":
    """Factory do callback on_permission. Respeita state['bypass'].

    Extraído de cli.py para manter o arquivo abaixo de 800 linhas
    (GUIDE.md §6). Permanece aqui porque é render layer (ADR-024).
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
    _eprint(
        f"  {ANSI_MUTED_FG}{BULLETS['note']} compactação nível {level}: "
        f"-{tokens_removed} tokens (ctx {before_pct}% → {after_pct}%){ANSI_RESET}"
    )


USER_INPUT_COLLAPSE_LINES = 8


def _render_soft_box(display_text: str, label: str, ansi_color_fg: str) -> None:
    """TUI-NYX-SOFT-BOX-01: soft-box ANSI genérico parametrizado por cor.

    Formato: ╭─ <label> ─...─╮ / │ linha ... │ / ╰─...─╯ tudo na cor passada.
    Largura ajustada dinamicamente à linha mais longa + 2 padding, com cap
    em min(console_width - 4, 100) para resposta longa da Nyx que vem como
    uma única linha de tokens sem newline. Reutilizado por user (turquesa
    ACCENT) e Nyx (roxo PURPLE), simetria visual exigida pelo feedback do
    usuário (2026-05-25).
    """
    import shutil
    import textwrap

    console_width = shutil.get_terminal_size(fallback=(80, 24)).columns
    # 4 = 2 indent + 1 borda esquerda + 1 borda direita (+1 space pad cada lado)
    # Mantém box dentro do terminal. 100 evita boxes ridiculamente largos em
    # terminais ultra-wide.
    max_inner = max(20, min(console_width - 6, 100))

    raw_lines = display_text.splitlines() or [display_text]
    # Wrap cada linha longa para caber em max_inner - 2 (descontando padding).
    wrap_w = max_inner - 2
    wrapped_lines: list[str] = []
    for ln in raw_lines:
        if not ln:
            wrapped_lines.append("")
            continue
        # textwrap.wrap respeita palavras; se uma palavra sozinha exceder
        # wrap_w, break_long_words=True fragmenta. drop_whitespace=False
        # preserva indentação interna.
        chunks = textwrap.wrap(
            ln,
            width=wrap_w,
            break_long_words=True,
            break_on_hyphens=False,
            drop_whitespace=False,
        ) or [""]
        wrapped_lines.extend(chunks)

    title = f"─ {label} ─" if label else "─"
    max_line_w = max((len(line) for line in wrapped_lines), default=0)
    inner_w = max(max_line_w + 2, len(title) + 2)
    # Cap final para não ultrapassar console.
    inner_w = min(inner_w, max_inner)
    top = "╭" + title + "─" * (inner_w - len(title)) + "╮"
    bottom = "╰" + "─" * inner_w + "╯"
    reset = ANSI_RESET
    _eprint()
    _eprint(f"  {ansi_color_fg}{top}{reset}")
    for line in wrapped_lines:
        # Trunca defensivamente se algum chunk excedeu (não deve acontecer
        # com textwrap, mas paranoia evita assert).
        if len(line) > inner_w - 2:
            line = line[: inner_w - 2]
        pad = " " * (inner_w - len(line) - 2)
        _eprint(f"  {ansi_color_fg}│{reset} {line}{pad} {ansi_color_fg}│{reset}")
    _eprint(f"  {ansi_color_fg}{bottom}{reset}")
    _eprint()


def _render_user_soft_box(display_text: str, user_name: str) -> None:
    """TUI-REDESIGN-26-01: bubble user em ANSI soft-box turquesa (ACCENT).

    Wrapper byte-a-byte sobre _render_soft_box. Call-sites antigos preservados.
    """
    _render_soft_box(display_text, user_name, ANSI_ACCENT_FG)


def render_assistant_box(display_text: str) -> None:
    """TUI-NYX-SOFT-BOX-01: bubble Nyx em ANSI soft-box roxo (PURPLE).

    Simétrico ao box do usuário. Materializa ao FIM do turno (não durante
    stream) para evitar cursor-up/repaint que dissolveu o box anterior em
    TUI-REDESIGN-26-02. Largura ajustada à linha mais longa + 2 padding.

    Chamado por render_assistant_end quando body_text é fornecido e
    console_width >= 80. Em fallback (width < 80), end emite linha em branco
    sem box, preservando comportamento da Sprint 26-02.
    """
    if not display_text.strip():
        return
    from nyx.themes.design_tokens import ANSI_PURPLE_FG
    # UX-NYX-OUTPUT-DEDUP-01: box sem titulo "Nyx" -- identidade ja vem no
    # header "◆ NyxCode" acima; titulo no box era redundante.
    _render_soft_box(display_text, "", ANSI_PURPLE_FG)


def render_user_input(
    text: str,
    console_width: int | None = None,
    expanded: bool = False,
    user_name: str = "você",
) -> None:
    """Imprime eco da mensagem do usuário num box '╭─ <user_name> ─╮'.

    Se o input tem mais de USER_INPUT_COLLAPSE_LINES linhas (paste longo)
    e ``expanded=False`` (default), colapsa para a primeira linha seguida
    de hint explicando Ctrl+O para expandir. Limiar é estritamente maior
    (> 8): paste com exatamente 8 linhas renderiza integralmente.

    Fallback pra '> texto' se terminal <80 cols ou sem suporte a Rich.

    TUI-REDESIGN-25-04: ``user_name`` substitui 'você' como title; resolve
    via git config user.name (fallback 'visitante') em call-sites que
    propagam app_state['user_display_name'].

    TUI-REDESIGN-26-01: schema=hybrid usa ANSI soft-box (mockup-faithful);
    outros schemas mantém Rich Panel default.
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

    # TUI-REDESIGN-26-01: schema-aware. Hybrid usa ANSI soft-box; outros Rich.
    try:
        from nyx.themes.theme_manager import current_schema_id
        if current_schema_id() == "hybrid" and console_width >= 80:
            _render_user_soft_box(display_text, user_name)
            return
    except Exception as exc:  # noqa: BLE001 -- fallback silencioso
        logger.debug("schema_id lookup falhou: %s", exc)

    if console_width < 80 or not RICH_AVAILABLE:
        _eprint()
        for line in display_text.splitlines() or [display_text]:
            _eprint(f"  {ANSI_ACCENT_FG}>{ANSI_RESET} {line}")
        _eprint()
        return
    try:
        console = _get_console()
        if console is None:
            for line in display_text.splitlines() or [display_text]:
                _eprint(f"  {ANSI_ACCENT_FG}>{ANSI_RESET} {line}")
            return
        console.print()
        console.print(
            Panel(
                display_text,
                title=user_name,
                title_align="left",
                border_style=f"{NYX_ACCENT}",
                expand=False,
            )
        )
        console.print()
    except Exception as e:
        logger.debug("Rich user input render falhou: %s", e)


def wrap_token_with_side_rule(text: str, state: dict) -> str:
    """STREAMING-SIDE-RULE-01: prefixa cada linha do streaming com '│ ' PURPLE.

    state é um dict mutável que mantém continuidade entre chamadas (preserva
    bandeira at_line_start). Idempotente: passa texto sem mudança se state
    foi explicitamente desativado via state['disabled'] = True.

    Reset por turno: caller deve setar state.clear() em render_assistant_start
    para reabrir a faixa para o novo bloco da Nyx.
    """
    if state.get("disabled"):
        return text
    from nyx.themes.design_tokens import ANSI_PURPLE_FG
    PREFIX = f"  {ANSI_PURPLE_FG}│{ANSI_RESET} "

    if state.get("at_line_start", True):
        text = PREFIX + text

    if "\n" in text:
        text = text.replace("\n", "\n" + PREFIX)
        if text.endswith(PREFIX):
            text = text[:-len(PREFIX)]
            state["at_line_start"] = True
        else:
            state["at_line_start"] = False
    else:
        state["at_line_start"] = False
    return text


def render_assistant_start() -> None:
    """Header inline-leading ' Nyx' antes do streaming (TUI-REDESIGN-26-02).

    Emite uma linha:  (PURPLE) + Nyx (ACCENT bold). Meta dinâmica (tempo,
    tokens) é renderizada no rodapé via render_assistant_end (cursor não
    volta atrás durante streaming sem hack visual).
    """
    from nyx.themes.design_tokens import ANSI_BOLD, ANSI_PURPLE_FG

    # HOTFIX-GLYPHS-01: ◆ = ◆ (black diamond, header da Nyx)
    # UX-NYX-OUTPUT-DEDUP-01: "Nyx" -> "NyxCode" (identidade do projeto no header).
    _eprint(f"\n  {ANSI_PURPLE_FG}◆{ANSI_RESET} {ANSI_ACCENT_FG}{ANSI_BOLD}NyxCode{ANSI_RESET}")


def render_assistant_end(
    start_monotonic: float | None = None,
    tokens: int | None = None,
    body_text: str | None = None,
) -> None:
    """Rodapé do turno com meta opcional (TUI-REDESIGN-26-02 + 25-08 + 224).

    TUI-NYX-SOFT-BOX-01: quando body_text é fornecido e console_width>=80,
    materializa um soft-box roxo com o texto consolidado da Nyx ANTES do
    footer. Caller (cli.py) passa turn_state['streamed_text']. Texto vazio
    ou width<80 mantém comportamento prévio (sem box, footer direto).

    Se start_monotonic ou tokens informados, emite rodapé compacto:
      '└── 4.5s · 487 tokens'
    em PURPLE/DIM, simulando o fechamento do bloco do mockup.
    Sem dados, mantém comportamento antigo (linha em branco).
    """
    import shutil

    from nyx.themes.design_tokens import ANSI_PURPLE_FG

    will_box = bool(body_text and body_text.strip()) and (
        shutil.get_terminal_size(fallback=(80, 24)).columns >= 80
    )
    elapsed: float | None = None
    if start_monotonic is not None:
        import time
        elapsed = time.monotonic() - start_monotonic

    # UX-NYX-OUTPUT-DEDUP-01: quando o box materializa, o tempo vai numa
    # meta-line DIM ACIMA do box (no lugar do footer "└── Ns" que vinha
    # depois). A duplicacao stream+box ja foi eliminada por suppress_live.
    if will_box:
        if elapsed is not None:
            _eprint(
                f"  {ANSI_PURPLE_FG}│{ANSI_RESET} "
                f"{ANSI_DIM}Respondeu em apenas {elapsed:.1f}s{ANSI_RESET}"
            )
        render_assistant_box(body_text)
        return

    # Fallback (width<80 ou turno sem texto): footer compacto antigo preservado.
    if start_monotonic is None and tokens is None:
        _eprint()
        return

    parts: list[str] = []
    if elapsed is not None:
        parts.append(f"{elapsed:.1f}s")
    if tokens is not None:
        parts.append(f"{tokens} tokens")
    meta = " · ".join(parts) if parts else ""
    _eprint(
        f"  {ANSI_PURPLE_FG}└──{ANSI_RESET} {ANSI_DIM}{meta}{ANSI_RESET}"
    )
    _eprint()


def render_footer(
    pct: int,
    model: str,
    iteration: int,
    reads: int,
    mods: int,
) -> None:
    """[LEGADO/MORTO — zero chamadores] Footer do REPL prompt_toolkit pré-Textual.

    Substituído pelo widget Textual `agent/tui/widgets/toolbar.py` (ONDA-32).
    Auditado em TUI-OUTPUT-CAPITALIZATION-AUDIT-01: como não tem chamador, os
    labels minúsculos abaixo (ctx/iter/lidos/modif) são user-invisíveis e NÃO
    recebem a capitalização aplicada à toolbar viva na SPRINT 287. Mantido (não
    deletado) por GUIDE #3 "código morto: mencionar, não deletar".

    Imprime footer 1 linha acima do prompt: '── ctx X% ── modelo ── iter N ──'.

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
