"""Theme Manager -- fachada de runtime para design_tokens_extended.

Resolve a paleta ativa lendo NYX_AESTHETIC + NYX_ENTITY do ambiente e
expoe escape sequences ANSI 24-bit prontas para uso pelos call sites
(nyx/agent/output.py e nyx/agent/banner.py).

ADRs:
- ADR-023 Design System -- fonte unica via design_tokens.
- ADR-029 Aesthetic Control -- VISUAL-LAYOUT-01/08/CLI-CONSUME-01.

Cache:
    resolve_palette() cacheada via lru_cache. Chave: (aesthetic_id, entity_id)
    derivada do ambiente em cada chamada externa. clear_cache() exposto para
    handlers SIGUSR1 ou comando /aesthetic seguido de restart leve.

Sprint origem: VISUAL-LAYOUT-CLI-CONSUME-01 (Onda 24).
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from nyx.themes.design_tokens_extended import DEFAULT_SCHEMA, compose, compose_full


def _env_keys() -> tuple[str, str]:
    """Le NYX_AESTHETIC e NYX_ENTITY com fallbacks canonicos."""
    return (
        os.environ.get("NYX_AESTHETIC", "default"),
        os.environ.get("NYX_ENTITY", "nyx"),
    )


def _env_keys_full() -> tuple[str, str, str]:
    """Le NYX_SCHEMA + NYX_AESTHETIC + NYX_ENTITY com fallbacks (TUI-REDESIGN-25-16)."""
    return (
        os.environ.get("NYX_SCHEMA", DEFAULT_SCHEMA),
        os.environ.get("NYX_AESTHETIC", "default"),
        os.environ.get("NYX_ENTITY", "nyx"),
    )


@lru_cache(maxsize=64)
def _compose_cached(aesthetic: str, entity: str) -> dict[str, Any]:
    """Wrap puro de compose() para benefit do lru_cache."""
    return compose(aesthetic, entity)


@lru_cache(maxsize=64)
def _compose_full_cached(
    schema: str, aesthetic: str, entity: str,
) -> dict[str, Any]:
    """Wrap puro de compose_full() cacheado (TUI-REDESIGN-25-16)."""
    return compose_full(schema, aesthetic, entity)


def resolve_palette() -> dict[str, Any]:
    """Retorna paleta ativa (aesthetic + entity) lendo ambiente.

    Estrutura: ``{aesthetic, aesthetic_id, entity, entity_id, tagline,
    palette, type, glyphs}``. Vide design_tokens_extended.compose().
    """
    aesthetic, entity = _env_keys()
    return _compose_cached(aesthetic, entity)


def resolve_active() -> dict[str, Any]:
    """Retorna config runtime completa (schema + aesthetic + entity) (TUI-REDESIGN-25-16).

    Lê NYX_SCHEMA, NYX_AESTHETIC, NYX_ENTITY do ambiente. Cacheada via
    lru_cache; clear_cache() a invalida junto com resolve_palette.
    """
    schema, aesthetic, entity = _env_keys_full()
    return _compose_full_cached(schema, aesthetic, entity)


def current_schema_id() -> str:
    """Retorna id do schema ativo lendo NYX_SCHEMA (fallback DEFAULT_SCHEMA)."""
    return os.environ.get("NYX_SCHEMA", DEFAULT_SCHEMA)


def _hex_to_ansi_fg(hex_str: str) -> str:
    """Converte #RRGGBB em escape ANSI 24-bit foreground."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


def current_ansi() -> dict[str, str]:
    """Retorna dict de escape sequences ANSI 24-bit para a paleta ativa.

    Chaves: accent, accent_lo, muted, primary, error, success, warning.
    Tambem inclui constantes universais: dim, bold, reset.
    """
    palette = resolve_palette()["palette"]
    return {
        "accent":   _hex_to_ansi_fg(palette["accent"]),
        "accent_lo": _hex_to_ansi_fg(palette["accent_lo"]),
        "muted":    _hex_to_ansi_fg(palette["ink_muted"]),
        "primary":  _hex_to_ansi_fg(palette["ink"]),
        "error":    _hex_to_ansi_fg(palette["error"]),
        "success":  _hex_to_ansi_fg(palette["success"]),
        "warning":  _hex_to_ansi_fg(palette["warning"]),
        "dim":      "\033[2m",
        "bold":     "\033[1m",
        "reset":    "\033[0m",
    }


def current_accent_hex() -> str:
    """Retorna o hex puro do accent ativo (uso em styles Rich)."""
    return resolve_palette()["palette"]["accent"]


def current_glyphs() -> dict[str, str]:
    """Retorna glyphs (box drawing) do aesthetic ativo."""
    return dict(resolve_palette()["glyphs"])


def clear_cache() -> None:
    """Limpa o cache do lru. Util apos mudanca de env em runtime."""
    _compose_cached.cache_clear()
    _compose_full_cached.cache_clear()


__all__ = [
    "resolve_palette",
    "resolve_active",
    "current_schema_id",
    "current_ansi",
    "current_accent_hex",
    "current_glyphs",
    "clear_cache",
]


# "Vidro pintado não reflete luz; espelhe a fonte." -- VISUAL-LAYOUT-CLI-CONSUME-01
