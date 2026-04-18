"""Tool: Config -- Lê e escreve configuração do projeto."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.config")

CONFIG_FILE = Path.home() / ".nyx" / "config.json"


def _load_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        logger.debug("Falha ao carregar config: %s", e)
        return {}


def _save_config(data: dict[str, Any]) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


class ConfigTool(RegisteredTool):
    action_type = ActionType.READ_FILE

    tool_def = ToolDef(
        name="config",
        description=(
            "Lê ou escreve configuração do Nyx. Ações: get (lê chave), set (define chave=valor), list (mostra tudo)."
        ),
        parameters={
            "action": {
                "type": "string",
                "enum": ["get", "set", "list"],
                "description": "Ação: get, set ou list",
            },
            "key": {"type": "string", "description": "Chave da configuração"},
            "value": {"type": "string", "description": "Valor a definir (apenas para set)"},
        },
        required=["action"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        action = str(params.get("action", "list")).strip()
        key = str(params.get("key", "")).strip()
        value = str(params.get("value", "")).strip()

        config = _load_config()

        if action == "list":
            if not config:
                return ActionResult(success=True, output="Configuração vazia.")
            lines = [f"  {k}: {v}" for k, v in sorted(config.items())]
            return ActionResult(success=True, output="Configuração:\n" + "\n".join(lines))

        if action == "get":
            if not key:
                return ActionResult(success=False, error="Chave não especificada")
            val = config.get(key)
            if val is None:
                return ActionResult(success=True, output=f"Chave '{key}' não definida.")
            return ActionResult(success=True, output=f"{key}: {val}")

        if action == "set":
            if not key:
                return ActionResult(success=False, error="Chave não especificada")
            config[key] = value
            _save_config(config)
            logger.info("Config: %s = %s", key, value)
            return ActionResult(success=True, output=f"Definido: {key} = {value}")

        return ActionResult(success=False, error=f"Ação desconhecida: {action}")


# "Configurar é adaptar a máquina ao homem." -- Alan Kay
