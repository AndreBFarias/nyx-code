"""Banner de boot do Nyx CLI.

Consome design_tokens (ADR-023) como fonte única de cores e glifos.
Dois modos:
  - Compacto (cols < 80): 1 linha do block "$ nyx.code" + 1 linha info.
  - Amplo (cols >= 80): block "$ nyx.code▌" + box ╭─╮│╰╯ com 3 linhas
    (versão, offline, modelo/projeto/rede, tools/comandos/memória/tipo).

TUI-REDESIGN-28-06: banner reescrito como bloco textual com cursor + box
info, mantendo paleta turquesa+roxo+verde (não migra para roxo claro do
mockup HTML de referência).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nyx.__version__ import __version__ as NYX_VERSION
from nyx.themes.design_tokens import (
    ANSI_DIM,
    ANSI_PRIMARY_FG,
    ANSI_PURPLE_FG,
    ANSI_RESET,
    ANSI_SUCCESS_FG,
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
    """Versão estreita (cols < 80): block '$ nyx.code' + 1 linha info.

    Sem box; só o block textual + dados essenciais agrupados.
    """
    purple = ANSI_PURPLE_FG
    primary = ANSI_PRIMARY_FG
    success = ANSI_SUCCESS_FG
    block = (
        f"  {purple}$ {primary}nyx{purple}.{primary}code{purple}▌{nc}"
    )
    info = (
        f"  {dim}v{NYX_VERSION}{nc}  "
        f"{accent}●{nc} {success}100% offline{nc}  "
        f"{muted}Modelo{nc} {primary}{model}{nc}  "
        f"{muted}Rede{nc} {primary}{ports_line}{nc}"
    )
    return "\n".join(["", block, info, ""])


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
    """Block '$ nyx.code▌' + box info de 3 linhas (TUI-REDESIGN-28-06).

    Layout (cols >= 80, largura interna fixa = 66 chars + bordas):

        $ nyx.code▌
        ╭──────────────────────────────────────────────────────────────────╮
        │  v1.2.0    ● 100% offline                                        │
        │  Modelo X   Projeto Y   Rede :p1/:p2                             │
        │  Tools N   Comandos M   Memória ativa   Tipo REPL                │
        ╰──────────────────────────────────────────────────────────────────╯

    Cores:
      - '$ ' roxo, 'nyx' primary, '.' roxo, 'code' primary, '▌' roxo.
      - Bordas ╭─╮│╰╯ accent.
      - '●' accent. '100% offline' verde NYX_SUCCESS.
      - Rótulos muted; valores primary; versão dim.
    """
    purple = ANSI_PURPLE_FG
    primary = ANSI_PRIMARY_FG
    success = ANSI_SUCCESS_FG

    mem_str = (
        f"{memory_count} entradas" if memory_count is not None else "ativa"
    )
    # Compactar portas dentro do box (sem espaços ao redor do '/').
    ports_box = ports_short.replace(" / ", "/")

    # Largura interna do box (entre as bordas │ │). Fixa em 66 para layout
    # estável; padding lateral de 2 chars (mesmo do padding "  " externo).
    inner_w = 66

    # ---- block "$ nyx.code▌" ----
    block_line = (
        f"  {purple}$ {primary}nyx{purple}.{primary}code{purple}▌{nc}"
    )

    # ---- topo do box ----
    topo = f"  {accent}{tl}{h * inner_w}{tr}{nc}"

    # ---- linha 1 do box: versão + offline ----
    # plain: "  v1.2.0    ● 100% offline" -> visible len = 2 + len(v...) + 4 + 2 + len("100% offline")
    plain1 = f"  v{NYX_VERSION}    ● 100% offline"
    pad1 = max(1, inner_w - len(plain1))
    linha1 = (
        f"  {accent}{v}{nc}  "
        f"{dim}v{NYX_VERSION}{nc}    "
        f"{accent}●{nc} "
        f"{success}100% offline{nc}"
        f"{' ' * pad1}"
        f"{accent}{v}{nc}"
    )

    # ---- linha 2 do box: Modelo / Projeto / Rede ----
    plain2 = f"  Modelo {model}   Projeto {project}   Rede {ports_box}"
    pad2 = max(1, inner_w - len(plain2))
    linha2 = (
        f"  {accent}{v}{nc}  "
        f"{muted}Modelo{nc} {primary}{model}{nc}   "
        f"{muted}Projeto{nc} {primary}{project}{nc}   "
        f"{muted}Rede{nc} {primary}{ports_box}{nc}"
        f"{' ' * pad2}"
        f"{accent}{v}{nc}"
    )

    # ---- linha 3 do box: Tools / Comandos / Memória / Tipo ----
    plain3 = (
        f"  Tools {tools_count}   Comandos {commands_count}   "
        f"Memória {mem_str}   Tipo {session_type}"
    )
    pad3 = max(1, inner_w - len(plain3))
    linha3 = (
        f"  {accent}{v}{nc}  "
        f"{muted}Tools{nc} {primary}{tools_count}{nc}   "
        f"{muted}Comandos{nc} {primary}{commands_count}{nc}   "
        f"{muted}Memória{nc} {primary}{mem_str}{nc}   "
        f"{muted}Tipo{nc} {primary}{session_type}{nc}"
        f"{' ' * pad3}"
        f"{accent}{v}{nc}"
    )

    # ---- rodape do box ----
    base = f"  {accent}{bl}{h * inner_w}{br}{nc}"

    return "\n".join(["", block_line, topo, linha1, linha2, linha3, base, ""])


# "A forma segue a função." -- Louis Sullivan
