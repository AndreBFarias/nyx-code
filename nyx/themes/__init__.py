"""Sistema de temas por entidade.

Cada tema é um JSON em nyx/themes/entities/ com as cores de uma entidade
do panteão Luna. O tema padrão é Nyx (cyan/teal via design_tokens).

Uso:
    from nyx.themes import ThemeManager

    tm = ThemeManager()
    cores = tm.load_theme("nyx")
    ansi = tm.get_ansi_colors("nyx")
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nyx.agent.services.logging_service import get_logger
from nyx.themes.constants import ANSI_RESET, DRACULA_FALLBACK, TEMA_PADRAO
from nyx.themes.utils import hex_to_ansi_raw

logger = get_logger("nyx.themes")

ENTITIES_DIR = Path(__file__).parent / "entities"


class ThemeManager:
    """Gerencia temas de entidades do panteão."""

    def __init__(self, tema_ativo: str = TEMA_PADRAO) -> None:
        self._tema_ativo = tema_ativo
        self._cache: dict[str, dict[str, Any]] = {}

    @property
    def tema_ativo(self) -> str:
        return self._tema_ativo

    @tema_ativo.setter
    def tema_ativo(self, entity_id: str) -> None:
        self._tema_ativo = entity_id

    def load_theme(self, entity_id: str | None = None) -> dict[str, str]:
        """Carrega cores de uma entidade. Fallback para Dracula."""
        entity_id = entity_id or self._tema_ativo

        if entity_id in self._cache:
            return self._cache[entity_id]

        theme_path = ENTITIES_DIR / f"{entity_id}.json"
        if not theme_path.exists():
            logger.warning("Tema '%s' não encontrado, usando fallback Dracula", entity_id)
            return DRACULA_FALLBACK.copy()

        with open(theme_path, encoding="utf-8") as f:
            data = json.load(f)

        cores = data.get("colors", DRACULA_FALLBACK)
        self._cache[entity_id] = cores
        return cores

    def get_ansi_colors(self, entity_id: str | None = None) -> dict[str, str]:
        """Retorna cores como escape sequences ANSI 24-bit.

        Para entity_id='nyx' (default), deriva de design_tokens (ADR-023).
        Demais entidades continuam via JSON + hex_to_ansi_raw.
        """
        entity_id = entity_id or self._tema_ativo
        if entity_id == "nyx":
            from nyx.themes.design_tokens import (
                ANSI_ACCENT_FG,
                ANSI_ERROR_FG,
                ANSI_MUTED_FG,
                ANSI_PRIMARY_FG,
                ANSI_PURPLE_FG,
                ANSI_SUCCESS_FG,
            )

            return {
                "accent": ANSI_ACCENT_FG,
                "primary": ANSI_PRIMARY_FG,
                "muted": ANSI_MUTED_FG,
                "error": ANSI_ERROR_FG,
                "success": ANSI_SUCCESS_FG,
                "special": ANSI_PURPLE_FG,
                "reset": ANSI_RESET,
            }
        cores = self.load_theme(entity_id)
        ansi: dict[str, str] = {}
        for chave, hex_cor in cores.items():
            ansi[chave] = hex_to_ansi_raw(hex_cor)
        ansi["reset"] = ANSI_RESET
        return ansi

    def get_theme_metadata(self, entity_id: str | None = None) -> dict[str, str]:
        """Retorna metadados do tema (id, name, description)."""
        entity_id = entity_id or self._tema_ativo
        theme_path = ENTITIES_DIR / f"{entity_id}.json"
        if not theme_path.exists():
            return {"id": entity_id, "name": entity_id, "description": ""}

        with open(theme_path, encoding="utf-8") as f:
            data = json.load(f)

        return {
            "id": data.get("id", entity_id),
            "name": data.get("name", entity_id),
            "description": data.get("description", ""),
        }

    def list_themes(self) -> list[dict[str, str]]:
        """Lista todos os temas disponíveis."""
        temas = []
        for path in sorted(ENTITIES_DIR.glob("*.json")):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            temas.append(
                {
                    "id": data.get("id", path.stem),
                    "name": data.get("name", path.stem),
                    "description": data.get("description", ""),
                }
            )
        return temas


# "A excelência não é um ato, mas um hábito." -- Aristóteles
