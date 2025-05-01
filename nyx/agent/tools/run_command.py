"""Tool: Bash -- Executa comando shell."""

from __future__ import annotations

import subprocess
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef


class RunCommandTool(RegisteredTool):
    action_type = ActionType.RUN_COMMAND
    tool_def = ToolDef(
        name="run_command",
        description="Executa um comando no terminal (bash)",
        parameters={
            "command": {"type": "string", "description": "Comando a executar"},
        },
        required=["command"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        command = params.get("command", "")
        if not command.strip():
            return ActionResult(success=False, error="Comando vazio")

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=project_root,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"

            return ActionResult(
                success=result.returncode == 0,
                output=output[:8000] if output else "(sem saída)",
                error=f"Exit code: {result.returncode}" if result.returncode != 0 else "",
            )
        except subprocess.TimeoutExpired:
            return ActionResult(success=False, error="Timeout: comando excedeu 120s")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


# "A linha de comando é a espada do programador." -- Neal Stephenson
