"""Tool: Bash -- Executa comando shell.

SUDO-MODE-01: quando ``sudo_session.is_active()`` retorna True e há
senha cacheada, o comando é encapsulado em ``sudo -S -p '' bash -c``
e a senha vai por stdin (sem ecoar). Lista negra de comandos
destrutivos (DANGER_PATTERNS em sudo_session) bloqueia mesmo com
elevação.
"""

from __future__ import annotations

import shlex
import subprocess
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef
from nyx.agent.tools.sudo_session import (
    get_password,
    is_destructive,
)
from nyx.agent.tools.sudo_session import (
    is_active as sudo_is_active,
)


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

        # SUDO-MODE-01: blacklist destrutiva bloqueia mesmo com sudo elevado.
        danger = is_destructive(command)
        if danger is not None:
            return ActionResult(
                success=False,
                error=f"Comando destrutivo bloqueado: '{danger}'",
            )

        sudo_active = sudo_is_active()
        sudo_pwd = get_password() if sudo_active else None

        if sudo_active and sudo_pwd is not None:
            # Encapsula em sudo -S -p '' bash -c <comando>. -S lê senha
            # de stdin sem ecoar; -p '' evita prompt "[sudo] password".
            shell_cmd = f"sudo -S -p '' bash -c {shlex.quote(command)}"
            stdin_input: str | None = sudo_pwd + "\n"
        else:
            shell_cmd = command
            stdin_input = None

        try:
            result = subprocess.run(
                shell_cmd,
                shell=True,
                input=stdin_input,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=project_root,
            )
            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"

            ok = result.returncode == 0
            hint = " Se a tarefa está completa, chame done()." if ok else ""
            # RUN-COMMAND-ERROR-OUTPUT-01: em falha o consumidor do loop grava
            # so o `error` (result.output if success else result.error, em 6
            # sitios de _iteration.py). Antes o error era so "Exit code: N" e o
            # stdout/stderr capturado era descartado -- o 3b não via o
            # diagnostico e não tinha como se autocorrigir (fere ADR-032/033: a
            # infra tinha a informação e a jogou fora). Anexamos a CAUDA do
            # output (onde vive o erro operativo: última linha do traceback,
            # sumario do pytest), capada em 4000 para não estourar a janela do 3b.
            diag = output if output else "(sem saída)"
            return ActionResult(
                success=ok,
                output=(output[:8000] if output else "(sem saída)") + hint,
                error=(
                    f"Exit code: {result.returncode}\n{diag[-4000:]}"
                    if not ok
                    else ""
                ),
            )
        except subprocess.TimeoutExpired:
            return ActionResult(success=False, error="Timeout: comando excedeu 120s")
        except Exception as e:
            return ActionResult(success=False, error=str(e))


# "A linha de comando é a espada do programador." -- Neal Stephenson
