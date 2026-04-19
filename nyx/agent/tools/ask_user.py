"""AskUser -- Pergunta ao usuário e retorna payload estruturado.

A tool NÃO renderiza UI nem bloqueia com input(); retorna dict serializado
como JSON em ActionResult.output. A camada CLI (output.py + cli.py) é quem
renderiza e coleta a resposta do humano (ADR-013, ADR-024).
"""

from __future__ import annotations

import json
import logging
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.ask_user")


class AskUserTool(RegisteredTool):
    action_type = ActionType.ANALYZE

    tool_def = ToolDef(
        name="ask_user",
        description=(
            "Faz uma pergunta ao usuário e aguarda resposta. "
            "Use quando precisar de decisão do usuário sobre abordagem, "
            "trade-offs ou confirmação. Pode incluir opções formatadas."
        ),
        parameters={
            "question": {"type": "string", "description": "Pergunta para o usuário"},
            "options": {
                "type": "array",
                "description": "Opções para o usuário escolher (opcional)",
                "items": {
                    "type": "object",
                    "properties": {
                        "label": {"type": "string", "description": "Texto curto da opção"},
                        "description": {"type": "string", "description": "Explicação da opção"},
                    },
                    "required": ["label"],
                },
            },
        },
        required=["question"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        question = str(params.get("question", "")).strip()
        if not question:
            return ActionResult(success=False, error="Pergunta vazia")

        raw_options = params.get("options", []) or []
        sanitized: list[dict[str, str]] = []
        if isinstance(raw_options, list):
            for opt in raw_options:
                if not isinstance(opt, dict):
                    continue
                label = str(opt.get("label", "")).strip()
                if not label:
                    continue
                desc = str(opt.get("description", "")).strip()
                sanitized.append({"label": label, "description": desc})

        payload = {
            "kind": "question",
            "question": question,
            "options": sanitized,
        }
        logger.info("ask_user: %s (%d opções)", question[:60], len(sanitized))
        return ActionResult(success=True, output=json.dumps(payload, ensure_ascii=False))


# "Perguntar é o início da sabedoria." -- Sócrates
