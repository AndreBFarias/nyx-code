"""Banner de boot do Nyx CLI.

Consome design_tokens (ADR-023) como fonte única de cores e glifos.
Dois modos:
  - Compacto (cols < 80): 3 linhas com modelo, projeto, portas, atalho.
  - Amplo (cols >= 80): banner completo com modelo, projeto, rede, visão,
    memória, atalho.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nyx.__version__ import __version__ as NYX_VERSION
from nyx.themes.design_tokens import (
    ANSI_DIM,
    ANSI_RESET,
    BOX_CHARS,
)
from nyx.themes.theme_manager import current_ansi

# VISUAL-LAYOUT-CLI-CONSUME-01: accent/muted resolvidos em import-time via
# theme_manager. Honra NYX_AESTHETIC + NYX_ENTITY. Default = paleta D.
_ANSI = current_ansi()
ANSI_ACCENT_FG = _ANSI["accent"]
ANSI_MUTED_FG = _ANSI["muted"]

if TYPE_CHECKING:
    from nyx.config.settings import NyxSettings


def build_banner(
    model: str,
    tools_count: int,
    project: str,
    settings: "NyxSettings | None" = None,
    cols: int | None = None,
    memory_count: int | None = None,
    commands_count: int | None = None,
    session_type: str = "REPL",
) -> str:
    """Constrói banner de abertura. Retorna string pronta para imprimir.

    TUI-REDESIGN-25-06: ``commands_count`` e ``session_type`` adicionados.
    Se ``commands_count`` é None, conta via list_commands() em tempo de chamada.
    """
    import shutil

    from nyx.config.settings import load_settings

    if settings is None:
        settings = load_settings()
    if cols is None:
        cols = shutil.get_terminal_size(fallback=(80, 24)).columns
    if commands_count is None:
        try:
            from nyx.agent.commands import list_commands

            commands_count = len(list_commands())
        except Exception:
            commands_count = 0

    tl = BOX_CHARS["tl"]
    tr = BOX_CHARS["tr"]
    bl = BOX_CHARS["bl"]
    br = BOX_CHARS["br"]
    h = BOX_CHARS["h"]
    v = BOX_CHARS["v"]

    accent = ANSI_ACCENT_FG
    muted = ANSI_MUTED_FG
    dim = ANSI_DIM
    nc = ANSI_RESET

    ollama_port = str(settings.ollama_port)
    proxy_port = str(settings.proxy_port)
    ports_short = f":{ollama_port} / :{proxy_port}"
    ports_line = f":{ollama_port} ollama  ·  :{proxy_port} proxy"

    if cols < 80:
        return _build_compact(
            model, project, ports_line, accent, muted, dim, nc, tl, tr, bl, br, h, v
        )

    return _build_wide(
        model=model,
        tools_count=tools_count,
        project=project,
        ports_short=ports_short,
        memory_count=memory_count,
        commands_count=commands_count,
        session_type=session_type,
        cols=cols,
        accent=accent,
        muted=muted,
        dim=dim,
        nc=nc,
        tl=tl,
        tr=tr,
        bl=bl,
        br=br,
        h=h,
        v=v,
    )


def _build_compact(
    model: str,
    project: str,
    ports_line: str,
    accent: str,
    muted: str,
    dim: str,
    nc: str,
    tl: str,
    tr: str,
    bl: str,
    br: str,
    h: str,
    v: str,
) -> str:
    """3 linhas — mínimo essencial para cols < 80."""
    topo = f"  {accent}{tl}{h} Nyx · {model} · {project} {h}{tr}{nc}"
    meio = f"  {accent}{v}{nc}   {muted}{ports_line}{nc}"
    base = f"  {accent}{bl}{h} {muted}/help · Ctrl+D{accent} {h * 6}{br}{nc}"
    return "\n".join(["", topo, meio, base, ""])


def _build_wide(
    model: str,
    tools_count: int,
    project: str,
    ports_short: str,
    memory_count: int | None,
    commands_count: int,
    session_type: str,
    cols: int,
    accent: str,
    muted: str,
    dim: str,
    nc: str,
    tl: str,
    tr: str,
    bl: str,
    br: str,
    h: str,
    v: str,
) -> str:
    """Header de sessão em 3 linhas com agrupamento (TUI-REDESIGN-25-06).

    Linha 1: Nyx vX                 100% offline (direita)
    Linha 2: Modelo X   Projeto Y   Rede :p1 / :p2
    Linha 3: Tools N   Comandos M   Memória K   Tipo Z

    Rótulos em ink_muted, valores em ink_dim, accent só no nome 'Nyx'.
    Sem hint /help aqui — o discoverability fica para o REPL.
    """
    mem_str = (
        f"{memory_count} entradas" if memory_count is not None else "ativa"
    )
    # Linha 1: logo + offline pin.
    title = f"{accent}Nyx{nc} {dim}v{NYX_VERSION}{nc}"
    right_tag = f"{muted}100% offline{nc}"
    pad = max(2, cols - len(f"Nyx v{NYX_VERSION}") - len("100% offline") - 4)
    linha_logo = f"  {title}{' ' * pad}{right_tag}"
    # Linha 2: agrupamento por rótulo (Modelo | Projeto | Rede).
    linha_ctx = (
        f"  {muted}Modelo{nc} {dim}{model}{nc}"
        f"   {muted}Projeto{nc} {dim}{project}{nc}"
        f"   {muted}Rede{nc} {dim}{ports_short}{nc}"
    )
    # Linha 3: estatísticas (Tools | Comandos | Memória | Tipo).
    linha_stats = (
        f"  {muted}Tools{nc} {dim}{tools_count}{nc}"
        f"   {muted}Comandos{nc} {dim}{commands_count}{nc}"
        f"   {muted}Memória{nc} {dim}{mem_str}{nc}"
        f"   {muted}Tipo{nc} {dim}{session_type}{nc}"
    )

    return "\n".join(["", linha_logo, linha_ctx, linha_stats, ""])


# "A forma segue a função." -- Louis Sullivan
