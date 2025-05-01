"""AskUser -- Pergunta ao usuário com opções formatadas.

Permite ao agent fazer perguntas ao usuário durante a execução.
Suporta opções com descrições para decisões de design.
"""

from __future__ import annotations

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

        options = params.get("options", [])

        lines = [f"\n  [pergunta] {question}\n"]

        if options and isinstance(options, list):
            for i, opt in enumerate(options, 1):
                if not isinstance(opt, dict):
                    continue
                label = opt.get("label", "")
                desc = opt.get("description", "")
                if desc:
                    lines.append(f"    {i}. {label} -- {desc}")
                else:
                    lines.append(f"    {i}. {label}")
            lines.append("")

        prompt_text = "\n".join(lines)
        print(prompt_text)

        try:
            if options:
                answer = input("  Resposta (número ou texto): ").strip()
                try:
                    idx = int(answer) - 1
                    if 0 <= idx < len(options):
                        selected = options[idx]
                        answer = selected.get("label", answer)
                except ValueError:
                    pass
            else:
                answer = input("  Resposta: ").strip()
        except (EOFError, KeyboardInterrupt):
            return ActionResult(success=True, output="Usuário cancelou a pergunta.")

        if not answer:
            answer = "Sem resposta"

        logger.info("Usuário respondeu: %s", answer[:60])
        return ActionResult(success=True, output=f"Resposta do usuário: {answer}")


# "Perguntar é o início da sabedoria." -- Sócrates
