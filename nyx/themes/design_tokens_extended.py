"""design_tokens_extended.py -- paletas combinatorias (aesthetics x entities).

Portado de novo_layout/src/themes.js (entrega do usuario em 2026-05-18).

Backwards compatible: AESTHETICS["default"] + ENTITIES["nyx"] reproduz a
paleta D (ADR-023) usada pelo design_tokens.py canonico.

Uso:
    from nyx.themes.design_tokens_extended import compose, get_active
    tokens = compose("arcano", "nyx")   # paleta arcana com accent Nyx
    tokens = get_active()               # respeita NYX_AESTHETIC + NYX_ENTITY

ADRs:
- ADR-023 Design System -- mantem paleta D como default.
- ADR-004 Zero Emojis -- usamos apenas Box Drawing/ASCII.
- ADR-006 PT-BR -- nomes e tags em portugues quando possivel.

Sprint origem: VISUAL-LAYOUT-01 (Onda 24).
"""

from __future__ import annotations

import os
from typing import Any

# 6 aesthetics: default (paleta D canonica) + 5 portados de novo_layout.
AESTHETICS: dict[str, dict[str, Any]] = {
    "default": {
        "name": "Default (paleta D)",
        "tagline": "Minimalismo turquesa; identidade Nyx canonica.",
        "palette": {
            "bg":         "#1A1B23",
            "bg_soft":    "#2A2C39",
            "bg_inset":   "#0A0B14",
            "ink":        "#E8E8E8",
            "ink_dim":    "#A0A8B5",
            "ink_muted":  "#6C7A89",
            "accent":     "#00D4AA",
            "accent_lo":  "#007A63",
            "ember":      "#9D4EDD",
            "success":    "#4ADE80",
            "warning":    "#FFC857",
            "error":      "#FF6B6B",
            "info":       "#86C5FF",
            "glow":       "rgba(0, 212, 170, 0.0)",
            "glow_soft":  "rgba(0, 212, 170, 0.0)",
        },
        "type": {
            "mono":         "ui-monospace, 'JetBrains Mono', monospace",
            "display":      "ui-monospace, 'JetBrains Mono', monospace",
            "body":         "ui-monospace, 'JetBrains Mono', monospace",
            "mono_weight":  400,
            "mono_track":   "0",
            "mono_leading": 1.5,
        },
        "glyphs": {
            "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
            "h":  "─", "v":  "│",
        },
    },
    "arcano": {
        "name": "Arcano",
        "tagline": "Invocando. Sussurrando. Tracejando circulos.",
        "palette": {
            "bg":         "#0E0820",
            "bg_soft":    "#16102B",
            "bg_inset":   "#08051A",
            "ink":        "#E8E0D0",
            "ink_dim":    "#9C8FB0",
            "ink_muted":  "#5A4F70",
            "accent":     "#9D4EDD",
            "accent_lo":  "#5A189A",
            "ember":      "#FFB454",
            "success":    "#7DD3A0",
            "warning":    "#FFB454",
            "error":      "#E5484D",
            "info":       "#86C5FF",
            "glow":       "rgba(157, 78, 221, 0.35)",
            "glow_soft":  "rgba(157, 78, 221, 0.15)",
        },
        "type": {
            "mono":         "'JetBrains Mono', 'Fira Code', monospace",
            "display":      "'Cormorant Garamond', 'EB Garamond', serif",
            "body":         "'Cormorant Garamond', serif",
            "mono_weight":  400,
            "mono_track":   "0.01em",
            "mono_leading": 1.55,
        },
        "glyphs": {
            "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
            "h":  "─", "v":  "│",
        },
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "tagline": "Neon saturado; scanlines; typewriter rapido.",
        "palette": {
            "bg":         "#000000",
            "bg_soft":    "#0D0D0D",
            "bg_inset":   "#1A0A1A",
            "ink":        "#F5F5F5",
            "ink_dim":    "#888888",
            "ink_muted":  "#444444",
            "accent":     "#00F5FF",
            "accent_lo":  "#00B8C0",
            "ember":      "#FF00AA",
            "success":    "#00FF88",
            "warning":    "#FFD700",
            "error":      "#FF0066",
            "info":       "#00F5FF",
            "glow":       "rgba(0, 245, 255, 0.4)",
            "glow_soft":  "rgba(255, 0, 170, 0.2)",
        },
        "type": {
            "mono":         "'JetBrains Mono', 'Roboto Mono', monospace",
            "display":      "'JetBrains Mono', monospace",
            "body":         "'JetBrains Mono', monospace",
            "mono_weight":  500,
            "mono_track":   "0",
            "mono_leading": 1.4,
        },
        "glyphs": {
            "tl": "┏", "tr": "┓", "bl": "┗", "br": "┛",
            "h":  "━", "v":  "┃",
        },
    },
    "brutalist": {
        "name": "Brutalist",
        "tagline": "Papel branco; tinta preta; Knuth-style.",
        "palette": {
            "bg":         "#FAFAF7",
            "bg_soft":    "#F0F0EC",
            "bg_inset":   "#E8E8E0",
            "ink":        "#0A0A0A",
            "ink_dim":    "#3A3A3A",
            "ink_muted":  "#7A7A7A",
            "accent":     "#0A0A0A",
            "accent_lo":  "#3A3A3A",
            "ember":      "#C8102E",
            "success":    "#1B5E20",
            "warning":    "#E65100",
            "error":      "#C8102E",
            "info":       "#0D47A1",
            "glow":       "rgba(0, 0, 0, 0)",
            "glow_soft":  "rgba(0, 0, 0, 0)",
        },
        "type": {
            "mono":         "'Courier New', 'Courier Prime', monospace",
            "display":      "'Courier New', monospace",
            "body":         "'Courier New', monospace",
            "mono_weight":  700,
            "mono_track":   "0",
            "mono_leading": 1.5,
        },
        "glyphs": {
            "tl": "+", "tr": "+", "bl": "+", "br": "+",
            "h":  "-", "v":  "|",
        },
    },
    "mecha": {
        "name": "Mecha",
        "tagline": "HUD cockpit; ambar; grid background.",
        "palette": {
            "bg":         "#0C1117",
            "bg_soft":    "#161C22",
            "bg_inset":   "#0A0F14",
            "ink":        "#E0E6ED",
            "ink_dim":    "#8A95A5",
            "ink_muted":  "#4A5460",
            "accent":     "#FFAB00",
            "accent_lo":  "#CC8800",
            "ember":      "#FF3D3D",
            "success":    "#52D072",
            "warning":    "#FFAB00",
            "error":      "#FF3D3D",
            "info":       "#3DAEFF",
            "glow":       "rgba(255, 171, 0, 0.3)",
            "glow_soft":  "rgba(255, 61, 61, 0.2)",
        },
        "type": {
            "mono":         "'Roboto Mono', 'JetBrains Mono', monospace",
            "display":      "'Roboto Mono', monospace",
            "body":         "'Roboto Mono', monospace",
            "mono_weight":  500,
            "mono_track":   "0.02em",
            "mono_leading": 1.4,
        },
        "glyphs": {
            "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
            "h":  "─", "v":  "│",
        },
    },
    "editorial": {
        "name": "Editorial",
        "tagline": "Papel creme; serif; marginalia O'Reilly.",
        "palette": {
            "bg":         "#FFFBF0",
            "bg_soft":    "#F5F0E0",
            "bg_inset":   "#FAFAF7",
            "ink":        "#1A1A1A",
            "ink_dim":    "#5A5A5A",
            "ink_muted":  "#9A9A9A",
            "accent":     "#7A4A1A",
            "accent_lo":  "#5A3A0A",
            "ember":      "#C8102E",
            "success":    "#1B5E20",
            "warning":    "#E65100",
            "error":      "#C8102E",
            "info":       "#0D47A1",
            "glow":       "rgba(0, 0, 0, 0)",
            "glow_soft":  "rgba(0, 0, 0, 0)",
        },
        "type": {
            "mono":         "'Crimson Pro', 'EB Garamond', serif",
            "display":      "'Crimson Pro', serif",
            "body":         "'Crimson Pro', serif",
            "mono_weight":  400,
            "mono_track":   "0",
            "mono_leading": 1.6,
        },
        "glyphs": {
            "tl": "(", "tr": ")", "bl": "(", "br": ")",
            "h":  "-", "v":  "|",
        },
    },
}


