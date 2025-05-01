"""AgentTool -- Executa sub-loop isolado para tarefas complexas.

Sem worktree git, sem fork de processo. Apenas um AgentLoop
com prompt isolado e sessão separada.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.agent")

AGENT_MAX_ITERATIONS = 15
AGENT_TIMEOUT = 120


class AgentTool(RegisteredTool):
    action_type = ActionType.ANALYZE

    tool_def = ToolDef(
        name="agent",
        description=(
            "Executa uma sub-tarefa em um loop isolado com sessão separada. "
            "Use para tarefas que exigem múltiplas iterações de leitura/análise "
            "sem poluir o contexto da conversa principal. "
            "O sub-agente tem acesso às mesmas tools mas sessão independente."
        ),
        parameters={
            "prompt": {"type": "string", "description": "Tarefa para o sub-agente executar"},
            "max_iterations": {
                "type": "integer",
                "description": "Limite de iterações (padrão: 15)",
            },
        },
        required=["prompt"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        prompt = str(params.get("prompt", "")).strip()
        if not prompt:
            return ActionResult(success=False, error="Prompt vazio para sub-agente")

        max_iter = int(params.get("max_iterations", AGENT_MAX_ITERATIONS))

        try:
            result = asyncio.run(self._run_sub_agent(prompt, project_root, max_iter))
            return result
        except Exception as e:
            logger.error("Erro no sub-agente: %s", e)
            return ActionResult(success=False, error=f"Sub-agente falhou: {e}")

    async def _run_sub_agent(
        self, prompt: str, project_root: str, max_iterations: int,
    ) -> ActionResult:
        from nyx.agent.loop import AgentLoop

        agent = AgentLoop(
            project_root=project_root,
            max_iterations=max_iterations,
        )

        try:
            status = await asyncio.wait_for(
                agent.run(prompt),
                timeout=AGENT_TIMEOUT,
            )

            files_read = agent.session.files_read_count
            files_modified = agent.session.files_modified_count

            summary = (
                f"[sub-agente] {status.state.value} em {status.iterations} iterações\n"
                f"Lidos: {files_read} | Modificados: {files_modified}\n"
                f"Resultado: {status.summary}"
            )

            logger.info(
                "Sub-agente: %s em %d iter (%d lidos, %d modificados)",
                status.state.value, status.iterations, files_read, files_modified,
            )

            return ActionResult(
                success=True,
                output=summary,
                files_read=sorted(agent.session._files_read),
                files_modified=sorted(agent.session._files_modified),
            )

        except asyncio.TimeoutError:
            return ActionResult(
                success=False,
                error=f"Sub-agente excedeu timeout de {AGENT_TIMEOUT}s",
            )


# "Dividir para conquistar." -- Júlio César
