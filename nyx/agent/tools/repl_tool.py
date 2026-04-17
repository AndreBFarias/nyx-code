"""Tool: REPL -- Execução interativa de código."""

from __future__ import annotations

import logging
import subprocess
import sys
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.repl")

REPL_TIMEOUT = 30
MAX_OUTPUT = 10_000


class REPLTool(RegisteredTool):
    action_type = ActionType.REPL

    tool_def = ToolDef(
        name="repl",
        description=(
            "Executa código Python e retorna o output. "
            "Útil para cálculos, testes rápidos e exploração."
        ),
        parameters={
            "code": {"type": "string", "description": "Código Python para executar"},
        },
        required=["code"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        code = str(params.get("code", "")).strip()
        if not code:
            return ActionResult(success=False, error="Código vazio")

        try:
            proc = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=REPL_TIMEOUT,
                cwd=project_root,
            )

            stdout = proc.stdout[:MAX_OUTPUT] if proc.stdout else ""
            stderr = proc.stderr[:MAX_OUTPUT] if proc.stderr else ""

            if proc.returncode != 0:
                output = f"Exit code: {proc.returncode}"
                if stdout:
                    output += f"\nstdout:\n{stdout}"
                if stderr:
                    output += f"\nstderr:\n{stderr}"
                return ActionResult(success=False, error=output)

            output = stdout if stdout else "(sem output)"
            if stderr:
                output += f"\nstderr:\n{stderr}"

            return ActionResult(success=True, output=output)

        except subprocess.TimeoutExpired:
            return ActionResult(success=False, error=f"Timeout: execução excedeu {REPL_TIMEOUT}s")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


# "O código é a única linguagem que a máquina entende." -- Grace Hopper