# 7 entidades: cada uma sobrescreve accent + glow do aesthetic.
ENTITIES: dict[str, dict[str, Any]] = {
    "nyx":  {"name": "Nyx",  "accent": "#00D4AA", "accent_lo": "#00A88A", "glow": "rgba(0, 212, 170, 0.30)"},
    "eris": {"name": "Eris", "accent": "#FF79C6", "accent_lo": "#C8568D", "glow": "rgba(255, 121, 198, 0.30)"},
    "juno": {"name": "Juno", "accent": "#A4CB58", "accent_lo": "#7AA040", "glow": "rgba(164, 203, 88, 0.30)"},
    "lars": {"name": "Lars", "accent": "#50FA7B", "accent_lo": "#3EC85F", "glow": "rgba(80, 250, 123, 0.30)"},
    "luna": {"name": "Luna", "accent": "#BD93F9", "accent_lo": "#9070C8", "glow": "rgba(189, 147, 249, 0.30)"},
    "mars": {"name": "Mars", "accent": "#FF5555", "accent_lo": "#C84040", "glow": "rgba(255, 85, 85, 0.30)"},
    "somn": {"name": "Somn", "accent": "#8BE9FD", "accent_lo": "#6BB8C8", "glow": "rgba(139, 233, 253, 0.30)"},
}


