"""
Nyx Code — Entidades do panteão

Cada entidade é uma "voz" — sobrescreve accent + accent_lo + glow do
estético selecionado. Ember, bg, tipografia e glifos ficam do estético.

Compatível com o JSON existente em nyx/themes/entities/*.json (carregamento
via ThemeManager.load_theme). Esta versão dataclass é a fonte canônica para
uso interno; o JSON continua valendo pra customização externa do usuário.
"""

from __future__ import annotations

from nyx.themes.design_tokens import Entity


# ════════════════════════════════════════════════════════════════════════════
# AS 7 ENTIDADES
# ════════════════════════════════════════════════════════════════════════════

NYX = Entity(
    key="nyx",
    name="Nyx",
    description="Codificadora silenciosa. Cinza cirúrgico + cyan técnico.",
    accent="#00D4AA",
    accent_lo="#007A63",
    glow="0;212;170",  # RGB triplet pra building gradients/glows
    mood="silenciosa, precisa, monástica",
)

ERIS = Entity(
    key="eris",
    name="Eris",
    description="Caos púrpura. Vermelho + rosa sobre fundo profundo.",
    accent="#FF79C6",
    accent_lo="#B84785",
    glow="255;121;198",
    mood="caótica, provocadora, brilhante",
)

JUNO = Entity(
    key="juno",
    name="Juno",
    description="Verde orgânico + laranja quente. Natureza digital.",
    accent="#A4CB58",
    accent_lo="#6F8B3A",
    glow="164;203;88",
    mood="fértil, generosa, paciente",
)

LARS = Entity(
    key="lars",
    name="Lars",
    description="Verde matrix + cyan. Terminal clássico.",
    accent="#50FA7B",
    accent_lo="#2A8C44",
    glow="80;250;123",
    mood="veterana, direta, old-school",
)

LUNA = Entity(
    key="luna",
    name="Luna",
    description="Dracula gothic. Roxo profundo + rosa neon.",
    accent="#BD93F9",
    accent_lo="#7A5BC9",
    glow="189;147;249",
    mood="melancólica, lúcida, romântica",
)

MARS = Entity(
    key="mars",
    name="Mars",
    description="Vermelho agressivo sobre negro absoluto.",
    accent="#FF5555",
    accent_lo="#992F2F",
    glow="255;85;85",
    mood="guerreira, urgente, decidida",
)

SOMN = Entity(
    key="somn",
    name="Somn",
    description="Azul profundo noturno. Cyan + roxo sobre escuridão.",
    accent="#8BE9FD",
    accent_lo="#4A8AA0",
    glow="139;233;253",
    mood="onírica, fluida, telepática",
)


# Registry pública
ENTITIES: dict[str, Entity] = {
    "nyx": NYX,
    "eris": ERIS,
    "juno": JUNO,
    "lars": LARS,
    "luna": LUNA,
    "mars": MARS,
    "somn": SOMN,
}


def get_entity(key: str) -> Entity:
    """Retorna entidade por key. Fallback silencioso pra Nyx se desconhecida."""
    return ENTITIES.get(key, NYX)


def list_entities() -> list[dict[str, str]]:
    """Lista entidades pra apresentação em /theme."""
    return [
        {"id": e.key, "name": e.name, "description": e.description, "mood": e.mood}
        for e in ENTITIES.values()
    ]


__all__ = [
    "NYX", "ERIS", "JUNO", "LARS", "LUNA", "MARS", "SOMN",
    "ENTITIES", "get_entity", "list_entities",
]
