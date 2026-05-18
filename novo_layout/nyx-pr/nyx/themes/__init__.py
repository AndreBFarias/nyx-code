"""
Nyx Code — Pacote de temas

Exports principais:

    build_theme(aesthetic, entity) -> Theme
        Compõe um tema final (estético × entidade) com paleta, glifos,
        tipografia e ANSI escape codes prontos.

    load_theme_from_config() -> Theme
        Carrega o tema atual a partir de ~/.nyx/config.toml (com fallback).

    save_theme_to_config(aesthetic, entity) -> None
        Persiste a escolha do usuário.

Compatibilidade com ADR-023 (design tokens é a fonte única):
  - As constantes globais NYX_ACCENT, ANSI_ACCENT_FG, BOX_CHARS, BULLETS,
    SPINNER_FRAMES continuam exportadas via design_tokens.
  - ThemeManager legado (carrega JSON de entities/) continua funcionando.

Uso típico no banner ou em output.py:

    from nyx.themes import build_theme
    theme = build_theme("arcano", "nyx")
    print(f"{theme.ansi.accent}Nyx{theme.ansi.reset}")
    print(f"  {theme.glyphs.tl}{theme.glyphs.h * 60}{theme.glyphs.tr}")
"""

from __future__ import annotations

import os
import sys
import tomllib
from dataclasses import replace
from pathlib import Path

from nyx.themes.aesthetics import AESTHETICS, get_aesthetic, list_aesthetics
from nyx.themes.design_tokens import (
    AnsiPalette,
    Palette,
    Theme,
    hex_to_ansi_fg,
)
from nyx.themes.entities import ENTITIES, get_entity, list_entities


CONFIG_PATH = Path.home() / ".nyx" / "config.toml"
DEFAULT_AESTHETIC = "arcano"
DEFAULT_ENTITY = "nyx"


# ════════════════════════════════════════════════════════════════════════════
# COMPOSE
# ════════════════════════════════════════════════════════════════════════════

def build_theme(aesthetic: str = DEFAULT_AESTHETIC, entity: str = DEFAULT_ENTITY) -> Theme:
    """Compõe um Theme final.

    Entidade sobrescreve apenas accent + accent_lo. Ember, bg e glifos
    ficam do estético — são parte da identidade estrutural da língua visual.
    """
    a = get_aesthetic(aesthetic)
    e = get_entity(entity)

    # Palette final: tudo do estético, exceto accent/accent_lo que vêm da entidade
    palette = replace(a.palette, accent=e.accent, accent_lo=e.accent_lo)

    ansi = AnsiPalette(
        accent=hex_to_ansi_fg(palette.accent),
        accent_lo=hex_to_ansi_fg(palette.accent_lo),
        ember=hex_to_ansi_fg(palette.ember),
        ink=hex_to_ansi_fg(palette.ink),
        ink_dim=hex_to_ansi_fg(palette.ink_dim),
        ink_muted=hex_to_ansi_fg(palette.ink_muted),
        success=hex_to_ansi_fg(palette.success),
        warning=hex_to_ansi_fg(palette.warning),
        error=hex_to_ansi_fg(palette.error),
        info=hex_to_ansi_fg(palette.info),
    )

    return Theme(
        aesthetic_key=a.key,
        entity_key=e.key,
        aesthetic=a,
        entity=e,
        palette=palette,
        glyphs=a.glyphs,
        type=a.type,
        motion=a.motion,
        ansi=ansi,
    )


# ════════════════════════════════════════════════════════════════════════════
# PERSISTÊNCIA
# ════════════════════════════════════════════════════════════════════════════

