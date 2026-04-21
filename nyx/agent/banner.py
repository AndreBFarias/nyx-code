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
    ANSI_ACCENT_FG,
    ANSI_DIM,
    ANSI_MUTED_FG,
    ANSI_RESET,
    BOX_CHARS,
)

if TYPE_CHECKING:
    from nyx.config.settings import NyxSettings


def build_banner(
    model: str,
    tools_count: int,
    project: str,
    settings: "NyxSettings | None" = None,
    cols: int | None = None,
    memory_count: int | None = None,
) -> str:
    """Constrói banner de abertura. Retorna string pronta para imprimir."""
    import shutil

    from nyx.config.settings import load_settings

    if settings is None:
        settings = load_settings()
    if cols is None:
        cols = shutil.get_terminal_size(fallback=(80, 24)).columns

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
    ports_line = f":{ollama_port} ollama  ·  :{proxy_port} proxy"

    if cols < 80:
        return _build_compact(
            model, project, ports_line, accent, muted, dim, nc, tl, tr, bl, br, h, v
        )

    return _build_wide(
        model=model,
        tools_count=tools_count,
        project=project,
        ports_line=ports_line,
        memory_count=memory_count,
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
    ports_line: str,
    memory_count: int | None,
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
    """Banner completo para cols >= 80."""
    largura_total = min(cols - 2, 78)
    interior = largura_total - 2

    title_left = f" Nyx · v{NYX_VERSION} "
    title_right = " 100% offline "
    padding = interior - len(title_left) - len(title_right) - 2
    if padding < 2:
        padding = 2
    topo = f"  {accent}{tl}{h}{title_left}{h * padding}{title_right}{h}{tr}{nc}"

    def linha(payload: str) -> str:
        raw_len = len(payload)
        pad_right = interior - raw_len - 2
        if pad_right < 0:
            pad_right = 0
        return f"  {accent}{v}{nc} {payload}{' ' * pad_right} {accent}{v}{nc}"

    col_labels = f"   modelo    {model:<18s}   tools    {tools_count}"
    col_projeto = f"   projeto   {project:<18s}   visão    moondream (cold)"
    col_rede = f"   rede      {ports_line}"
    mem_str = (
        f"{memory_count} entradas" if memory_count is not None else "ativa"
    )
    col_memoria = f"   memória   {mem_str}"

    vazia = linha("")
    rodape_txt = " /help para comandos · Ctrl+D para sair "
    rodape_pad = interior - len(rodape_txt) - 2
    if rodape_pad < 2:
        rodape_pad = 2
    base = f"  {accent}{bl}{h}{muted}{rodape_txt}{accent}{h * rodape_pad}{h}{br}{nc}"

    return "\n".join([
        "",
        topo,
        vazia,
        linha(col_labels),
        linha(col_projeto),
        linha(col_rede),
        linha(col_memoria),
        vazia,
        base,
        "",
    ])


# "A forma segue a função." -- Louis Sullivan
