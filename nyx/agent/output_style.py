"""Registry de estilos de saída do Nyx (OUTPUT-STYLES-01).

Cada estilo influencia o system_prompt (hint_prompt) e dá uma dica de
tamanho (max_words, soft). Nunca altera ADRs invariantes: zero emoji,
PT-BR, anonimato, ADR-024 (render layer).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OutputStyle:
    name: str
    description: str
    hint_prompt: str
    max_words: int  # soft hint, não corta


STYLES: dict[str, OutputStyle] = {
    "default": OutputStyle(
        name="default",
        description="Trabalho normal, sem ajustes de tom.",
        hint_prompt="",
        max_words=0,
    ),
    "concise": OutputStyle(
        name="concise",
        description="Resposta mínima: frases curtas, zero floreio.",
        hint_prompt=(
            "Responda de forma mínima. Frases curtas, zero floreio. "
            "Mostre apenas o essencial. Se houver código, mantenha-o curto."
        ),
        max_words=120,
    ),
    "learning": OutputStyle(
        name="learning",
        description="Explica o porquê; bom para onboarding e ensino.",
        hint_prompt=(
            "Explique o porquê das decisões. Ofereça contexto. "
            "Quando aplicável, sugira pequenos trechos para o usuário escrever ou testar. "
            "Mantenha as explicações em PT-BR claro."
        ),
        max_words=400,
    ),
}


def get_style(name: str) -> OutputStyle:
    """Retorna estilo por nome; cai para default se desconhecido."""
    return STYLES.get(name, STYLES["default"])


def list_styles() -> list[OutputStyle]:
    return list(STYLES.values())
