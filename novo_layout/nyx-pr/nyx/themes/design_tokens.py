"""
Nyx Code — Design Tokens (PR-ready, retrocompatível com ADR-023)

Fonte única do sistema visual.

  5 estéticos:  arcano · cyber · brutalist · mecha · editorial
  7 entidades:  nyx · eris · juno · lars · luna · mars · somn

Cada tema final = estético × entidade. A entidade sobrescreve `accent` + `glow`;
o estético dita estrutura (bg, glyphs, tipografia, animação). O `ember` (cor de
alerta/destaque secundário) é parte da identidade do estético — não muda com
a entidade.

Glifos respeitam ADR-004 (zero emoji): Box Drawing (U+2500..257F),
Braille (U+2800..28FF), Block Elements (U+2580..259F), ASCII seguro.

Uso típico:

    from nyx.themes import build_theme
    theme = build_theme(aesthetic="arcano", entity="nyx")
    print(f"{theme.ansi.accent}Nyx{theme.ansi.reset}")

Retrocompatível com `nyx.themes.design_tokens` original — as constantes globais
NYX_ACCENT, ANSI_ACCENT_FG, BOX_CHARS, BULLETS, SPINNER_FRAMES continuam
exportadas e correspondem ao tema padrão (arcano × nyx).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


# ════════════════════════════════════════════════════════════════════════════
# CONVERSORES ANSI
# ════════════════════════════════════════════════════════════════════════════

def hex_to_ansi_fg(hex_str: str) -> str:
    """Converte #RRGGBB → escape ANSI 24-bit foreground."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


def hex_to_ansi_bg(hex_str: str) -> str:
    """Converte #RRGGBB → escape ANSI 24-bit background."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[48;2;{r};{g};{b}m"


ANSI_DIM = "\033[2m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"
ANSI_HIDE_CURSOR = "\033[?25l"
ANSI_SHOW_CURSOR = "\033[?25h"
ANSI_CLEAR_LINE = "\r\x1b[2K"


# ════════════════════════════════════════════════════════════════════════════
# DATACLASSES
# ════════════════════════════════════════════════════════════════════════════

AestheticKey = Literal["arcano", "cyber", "brutalist", "mecha", "editorial"]
EntityKey = Literal["nyx", "eris", "juno", "lars", "luna", "mars", "somn"]


@dataclass(frozen=True)
class Palette:
    """Cores do tema em #RRGGBB. Use `theme.ansi.<nome>` pra escape codes."""
    bg: str
    bg_soft: str
    bg_inset: str
    ink: str
    ink_dim: str
    ink_muted: str
    accent: str
    accent_lo: str
    ember: str
    success: str
    warning: str
    error: str
    info: str


@dataclass(frozen=True)
class Glyphs:
    """Conjunto canônico de glifos. Cada estético tem sua família."""
    # cantos
    tl: str
    tr: str
    bl: str
    br: str
    # linhas
    h: str
    v: str
    # junções
    tjoin: str
    bjoin: str
    cross: str
    ljoin: str
    rjoin: str
    # bullets e marcas
    bullet: str
    mark: str
    separator: str
    # spinner & barras
    spinner_frames: tuple[str, ...]
    pulse: tuple[str, ...]
    meter_full: str
    meter_empty: str
    # setas
    arrow: str
    result: str


@dataclass(frozen=True)
class Typography:
    """Famílias e métricas tipográficas (informativo — usado pelo banner e
    docs; o terminal real depende da config do emulador)."""
    mono: str
    display: str
    body: str
    mono_weight: int = 400


@dataclass(frozen=True)
class Motion:
    """Tags de comportamento de animação. Renderers consultam pra decidir
    se respiram, se piscam, se aplicam glitch, etc."""
    breathe: bool = False
    scanlines: bool = False
    grain: float = 0.0
    typewriter_speed_ms: int = 18
    glitch_chance: float = 0.0
    no_animation: bool = False


@dataclass(frozen=True)
class Aesthetic:
    """Uma das 5 línguas visuais. Não inclui accent — ele vem da entidade."""
    key: AestheticKey
    name: str
    tagline: str
    description: str
    palette: Palette
    glyphs: Glyphs
    type: Typography
    motion: Motion
    metaphor: str


@dataclass(frozen=True)
class Entity:
    """Uma das 7 entidades — sobrescreve accent + glow do estético."""
    key: EntityKey
    name: str
    description: str
    accent: str
    accent_lo: str
    glow: str
    mood: str


