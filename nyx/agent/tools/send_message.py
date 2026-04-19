"""Tool: SendMessage -- Envia mensagem para agent subprocess."""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = get_logger("nyx.tools.send_message")

SEND_TIMEOUT = 120


class SendMessageTool(RegisteredTool):
    action_type = ActionType.RUN_COMMAND

    tool_def = ToolDef(
        name="send_message",
        description=(
            "Envia mensagem para um sub-agent Nyx via protocolo headless. O sub-agent processa e retorna a resposta."
        ),
        parameters={
            "to": {"type": "string", "description": "Identificador do agent destino"},
            "content": {"type": "string", "description": "Conteúdo da mensagem"},
        },
        required=["content"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        content = str(params.get("content", "")).strip()
        if not content:
            return ActionResult(success=False, error="Conteúdo vazio")

        msg = json.dumps({"type": "request", "content": content}, ensure_ascii=False)

        try:
            proc = subprocess.run(
                [sys.executable, "-m", "nyx.cli", "--headless"],
                input=msg + "\n",
                capture_output=True,
                text=True,
                timeout=SEND_TIMEOUT,
                cwd=project_root,
            )

            stdout = proc.stdout.strip()
            if not stdout:
                return ActionResult(
                    success=False,
                    error=f"Sub-agent sem resposta. stderr: {proc.stderr[:200]}",
                )

            first_line = stdout.split("\n")[0]
            try:
                resp = json.loads(first_line)
            except json.JSONDecodeError:
                return ActionResult(success=False, error=f"Resposta inválida: {first_line[:200]}")

            resp_type = resp.get("type", "")
            if resp_type == "response":
                summary = resp.get("summary", "Sem resumo")
                iters = resp.get("iterations", 0)
                return ActionResult(
                    success=True,
                    output=f"[sub-agent] {summary} ({iters} iterações)",
                )

            if resp_type == "error":
                return ActionResult(success=False, error=f"[sub-agent] {resp.get('message', 'erro')}")

            return ActionResult(success=True, output=f"[sub-agent] {json.dumps(resp, ensure_ascii=False)}")

        except subprocess.TimeoutExpired:
            return ActionResult(success=False, error=f"Timeout: sub-agent excedeu {SEND_TIMEOUT}s")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


# "Comunicação é a ponte entre o isolamento e a comunidade." -- Rollo May
