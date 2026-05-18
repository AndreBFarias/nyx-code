"""Glifos canônicos de Nyx -- box drawing, braille e fallback ASCII.

Zero emoji (ADR-004). Faixas proibidas: U+1F300-U+1F9FF, U+2600-U+27BF.
Usamos Box Drawing (U+2500-U+257F), Braille (U+2800-U+28FF), Block
Elements (U+2580-U+259F) e ASCII puro.

Cada estético escolhe seu peso (light/heavy/double) e seu vocabulário de
bullets. O fallback ASCII é detectado em runtime via LC_ALL+LANG.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


# ──────────────────────────────────────────────────────────────────────────────
# 1. TABELAS DE GLIFOS POR PESO
# ──────────────────────────────────────────────────────────────────────────────


@dataclass(frozen=True)
class BoxGlyphs:
    tl: str
    tr: str
    bl: str
    br: str
    h: str
    v: str
    tjoin: str
    bjoin: str
    cross: str
    ljoin: str
    rjoin: str


@dataclass(frozen=True)
class GlyphSet:
    box: BoxGlyphs
    bullet: str
    mark: str
    arrow: str
    separator: str
    pulse: tuple[str, ...]
    spinner: tuple[str, ...]
    meter_full: str
    meter_empty: str


# ─── Box drawing por peso ─────────────────────────────────────────────────────

BOX_LIGHT_ROUND = BoxGlyphs(
    tl="╭", tr="╮", bl="╰", br="╯",
    h="─", v="│",
    tjoin="┬", bjoin="┴", cross="┼", ljoin="├", rjoin="┤",
)

BOX_LIGHT_SQUARE = BoxGlyphs(
    tl="┌", tr="┐", bl="└", br="┘",
    h="─", v="│",
    tjoin="┬", bjoin="┴", cross="┼", ljoin="├", rjoin="┤",
)

BOX_HEAVY = BoxGlyphs(
    tl="┏", tr="┓", bl="┗", br="┛",
    h="━", v="┃",
    tjoin="┳", bjoin="┻", cross="╋", ljoin="┣", rjoin="┫",
)

BOX_DOUBLE = BoxGlyphs(
    tl="╔", tr="╗", bl="╚", br="╝",
    h="═", v="║",
    tjoin="╦", bjoin="╩", cross="╬", ljoin="╠", rjoin="╣",
)

BOX_ASCII = BoxGlyphs(
    tl="+", tr="+", bl="+", br="+",
    h="-", v="|",
    tjoin="+", bjoin="+", cross="+", ljoin="+", rjoin="+",
)


# ─── Spinners ─────────────────────────────────────────────────────────────────

SPINNER_BRAILLE = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
SPINNER_BLOCKS = ("▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂")
SPINNER_DOTS = ("⢀", "⢄", "⢤", "⣠", "⣄", "⣀")
SPINNER_ASCII = ("|", "/", "-", "\\")


# ─── GlyphSets nomeados por estético ──────────────────────────────────────────

GLYPHS_ARCANO = GlyphSet(
    box=BOX_LIGHT_ROUND,
    bullet="·",
    mark="*",  # mark_safe — U+2726 estaria em Dingbats
    arrow="→",
    separator="─ ─ ─",
    pulse=("⠂", "⠐", "⠠", "⠐", "⠂"),
    spinner=SPINNER_BRAILLE,
    meter_full="█",
    meter_empty="░",
)

GLYPHS_CYBER = GlyphSet(
    box=BOX_HEAVY,
    bullet="",
    mark="",
    arrow="",
    separator="━ ━ ━",
    pulse=("", "", ""),
    spinner=SPINNER_BLOCKS,
    meter_full="█",
    meter_empty="░",
)

GLYPHS_BRUTALIST = GlyphSet(
    box=BOX_ASCII,
    bullet="—",
    mark="§",
    arrow="→",
    separator="* * *",
    pulse=(".", "·", "•", "·"),
    spinner=SPINNER_ASCII,
    meter_full="#",
    meter_empty=".",
)

GLYPHS_MECHA = GlyphSet(
    box=BOX_HEAVY,
    bullet="",
    mark="",
    arrow="",
    separator="━━━",
    pulse=("▁", "▃", "▅", "▇", "▅", "▃"),
    spinner=SPINNER_BLOCKS,
    meter_full="█",
    meter_empty="░",
)

GLYPHS_EDITORIAL = GlyphSet(
    box=BOX_LIGHT_SQUARE,
    bullet="·",
    mark="¶",
    arrow="→",
    separator="* * *",
    pulse=(".", "·", "•", "·"),
    spinner=SPINNER_BRAILLE,
    meter_full="█",
    meter_empty="░",
)

GLYPHS_FALLBACK_ASCII = GlyphSet(
    box=BOX_ASCII,
    bullet="*",
    mark="*",
    arrow="->",
    separator="* * *",
    pulse=(".", "o", "O", "o"),
    spinner=SPINNER_ASCII,
    meter_full="#",
    meter_empty=".",
)


_REGISTRY: dict[str, GlyphSet] = {
    "arcano": GLYPHS_ARCANO,
    "cyber": GLYPHS_CYBER,
    "brutalist": GLYPHS_BRUTALIST,
    "mecha": GLYPHS_MECHA,
    "editorial": GLYPHS_EDITORIAL,
}


# ──────────────────────────────────────────────────────────────────────────────
# 2. DETECÇÃO DE LOCALE
# ──────────────────────────────────────────────────────────────────────────────


def supports_utf8() -> bool:
    """Detecta se o locale do terminal aguenta UTF-8.

    Override via ``NYX_FORCE_UTF8=1`` ou ``NYX_FORCE_ASCII=1``.
    """
    if os.environ.get("NYX_FORCE_UTF8") == "1":
        return True
    if os.environ.get("NYX_FORCE_ASCII") == "1":
        return False
    raw = (os.environ.get("LC_ALL", "") + os.environ.get("LANG", "")).upper()
    return "UTF-8" in raw or "UTF8" in raw


def glyphs_for(aesthetic_id: str) -> GlyphSet:
    """Retorna o GlyphSet do estético, com fallback ASCII se necessário."""
    if not supports_utf8():
        return GLYPHS_FALLBACK_ASCII
    return _REGISTRY.get(aesthetic_id, GLYPHS_ARCANO)


# ──────────────────────────────────────────────────────────────────────────────
# 3. RETRO-COMPAT — constantes do design_tokens.py original
# ──────────────────────────────────────────────────────────────────────────────

# Mantém compatibilidade com código antigo que importa BOX_CHARS, BULLETS,
# SPINNER_FRAMES diretamente. Aponta para o estético arcano (default Nyx).

_default = glyphs_for("arcano")

BOX_CHARS: dict[str, str] = {
    "tl": _default.box.tl, "tr": _default.box.tr,
    "bl": _default.box.bl, "br": _default.box.br,
    "h":  _default.box.h,  "v":  _default.box.v,
    "tjoin": _default.box.tjoin, "bjoin": _default.box.bjoin,
    "cross": _default.box.cross,
    "ljoin": _default.box.ljoin, "rjoin": _default.box.rjoin,
}

BULLETS: dict[str, str] = {
    "tool": "",
    "tool_ok": "",
    "tool_err": "",
    "result": "└─",
    "note": _default.bullet,
    "arrow": _default.arrow,
    "bypass_on": "[!]",
    "bypass_off": "[ ]",
    "ready": "",
    "working": "",
    "prompt": ">",
}

SPINNER_FRAMES = _default.spinner


__all__ = [
    "BoxGlyphs", "GlyphSet",
    "BOX_LIGHT_ROUND", "BOX_LIGHT_SQUARE", "BOX_HEAVY", "BOX_DOUBLE", "BOX_ASCII",
    "SPINNER_BRAILLE", "SPINNER_BLOCKS", "SPINNER_DOTS", "SPINNER_ASCII",
    "GLYPHS_ARCANO", "GLYPHS_CYBER", "GLYPHS_BRUTALIST", "GLYPHS_MECHA",
    "GLYPHS_EDITORIAL", "GLYPHS_FALLBACK_ASCII",
    "supports_utf8", "glyphs_for",
    "BOX_CHARS", "BULLETS", "SPINNER_FRAMES",
]


# "Um glifo bem escolhido vale mil ícones." -- desconhecido
