"""Banner de boot do Nyx CLI.

Consome design_tokens (ADR-023) como fonte única de cores e glifos.
Dois modos:
  - Compacto (cols < 80): 1 linha do block "$ nyx.code" + 1 linha info.
  - Amplo (cols >= 80): grid 2-col — coluna esquerda com "$ nyx.code▌"
    centralizado verticalmente; coluna direita com 3 rows (versão+offline,
    MODELO+PROJETO, TOOLS+COMANDOS+MEMÓRIA), separadas por ├─┤ horizontais
    e seções de cada row separadas por │ verticais.

TUI-REDESIGN-28-06: bloco textual com cursor + box info de 3 linhas.
TUI-REDESIGN-28-09: refatorado para grid 2-col fiel ao mockup; rótulos
em CAPS; "Memória ativa" fixo; paleta turquesa+roxo+verde preservada.
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
    ANSI_WARNING_FG,
    BOX_CHARS,
)
from nyx.themes.theme_manager import current_ansi, current_glyphs

# VISUAL-LAYOUT-09: junções de grade 2-col (tjoin/bjoin/ljoin/rjoin) não fazem
# parte do schema aesthetic (que cobre apenas tl/tr/bl/br/h/v). São primitivas
# estruturais transversais; vêm de BOX_CHARS legacy. Cantos+linhas migram para
# current_glyphs() em build-time (resolução por aesthetic ativo).
_TJOIN = BOX_CHARS["tjoin"]
_BJOIN = BOX_CHARS["bjoin"]
_LJOIN = BOX_CHARS["ljoin"]
_RJOIN = BOX_CHARS["rjoin"]

# VISUAL-LAYOUT-CLI-CONSUME-01: accent/muted resolvidos em import-time via
# theme_manager. Honra NYX_AESTHETIC + NYX_ENTITY. Default = paleta D.
# Accent textual segue ADR-029: vem da ENTITY (luna roxa, mars vermelho, etc).
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
    cursor: str = chr(0x258C),
) -> str:
    """Constrói banner de abertura. Retorna string pronta para imprimir.

    TUI-REDESIGN-25-06: ``commands_count`` e ``session_type`` adicionados.
    Se ``commands_count`` é None, conta via list_commands() em tempo de chamada.

    TEXTUAL-BANNER-WIDGET-01: parâmetro ``cursor`` permite à BannerWidget
    (Textual) alternar entre U+258C (full block) e U+258F (thin block) para
    animação local de blink, sem race com app.invalidate global. Default
    preserva comportamento anterior (callsites prompt_toolkit não tocam).

    TUI-BANNER-BLINK-DEFAULT-01: ``cursor=""`` (string vazia) é aceito e
    substituído internamente por " " (espaço U+0020) para preservar a
    largura visível do grid 2-col. Permite que o timer de blink alterne
    entre "|" e "" sem quebrar o alinhamento de left_w/right_w.
    """
    if cursor == "":
        cursor = " "
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

    # VISUAL-LAYOUT-09: cantos+linhas resolvidos em BUILD-TIME via current_glyphs()
    # para permitir override por NYX_AESTHETIC entre chamadas. cyberpunk → ┏┓┗┛━┃,
    # brutalist → +|-, default → ╭╮╰╯─│. ADR-029 preservado: accent textual
    # continua vindo da entity via current_ansi() (import-time).
    glyphs = current_glyphs()
    tl = glyphs["tl"]
    tr = glyphs["tr"]
    bl = glyphs["bl"]
    br = glyphs["br"]
    h = glyphs["h"]
    v = glyphs["v"]

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
            model, project, ports_line, accent, muted, dim, nc, tl, tr, bl, br, h, v,
            cursor=cursor,
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
        cursor=cursor,
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
    cursor: str = chr(0x258C),
) -> str:
    """Versão estreita (cols < 80): block '$ nyx.code' + 1 linha info.

    Sem box; só o block textual + dados essenciais agrupados.

    TUI-BANNER-BLINK-DEFAULT-01: defesa contra cursor='' direto neste path.
    """
    if cursor == "":
        cursor = " "
    purple = ANSI_PURPLE_FG
    primary = ANSI_PRIMARY_FG
    success = ANSI_SUCCESS_FG
    block = (
        f"  {purple}$ {primary}nyx{purple}.{primary}code{purple}{cursor}{nc}"
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
    cursor: str = chr(0x258C),
) -> str:
    """Grid 2-col: '$ nyx.code▌' à esquerda + box info à direita (TUI-REDESIGN-28-09).

    Layout (cols >= 80, largura interna total fixa = 70):

        ╭──────────────────┬───────────────────────────────────────────────────╮
        │                  │  v1.2.0      ●  100% offline                      │
        │                  ├───────────────────────────────────────────────────┤
        │   $ nyx.code▌    │  MODELO qwen2.5-coder:3b │ PROJETO Nyx-Code        │
        │                  ├───────────────────────────────────────────────────┤
        │                  │  TOOLS 35 │ COMANDOS 62 │ MEMÓRIA ativa            │
        ╰──────────────────┴───────────────────────────────────────────────────╯

    Cores:
      - '$ ' roxo, 'nyx' primary, '.' roxo, 'code' primary, '▌' roxo.
      - Bordas ╭─╮│╰╯ e junções ┬├┤┴ accent.
      - '●' accent. '100% offline' verde NYX_SUCCESS.
      - Rótulos CAPS muted; valores primary; versão dim.
      - Pipes internos │ entre seções em muted (mais discretos que as bordas).
      - 'Memória ativa' fixo, independente de memory_count.

    Coluna esquerda fixa em 18 chars, separador vertical em accent,
    coluna direita = inner_w - 18 - 1.

    TUI-BANNER-BLINK-DEFAULT-01: defesa contra cursor='' direto neste path.
    """
    if cursor == "":
        cursor = " "
    import os

    purple = ANSI_PURPLE_FG
    primary = ANSI_PRIMARY_FG
    success = ANSI_SUCCESS_FG
    warning = ANSI_WARNING_FG

    # UX-BANNER-GPU-STATUS-01: lê NYX_NUM_GPU (setado por run.sh após auto-tune).
    # Valor inválido ou ausente cai em 0 (CPU mode).
    try:
        num_gpu = int(os.environ.get("NYX_NUM_GPU", "0"))
    except ValueError:
        num_gpu = 0

    # Largura total interna entre │ esquerda e │ direita.
    inner_w = 70
    left_w = 18  # coluna do "$ nyx.code▌"
    right_w = inner_w - left_w - 1  # 1 char do separador │ vertical

    # ---- conteúdo da coluna esquerda ----
    # "$ nyx.code▌" tem 11 chars visíveis; centralizado horizontalmente
    # dentro de left_w=18 e verticalmente na linha 3 (centro de 5 linhas).
    # TEXTUAL-BANNER-WIDGET-01: cursor é parametrizado; default preserva ▌.
    # A largura visível permanece 11 chars pois U+258C e U+258F têm width=1.
    nyx_visible = f"$ nyx.code{cursor}"  # 11 chars
    nyx_text = (
        f"{purple}$ {primary}nyx{purple}.{primary}code{purple}{cursor}{nc}"
    )
    left_pad_total = left_w - len(nyx_visible)
    left_pad_l = left_pad_total // 2
    left_pad_r = left_pad_total - left_pad_l
    left_filled = f"{' ' * left_pad_l}{nyx_text}{' ' * left_pad_r}"
    left_empty = " " * left_w

    # ---- topo do box (com ┬ na junção de colunas) ----
    topo = (
        f"  {accent}{tl}{h * left_w}{_TJOIN}{h * right_w}{tr}{nc}"
    )

    # ---- separadores horizontais entre rows da direita (┤ na borda esquerda interna, ┤ direita) ----
    # Esquerda fica intacta (sem horizontal), só a direita recebe ── e termina em ┤.
    sep_mid = (
        f"  {accent}{v}{nc}{left_empty}{accent}{_LJOIN}{h * right_w}{_RJOIN}{nc}"
    )

    # ---- row 1 (direita): versão + offline + GPU/CPU ----
    # UX-BANNER-GPU-STATUS-01: campo GPU/CPU após "100% offline", separado por
    # '·' muted. GPU: N layers em accent (turquesa) se num_gpu > 0; CPU em
    # warning (amarelo-âmbar) caso contrário.
    if num_gpu > 0:
        gpu_plain = f"GPU: {num_gpu} layers"
        gpu_colored = f"{accent}GPU:{nc} {primary}{num_gpu} layers{nc}"
    else:
        gpu_plain = "CPU"
        gpu_colored = f"{warning}CPU{nc}"
    # plain visible: "  v1.3.0  ●  100% offline  ·  GPU: N layers" within right_w
    plain_r1 = f"  v{NYX_VERSION}  ●  100% offline  ·  {gpu_plain}"
    pad_r1 = max(1, right_w - len(plain_r1))
    row1_right = (
        f"  {dim}v{NYX_VERSION}{nc}  "
        f"{accent}●{nc}  "
        f"{success}100% offline{nc}  "
        f"{muted}·{nc}  "
        f"{gpu_colored}"
        f"{' ' * pad_r1}"
    )
    linha_r1 = (
        f"  {accent}{v}{nc}{left_empty}{accent}{v}{nc}{row1_right}{accent}{v}{nc}"
    )

    # ---- row 2 (direita): MODELO + PROJETO (separados por │ muted) ----
    plain_r2 = f"  MODELO {model} | PROJETO {project}"
    pad_r2 = max(1, right_w - len(plain_r2))
    row2_right = (
        f"  {muted}MODELO{nc} {primary}{model}{nc} "
        f"{muted}{v}{nc} "
        f"{muted}PROJETO{nc} {primary}{project}{nc}"
        f"{' ' * pad_r2}"
    )
    # Linha 3 da grid (centro): aqui mostra o "$ nyx.code▌" na esquerda.
    linha_r2 = (
        f"  {accent}{v}{nc}{left_filled}{accent}{v}{nc}{row2_right}{accent}{v}{nc}"
    )

    # ---- row 3 (direita): TOOLS + COMANDOS + MEMÓRIA ativa ----
    plain_r3 = (
        f"  TOOLS {tools_count} | COMANDOS {commands_count} | MEMÓRIA ativa"
    )
    pad_r3 = max(1, right_w - len(plain_r3))
    row3_right = (
        f"  {muted}TOOLS{nc} {primary}{tools_count}{nc} "
        f"{muted}{v}{nc} "
        f"{muted}COMANDOS{nc} {primary}{commands_count}{nc} "
        f"{muted}{v}{nc} "
        f"{muted}MEMÓRIA{nc} {primary}ativa{nc}"
        f"{' ' * pad_r3}"
    )
    linha_r3 = (
        f"  {accent}{v}{nc}{left_empty}{accent}{v}{nc}{row3_right}{accent}{v}{nc}"
    )

    # ---- rodape do box (com ┴ na junção de colunas) ----
    base = (
        f"  {accent}{bl}{h * left_w}{_BJOIN}{h * right_w}{br}{nc}"
    )

    return "\n".join(
        [
            "",
            topo,
            linha_r1,
            sep_mid,
            linha_r2,
            sep_mid,
            linha_r3,
            base,
            "",
        ]
    )


# "A forma segue a função." -- Louis Sullivan