def compose(aesthetic: str = "default", entity: str = "nyx") -> dict[str, Any]:
    """Combina aesthetic + entity em paleta unificada.

    Aesthetic define bg/ink/glyphs/type. Entity sobrescreve accent + glow.
    Fallback silencioso para 'default' + 'nyx' se nome desconhecido.
    """
    base = AESTHETICS.get(aesthetic, AESTHETICS["default"])
    ent = ENTITIES.get(entity, ENTITIES["nyx"])
    palette = dict(base["palette"])
    palette["accent"] = ent["accent"]
    palette["accent_lo"] = ent["accent_lo"]
    palette["glow"] = ent["glow"]
    return {
        "aesthetic": base["name"],
        "aesthetic_id": next(
            (k for k, v in AESTHETICS.items() if v is base), "default"
        ),
        "entity": ent["name"],
        "entity_id": next(
            (k for k, v in ENTITIES.items() if v is ent), "nyx"
        ),
        "tagline": base.get("tagline", ""),
        "palette": palette,
        "type": dict(base["type"]),
        "glyphs": dict(base["glyphs"]),
    }


def get_active() -> dict[str, Any]:
    """Retorna paleta ativa lendo NYX_AESTHETIC e NYX_ENTITY do ambiente."""
    return compose(
        os.environ.get("NYX_AESTHETIC", "default"),
        os.environ.get("NYX_ENTITY", "nyx"),
    )


def list_aesthetics() -> list[dict[str, str]]:
    """Lista aesthetics disponiveis (id, name, tagline)."""
    return [
        {"id": k, "name": v["name"], "tagline": v.get("tagline", "")}
        for k, v in AESTHETICS.items()
    ]


def list_entities() -> list[dict[str, str]]:
    """Lista entidades disponiveis (id, name, accent)."""
    return [
        {"id": k, "name": v["name"], "accent": v["accent"]}
        for k, v in ENTITIES.items()
    ]


# ── Bubble styles (TUI-REDESIGN-25-03) ──────────────────────────────
# Vocabulário de bubbles que envolve mensagens do usuário e da Nyx.
# Cada "kind" descreve estrutura (glifos + padding + token de cor); a
# aplicação visual concreta usa os glifos do aesthetic ativo via compose().
# Renderização fina fica para sprints 25-07 (user) e 25-08 (Nyx).

BUBBLE_STYLES: dict[str, dict[str, Any]] = {
    "soft-box": {
        "kind": "box",
        "glyphs": ("tl", "tr", "bl", "br", "h", "v"),
        "padding": (0, 1, 0, 1),
        "color_token": "accent_lo",
        "label_position": "header",
    },
    "side-rule": {
        "kind": "rule",
        "glyphs": ("v",),
        "padding": (0, 0, 0, 2),
        "color_token": "accent",
        "label_position": "inline",
    },
    "bracket-label": {
        "kind": "label",
        "delimiters": ("[", "]"),
        "padding": (0, 1, 0, 0),
        "color_token": "ink",
        "uppercase": True,
    },
    "ornament-box": {
        "kind": "box",
        "glyphs": ("tl", "tr", "bl", "br", "h", "v"),
        "padding": (0, 2, 0, 2),
        "color_token": "accent",
        "label_position": "header",
        "ornaments": ("◆", "─"),
    },
}

DEFAULT_USER_BUBBLE = "soft-box"
DEFAULT_NYX_BUBBLE = "side-rule"


__all__ = [
    "AESTHETICS", "ENTITIES",
    "BUBBLE_STYLES", "DEFAULT_USER_BUBBLE", "DEFAULT_NYX_BUBBLE",
    "compose", "get_active",
    "list_aesthetics", "list_entities",
]
