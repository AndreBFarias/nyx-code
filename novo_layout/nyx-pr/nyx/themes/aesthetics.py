"""
Nyx Code — Os 5 estéticos

Cada estético é uma linguagem visual completa: paleta, glifos, tipografia,
ritmo. A entidade selecionada (em entities.py) sobrescreve apenas o accent.

Por estético:
  arcano     — místico, candle-amber, serif display, breathing accents
  cyber      — neon saturado, scanlines, geometria afiada
  brutalist  — branco-papel, tinta única, sem efeitos
  mecha      — HUD cockpit, âmbar + alarme, telemetria visível
  editorial  — papel creme, serif tipográfica, marginalia
"""

from __future__ import annotations

from nyx.themes.design_tokens import (
    Aesthetic,
    Motion,
    Palette,
    Typography,
)
from nyx.themes.glyphs import (
    ARCANO_UTF8,
    BRUTALIST_ASCII,
    CYBER_UTF8,
    EDITORIAL_UTF8,
    MECHA_UTF8,
)


# ════════════════════════════════════════════════════════════════════════════
# 1. ARCANO ─ Nyx como deusa da noite. Invocação, ritual.
# ════════════════════════════════════════════════════════════════════════════
ARCANO = Aesthetic(
    key="arcano",
    name="Arcano",
    tagline="Invocando. Sussurrando. Tracejando círculos.",
    description=(
        "Tipografia que respira. Bordas com leve halo. Ruído sutil de pergaminho. "
        "A sensação é de estar lendo um grimório que pensa em código."
    ),
    palette=Palette(
        bg="#0E0820",        bg_soft="#16102B",    bg_inset="#08051A",
        ink="#E8E0D0",       ink_dim="#9C8FB0",    ink_muted="#5A4F70",
        accent="#9D4EDD",    accent_lo="#5A189A",  ember="#FFB454",
        success="#7DD3A0",   warning="#FFB454",    error="#E5484D",
        info="#86C5FF",
    ),
    glyphs=ARCANO_UTF8,
    type=Typography(
        mono="JetBrains Mono",
        display="Cormorant Garamond",
        body="Cormorant Garamond",
        mono_weight=400,
    ),
    motion=Motion(
        breathe=True,
        typewriter_speed_ms=18,
        grain=0.04,
    ),
    metaphor="A interface é um altar. Cada comando, uma invocação.",
)


# ════════════════════════════════════════════════════════════════════════════
# 2. CYBERPUNK ─ Haxxor moderno. Saturado. Rápido.
# ════════════════════════════════════════════════════════════════════════════
CYBER = Aesthetic(
    key="cyber",
    name="Cyberpunk",
    tagline="Saturação calculada. ASCII como adrenalina.",
    description=(
        "Preto absoluto. Cyan e magenta gritando. Glitch sutil em transições. "
        "Tipografia geometricamente afiada."
    ),
    palette=Palette(
        bg="#000000",        bg_soft="#0A0612",    bg_inset="#050008",
        ink="#E0FFF7",       ink_dim="#7AB8B0",    ink_muted="#3A5856",
        accent="#00F5FF",    accent_lo="#0088AA",  ember="#FF00AA",
        success="#39FF14",   warning="#FFE500",    error="#FF003C",
        info="#00F5FF",
    ),
    glyphs=CYBER_UTF8,
    type=Typography(
        mono="JetBrains Mono",
        display="Space Grotesk",
        body="Inter",
        mono_weight=500,
    ),
    motion=Motion(
        scanlines=True,
        typewriter_speed_ms=8,
        glitch_chance=0.02,
    ),
    metaphor="Um console arrombado num cofre que não existe.",
)


