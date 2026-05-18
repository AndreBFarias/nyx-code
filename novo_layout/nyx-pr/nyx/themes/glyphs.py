"""
Nyx Code — Glifos canônicos por estético + fallback ASCII

Cada estético tem sua família de glifos (cantos, linhas, junções, bullets,
spinner). Em terminal sem UTF-8, todos degradam pra ASCII seguro.

Detecção de locale: LC_ALL + LANG contendo "UTF-8" ou "UTF8" → unicode.
Override via env: NYX_FORCE_UTF8=1 ou NYX_FORCE_ASCII=1.

Uso:

    from nyx.themes.glyphs import glyphs_for, ASCII_SAFE
    g = glyphs_for("arcano")
    print(f"{g.tl}{g.h * 10}{g.tr}")
"""

from __future__ import annotations

import os
from functools import lru_cache

from nyx.themes.design_tokens import Glyphs


# ════════════════════════════════════════════════════════════════════════════
# DETECÇÃO DE LOCALE
# ════════════════════════════════════════════════════════════════════════════

def locale_supports_utf8() -> bool:
    """True se o locale parece suportar UTF-8.

    Override por env:
      NYX_FORCE_UTF8=1 → sempre True
      NYX_FORCE_ASCII=1 → sempre False
    Caso contrário, lê LC_ALL + LANG (uppercase). Aceita "UTF-8", "UTF8",
    "utf-8", "utf8" em qualquer posição.
    """
    if os.environ.get("NYX_FORCE_UTF8") == "1":
        return True
    if os.environ.get("NYX_FORCE_ASCII") == "1":
        return False
    raw = (os.environ.get("LC_ALL", "") + os.environ.get("LANG", "")).upper()
    return "UTF-8" in raw or "UTF8" in raw


# ════════════════════════════════════════════════════════════════════════════
# CONJUNTOS DE GLIFOS POR ESTÉTICO
# ════════════════════════════════════════════════════════════════════════════
# Cada estético tem 2 versões: a UTF-8 rica e a ASCII degradada.
# A degradação ASCII é INTENCIONAL — não bonita, mas legível.

ARCANO_UTF8 = Glyphs(
    tl="╭", tr="╮", bl="╰", br="╯",
    h="─", v="│",
    tjoin="┬", bjoin="┴", cross="┼", ljoin="├", rjoin="┤",
    bullet="·",
    mark="*",
    separator="─ ─ ─",
    spinner_frames=("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"),
    pulse=("⠂", "⠐", "⠠", "⠐", "⠂"),
    meter_full="█",
    meter_empty="░",
    arrow="→",
    result="└─",
)

CYBER_UTF8 = Glyphs(
    tl="┏", tr="┓", bl="┗", br="┛",
    h="━", v="┃",
    tjoin="┳", bjoin="┻", cross="╋", ljoin="┣", rjoin="┫",
    bullet="",
    mark="",
    separator="━ ━ ━",
    spinner_frames=("⣿", "⣷", "⣯", "⣟", "⡿", "⢿"),
    pulse=("", "", ""),
    meter_full="█",
    meter_empty="░",
    arrow="",
    result="└━",
)

BRUTALIST_ASCII = Glyphs(
    # brutalist é ASCII-first POR DESIGN (Knuth manuscript vibe), mesmo
    # em terminal UTF-8 capaz. Use BRUTALIST_UTF8 se quiser overrride.
    tl="+", tr="+", bl="+", br="+",
    h="-", v="|",
    tjoin="+", bjoin="+", cross="+", ljoin="+", rjoin="+",
    bullet="—",
    mark="§",
    separator="* * *",
    spinner_frames=("|", "/", "-", "\\"),
    pulse=(".", "·", "•", "·"),
    meter_full="#",
    meter_empty=".",
    arrow="->",
    result="`->",
)

BRUTALIST_UTF8 = Glyphs(
    # variante opt-in com cantos Unicode mas mantendo austeridade
    tl="┌", tr="┐", bl="└", br="┘",
    h="─", v="│",
    tjoin="┬", bjoin="┴", cross="┼", ljoin="├", rjoin="┤",
    bullet="—",
    mark="§",
    separator="* * *",
    spinner_frames=("|", "/", "—", "\\"),
    pulse=(".", "·", "•", "·"),
    meter_full="█",
    meter_empty="░",
    arrow="→",
    result="└─",
)

MECHA_UTF8 = Glyphs(
    tl="┏", tr="┓", bl="┗", br="┛",
    h="━", v="┃",
    tjoin="┳", bjoin="┻", cross="╋", ljoin="┣", rjoin="┫",
    bullet="",
    mark="",
    separator="━━━",
    spinner_frames=("▁", "▂", "▃", "▄", "▅", "▆", "▇", "█", "▇", "▆", "▅", "▄", "▃", "▂"),
    pulse=("▁", "▃", "▅", "▇", "▅", "▃"),
    meter_full="█",
    meter_empty="░",
    arrow="",
    result="└─",
)

EDITORIAL_UTF8 = Glyphs(
    tl="┌", tr="┐", bl="└", br="┘",
    h="─", v="│",
    tjoin="┬", bjoin="┴", cross="┼", ljoin="├", rjoin="┤",
    bullet="·",
    mark="¶",
    separator="* * *",  # U+2766 estaria em Dingbats — usamos asteriscos
    spinner_frames=("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"),
    pulse=(".", "·", "•", "·"),
    meter_full="█",
    meter_empty="░",
    arrow="→",
    result="└─",
)


# Fallback universal — usado quando locale não suporta UTF-8 (qualquer estético).
ASCII_SAFE = Glyphs(
    tl="+", tr="+", bl="+", br="+",
    h="-", v="|",
    tjoin="+", bjoin="+", cross="+", ljoin="+", rjoin="+",
    bullet="*",
    mark="*",
    separator="* * *",
    spinner_frames=("|", "/", "-", "\\"),
    pulse=(".", "o", "O", "o"),
    meter_full="#",
    meter_empty=".",
    arrow="->",
    result="`->",
)


# Registry estético → glyph set UTF-8
_UTF8_SETS: dict[str, Glyphs] = {
    "arcano": ARCANO_UTF8,
    "cyber": CYBER_UTF8,
    "brutalist": BRUTALIST_ASCII,  # propositalmente ASCII mesmo em UTF-8
    "mecha": MECHA_UTF8,
    "editorial": EDITORIAL_UTF8,
}


@lru_cache(maxsize=8)
def glyphs_for(aesthetic_key: str, *, force_ascii: bool | None = None) -> Glyphs:
    """Retorna o conjunto de glifos do estético, com fallback automático.

    Args:
        aesthetic_key: arcano | cyber | brutalist | mecha | editorial
        force_ascii: se True, força ASCII_SAFE; se None, usa detecção de locale.
    """
    if force_ascii is True:
        return ASCII_SAFE
    if force_ascii is None and not locale_supports_utf8():
        return ASCII_SAFE
    if aesthetic_key not in _UTF8_SETS:
        return ARCANO_UTF8  # default
    return _UTF8_SETS[aesthetic_key]


__all__ = [
    "locale_supports_utf8",
    "glyphs_for",
    "ARCANO_UTF8", "CYBER_UTF8",
    "BRUTALIST_ASCII", "BRUTALIST_UTF8",
    "MECHA_UTF8", "EDITORIAL_UTF8",
    "ASCII_SAFE",
]


# "Box drawing é a tipografia esquecida do terminal." — anônimo