def load_theme_from_config() -> Theme:
    """Carrega o tema persistido em ~/.nyx/config.toml.

    Fallback silencioso pra (arcano, nyx) em qualquer erro de leitura.
    Override por env: NYX_AESTHETIC e NYX_ENTITY (precedência maior).
    """
    aesthetic = os.environ.get("NYX_AESTHETIC")
    entity = os.environ.get("NYX_ENTITY")

    if not (aesthetic and entity) and CONFIG_PATH.exists():
        try:
            data = tomllib.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            theme_cfg = data.get("theme", {})
            aesthetic = aesthetic or theme_cfg.get("aesthetic", DEFAULT_AESTHETIC)
            entity = entity or theme_cfg.get("entity", DEFAULT_ENTITY)
        except Exception:
            pass

    aesthetic = aesthetic or DEFAULT_AESTHETIC
    entity = entity or DEFAULT_ENTITY
    return build_theme(aesthetic, entity)


def save_theme_to_config(aesthetic: str, entity: str) -> None:
    """Persiste a escolha do usuário em ~/.nyx/config.toml.

    Cria o arquivo se não existir. Não sobrescreve outras seções; só atualiza
    a tabela [theme]. Escrita atômica (tmp + rename).
    """
    if aesthetic not in AESTHETICS or entity not in ENTITIES:
        raise ValueError(f"tema inválido: {aesthetic} × {entity}")

    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

    # leitura tolerante
    existing = ""
    if CONFIG_PATH.exists():
        try:
            existing = CONFIG_PATH.read_text(encoding="utf-8")
        except Exception:
            existing = ""

    # remove seção [theme] antiga se houver
    lines = existing.splitlines()
    new_lines: list[str] = []
    in_theme_section = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            in_theme_section = stripped == "[theme]"
            if in_theme_section:
                continue
        if in_theme_section:
            continue
        new_lines.append(line)

    # appende nova seção
    new_lines.extend([
        "",
        "[theme]",
        f'aesthetic = "{aesthetic}"',
        f'entity = "{entity}"',
    ])
    content = "\n".join(new_lines).strip() + "\n"

    # escrita atômica
    tmp = CONFIG_PATH.with_suffix(".toml.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(CONFIG_PATH)


# ════════════════════════════════════════════════════════════════════════════
# REEXPORTS PÚBLICOS
# ════════════════════════════════════════════════════════════════════════════

from nyx.themes.design_tokens import (  # noqa: E402
    ANSI_ACCENT_FG, ANSI_DIM, ANSI_BOLD, ANSI_ERROR_FG,
    ANSI_MUTED_FG, ANSI_PRIMARY_FG, ANSI_PURPLE_FG,
    ANSI_RESET, ANSI_SUCCESS_FG, ANSI_WARNING_FG,
    BOX_CHARS, BULLETS, SPINNER_FRAMES,
    NYX_ACCENT, NYX_ACCENT_DIM, NYX_BG, NYX_BG_SOFT,
    NYX_ERROR, NYX_MUTED, NYX_PRIMARY, NYX_PURPLE, NYX_PURPLE_DIM,
    NYX_SUCCESS, NYX_WARNING,
)


__all__ = [
    # builder
    "build_theme",
    # persistência
    "load_theme_from_config", "save_theme_to_config",
    "CONFIG_PATH",
    # registries
    "AESTHETICS", "ENTITIES",
    "get_aesthetic", "get_entity",
    "list_aesthetics", "list_entities",
    # retrocompat (ADR-023)
    "ANSI_ACCENT_FG", "ANSI_DIM", "ANSI_BOLD", "ANSI_ERROR_FG",
    "ANSI_MUTED_FG", "ANSI_PRIMARY_FG", "ANSI_PURPLE_FG",
    "ANSI_RESET", "ANSI_SUCCESS_FG", "ANSI_WARNING_FG",
    "BOX_CHARS", "BULLETS", "SPINNER_FRAMES",
    "NYX_ACCENT", "NYX_ACCENT_DIM", "NYX_BG", "NYX_BG_SOFT",
    "NYX_ERROR", "NYX_MUTED", "NYX_PRIMARY", "NYX_PURPLE", "NYX_PURPLE_DIM",
    "NYX_SUCCESS", "NYX_WARNING",
]


# "Cada arquivo é uma promessa. Cada tema é uma promessa cumprida." — anônimo