# ════════════════════════════════════════════════════════════════════════════
# 3. BRUTALIST ─ Manuscrito de Knuth. Branco. Preciso.
# ════════════════════════════════════════════════════════════════════════════
BRUTALIST = Aesthetic(
    key="brutalist",
    name="Brutalist",
    tagline="Uma cor de tinta. Tipografia como protagonista.",
    description=(
        "Papel branco. Tinta preta. Uma única cor de destaque (vermelho de errata). "
        "Nenhum efeito. Apenas tipografia, espaço e proporção."
    ),
    palette=Palette(
        bg="#FAFAF7",        bg_soft="#F2F0E8",    bg_inset="#E8E6DE",
        ink="#0A0A0A",       ink_dim="#454545",    ink_muted="#8A8A85",
        accent="#C8102E",    accent_lo="#7A0A1C",  ember="#1E3A8A",
        success="#0F5F2E",   warning="#A05A00",    error="#C8102E",
        info="#1E3A8A",
    ),
    glyphs=BRUTALIST_ASCII,
    type=Typography(
        mono="iA Writer Quattro",
        display="Spectral",
        body="Spectral",
        mono_weight=400,
    ),
    motion=Motion(
        breathe=False,
        typewriter_speed_ms=22,
        no_animation=True,
    ),
    metaphor="Um livro técnico que decidiu rodar comandos.",
)


# ════════════════════════════════════════════════════════════════════════════
# 4. MECHA ─ HUD de cockpit. Telemetria visível.
# ════════════════════════════════════════════════════════════════════════════
MECHA = Aesthetic(
    key="mecha",
    name="Mecha",
    tagline="Instrumentação. Medidores. Aviso. Confirmado.",
    description=(
        "Aço escuro com grid sutil. Âmbar HUD para confirmação, vermelho-alarme "
        "para perigo. Telemetria do modelo sempre visível."
    ),
    palette=Palette(
        bg="#0C1117",        bg_soft="#141B25",    bg_inset="#070A0F",
        ink="#D1E8F2",       ink_dim="#7A95A8",    ink_muted="#3E5260",
        accent="#FFAB00",    accent_lo="#B07600",  ember="#FF3D3D",
        success="#00E676",   warning="#FFAB00",    error="#FF3D3D",
        info="#4A9EFF",
    ),
    glyphs=MECHA_UTF8,
    type=Typography(
        mono="JetBrains Mono",
        display="JetBrains Mono",
        body="Inter",
        mono_weight=500,
    ),
    motion=Motion(
        typewriter_speed_ms=12,
        scanlines=False,
    ),
    metaphor="Um cockpit. Você é piloto.",
)


# ════════════════════════════════════════════════════════════════════════════
# 5. EDITORIAL ─ Livro técnico aprende a rodar.
# ════════════════════════════════════════════════════════════════════════════
EDITORIAL = Aesthetic(
    key="editorial",
    name="Editorial",
    tagline="Marginalia. Notas de rodapé. Tipografia.",
    description=(
        "Papel creme. Serif elegante para títulos, mono para código. Margens "
        "largas, linhas numeradas, notas laterais."
    ),
    palette=Palette(
        bg="#F5F1E8",        bg_soft="#EAE4D2",    bg_inset="#2A2620",
        ink="#2A2A1F",       ink_dim="#5C5848",    ink_muted="#8C7D5F",
        accent="#9C2A1A",    accent_lo="#5C1A10",  ember="#1E3A8A",
        success="#2D5A0F",   warning="#8B4500",    error="#9C2A1A",
        info="#1E3A8A",
    ),
    glyphs=EDITORIAL_UTF8,
    type=Typography(
        mono="Fira Code",
        display="Source Serif 4",
        body="Source Serif 4",
        mono_weight=450,
    ),
    motion=Motion(
        breathe=False,
        typewriter_speed_ms=20,
    ),
    metaphor="Um livro técnico que aprendeu a rodar comandos.",
)


# Registry pública
AESTHETICS: dict[str, Aesthetic] = {
    "arcano": ARCANO,
    "cyber": CYBER,
    "brutalist": BRUTALIST,
    "mecha": MECHA,
    "editorial": EDITORIAL,
}


def get_aesthetic(key: str) -> Aesthetic:
    """Retorna estético por key. Fallback silencioso pra arcano."""
    return AESTHETICS.get(key, ARCANO)


def list_aesthetics() -> list[dict[str, str]]:
    """Lista estéticos pra apresentação em /theme."""
    return [
        {
            "id": a.key,
            "name": a.name,
            "tagline": a.tagline,
            "description": a.description,
            "metaphor": a.metaphor,
        }
        for a in AESTHETICS.values()
    ]


__all__ = [
    "ARCANO", "CYBER", "BRUTALIST", "MECHA", "EDITORIAL",
    "AESTHETICS", "get_aesthetic", "list_aesthetics",
]