@dataclass(frozen=True)
class AnsiPalette:
    """Cores como escape codes ANSI 24-bit, prontas pra interpolar."""
    accent: str
    accent_lo: str
    ember: str
    ink: str
    ink_dim: str
    ink_muted: str
    success: str
    warning: str
    error: str
    info: str
    reset: str = ANSI_RESET
    dim: str = ANSI_DIM
    bold: str = ANSI_BOLD


@dataclass(frozen=True)
class Theme:
    """Tema final composto. Use `theme.ansi.<cor>` pra escape codes."""
    aesthetic_key: AestheticKey
    entity_key: EntityKey
    aesthetic: Aesthetic
    entity: Entity
    palette: Palette  # palette do aesthetic com accent/accent_lo da entity
    glyphs: Glyphs
    type: Typography
    motion: Motion
    ansi: AnsiPalette


# ════════════════════════════════════════════════════════════════════════════
# RETROCOMPATIBILIDADE — exporta constantes do tema padrão (arcano × nyx)
# ════════════════════════════════════════════════════════════════════════════
# Estas constantes são consumidas por banner.py, output.py e outros locais
# legados. Mantemos exportadas pra evitar migração big-bang.

NYX_ACCENT = "#00D4AA"
NYX_ACCENT_DIM = "#007A63"
NYX_PURPLE = "#9D4EDD"
NYX_PURPLE_DIM = "#5A189A"
NYX_PRIMARY = "#E8E8E8"
NYX_MUTED = "#606060"
NYX_BG = "#1A1B23"
NYX_BG_SOFT = "#2A2C39"
NYX_SUCCESS = "#4ADE80"
NYX_WARNING = "#FFC857"
NYX_ERROR = "#FF6B6B"

ANSI_ACCENT_FG = hex_to_ansi_fg(NYX_ACCENT)
ANSI_PURPLE_FG = hex_to_ansi_fg(NYX_PURPLE)
ANSI_PRIMARY_FG = hex_to_ansi_fg(NYX_PRIMARY)
ANSI_MUTED_FG = hex_to_ansi_fg(NYX_MUTED)
ANSI_ERROR_FG = hex_to_ansi_fg(NYX_ERROR)
ANSI_SUCCESS_FG = hex_to_ansi_fg(NYX_SUCCESS)
ANSI_WARNING_FG = hex_to_ansi_fg(NYX_WARNING)

# Conjunto canônico de glifos (default = arcano). Locale-aware fallback
# implementado em nyx/themes/glyphs.py:glyphs_for_locale().
BOX_CHARS: dict[str, str] = {
    "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
    "h": "─", "v": "│",
    "tjoin": "┬", "bjoin": "┴", "ljoin": "├", "rjoin": "┤", "cross": "┼",
}

BULLETS: dict[str, str] = {
    "tool": "",
    "tool_ok": "",
    "tool_err": "",
    "result": "└─",
    "note": "·",
    "arrow": "→",
    "bypass_on": "",
    "bypass_off": "[ ]",
    "ready": "",
    "working": "",
    "prompt": ">",
}

SPINNER_FRAMES: tuple[str, ...] = (
    "⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏",
)


__all__ = [
    # conversores
    "hex_to_ansi_fg", "hex_to_ansi_bg",
    # ANSI literais
    "ANSI_DIM", "ANSI_BOLD", "ANSI_RESET",
    "ANSI_HIDE_CURSOR", "ANSI_SHOW_CURSOR", "ANSI_CLEAR_LINE",
    # dataclasses
    "Palette", "Glyphs", "Typography", "Motion",
    "Aesthetic", "Entity", "AnsiPalette", "Theme",
    "AestheticKey", "EntityKey",
    # retrocompat — tema default
    "NYX_ACCENT", "NYX_ACCENT_DIM", "NYX_PURPLE", "NYX_PURPLE_DIM",
    "NYX_PRIMARY", "NYX_MUTED", "NYX_BG", "NYX_BG_SOFT",
    "NYX_SUCCESS", "NYX_WARNING", "NYX_ERROR",
    "ANSI_ACCENT_FG", "ANSI_PURPLE_FG", "ANSI_PRIMARY_FG", "ANSI_MUTED_FG",
    "ANSI_ERROR_FG", "ANSI_SUCCESS_FG", "ANSI_WARNING_FG",
    "BOX_CHARS", "BULLETS", "SPINNER_FRAMES",
]


# "Cada token é uma decisão de design feita uma vez, lembrada para sempre." — anônimo
