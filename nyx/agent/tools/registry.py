"""ToolRegistry -- Carrega e executa tools do Nyx Agent."""

from __future__ import annotations

import asyncio
import json
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.services.hooks import ToolHooks
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import RegisteredTool, ToolDef

from .agent_tool import AgentTool
from .analyze_tool import AnalyzeTool
from .ask_user import AskUserTool
from .brief_tool import BriefTool
from .config_tool import ConfigTool
from .done import DoneTool
from .edit_file import EditFileTool
from .glob_tool import GlobTool
from .list_files import ListFilesTool
from .multi_edit import MultiEditTool
from .notebook_edit import NotebookEditTool
from .patch_tool import PatchTool
from .plan_mode import EnterPlanModeTool, ExitPlanModeTool
from .read_file import ReadFileTool
from .repl_tool import REPLTool
from .run_command import RunCommandTool
from .search import SearchTool
from .send_message import SendMessageTool
from .skill_tool import SkillTool
from .sleep_tool import SleepTool
from .sudo_session import (
    status as _sudo_session_status,  # noqa: F401 -- ADR-013: singleton module-level state (SUDO-MODE-01); sem classe Tool, mantém arquivo carregado conforme integração obrigatória
)
from .task_manager import (
    TaskCreateTool,
    TaskGetTool,
    TaskListTool,
    TaskOutputTool,
    TaskStopTool,
    TaskUpdateTool,
)
from .todo_write import TodoWriteTool
from .tool_search import ToolSearchTool
from .web_fetch import WebFetchTool
from .web_search import WebSearchTool
from .worktree import EnterWorktreeTool, ExitWorktreeTool
from .write_file import WriteFileTool
from .write_memory import WriteMemoryTool

logger = get_logger("nyx.tools")


class ToolRegistry:
    def __init__(self, project_root: str) -> None:
        self.project_root = project_root
        self._tools: dict[str, RegisteredTool] = {}
        self._hooks = ToolHooks()
        self._load_tools()
        # MCP-SERVER-03: descoberta MCP é boot-tolerante (try amplo).
        # Falha de descoberta NÃO derruba o registry; tools nativas
        # permanecem 100% disponíveis. Roda 1x no boot — asyncio.run
        # síncrono é aceitável (timeout curto via connect_all_with_timeout).
        self._load_mcp_tools()

    def _load_mcp_tools(self) -> None:
        """Descobre tools MCP no boot e registra com prefix mcp_<server>_<tool>.

        Boot-tolerante: try amplo envolve toda descoberta. Falha (mcp.json
        ausente, server offline, timeout) é logada e ignorada. Tools
        nativas continuam disponíveis sem MCP. MCP-SERVER-03.
        """
        try:
            from nyx.agent.services.mcp_client import (
                CONNECT_TIMEOUT_S,
                McpClient,
                load_mcp_servers,
            )

            servers = load_mcp_servers()
            if not servers:
                return
            # Se já há event loop rodando (ToolRegistry instanciado dentro
            # de contexto async, ex.: gauntlet, testes pytest-asyncio),
            # asyncio.run rejeita e a descoberta MCP é pulada graciosamente.
            # MCP discovery roda apenas no boot síncrono real do agente.
            try:
                asyncio.get_running_loop()
            except RuntimeError:
                # Sem loop ativo: caminho normal síncrono asyncio.run.
                logger.debug("MCP discovery: nenhum loop ativo, prossegue sincrono")
            else:
                logger.warning(
                    "MCP discovery: event loop ativo no construtor — descoberta pulada"
                )
                return
            client = McpClient(servers=servers)
            try:
                asyncio.run(client.connect_all_with_timeout(timeout=CONNECT_TIMEOUT_S))
            except Exception as e:  # noqa: BLE001 -- descoberta MCP best-effort
                logger.warning("MCP discovery falhou no boot: %s", e)
                return
            registered = 0
            for server in client.servers.values():
                if not getattr(server, "connected", False):
                    continue
                for tool_def in server.tools:
                    raw_name = tool_def.get("name") if isinstance(tool_def, dict) else None
                    if not raw_name:
                        continue
                    tool_name = f"mcp_{server.name}_{raw_name}"
                    if tool_name in self._tools:
                        logger.warning(
                            "MCP tool %s já registrada (colisão); mantendo primeira",
                            tool_name,
                        )
                        continue
                    self._tools[tool_name] = McpToolAdapter(
                        client=client, server=server, tool_def=tool_def, name=tool_name
                    )
                    registered += 1
            if registered:
                logger.info("MCP discovery: %d tool(s) registradas no ToolRegistry", registered)
        except Exception as e:  # noqa: BLE001 -- envelope final anti-crash
            logger.warning("_load_mcp_tools: falha não-fatal capturada: %s", e)

    def _load_tools(self) -> None:
        for cls in [
            ReadFileTool,
            WriteFileTool,
            EditFileTool,
            RunCommandTool,
            GlobTool,
            SearchTool,
            ListFilesTool,
            NotebookEditTool,
            TodoWriteTool,
            WebFetchTool,
            WebSearchTool,
            TaskCreateTool,
            TaskUpdateTool,
            TaskListTool,
            TaskGetTool,
            TaskOutputTool,
            TaskStopTool,
            EnterPlanModeTool,
            ExitPlanModeTool,
            AskUserTool,
            AgentTool,
            SleepTool,
            ConfigTool,
            BriefTool,
            EnterWorktreeTool,
            ExitWorktreeTool,
            REPLTool,
            ToolSearchTool,
            SkillTool,
            SendMessageTool,
            AnalyzeTool,
            PatchTool,
            MultiEditTool,
            WriteMemoryTool,
            DoneTool,
        ]:
            tool = cls()
            self._tools[tool.tool_def.name] = tool

    @property
    def tool_defs(self) -> list[dict]:
        return [t.tool_def.to_openai() for t in self._tools.values()]

    @property
    def tool_count(self) -> int:
        return len(self._tools)

    def execute(self, tool_name: str, arguments: dict[str, Any] | str) -> ActionResult:
        tool = self._tools.get(tool_name)
        if not tool:
            return ActionResult(success=False, error=f"Tool desconhecida: {tool_name}")

        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                return ActionResult(success=False, error=f"Argumentos inválidos (não é JSON): {arguments[:100]}")

        logger.info("[tool] %s(%s)", tool_name, str(arguments)[:80])

        block = self._hooks.run_pre(tool_name, arguments)
        if block and block.get("block"):
            reason = block.get("reason", "bloqueado por hook")
            return ActionResult(success=False, error=reason)

        result = tool.execute(arguments, self.project_root)
        self._hooks.run_post(tool_name, arguments, result)

        tag = "OK" if result.success else "ERRO"
        logger.info("[tool] %s -> %s (%s)", tool_name, tag, result.output[:60] if result.output else result.error[:60])
        return result

    def is_done(self, tool_name: str) -> bool:
        return tool_name == "done"

    @property
    def hooks(self) -> ToolHooks:
        return self._hooks


class McpToolAdapter(RegisteredTool):
    """Wrap de tool MCP em RegisteredTool nativo (MCP-SERVER-03).

    Mantém `action_type = ActionType.MCP_TOOL` para PermissionChecker
    aplicar política específica (default: always_confirm). Cada chamada
    executa asyncio.run(call_tool) — caminho síncrono dentro do
    ToolRegistry.execute. Tool MCP herda as mesmas garantias de hook
    pre/post das nativas via ToolRegistry.execute (sem bypass).
    """

    action_type = ActionType.MCP_TOOL

    def __init__(
        self,
        client: Any,
        server: Any,
        tool_def: dict[str, Any],
        name: str,
    ) -> None:
        self._client = client
        self._server = server
        self._tool_def_mcp = tool_def
        raw_schema = tool_def.get("inputSchema") if isinstance(tool_def, dict) else None
        if not isinstance(raw_schema, dict):
            raw_schema = {}
        properties = raw_schema.get("properties") if isinstance(raw_schema.get("properties"), dict) else {}
        required = raw_schema.get("required") if isinstance(raw_schema.get("required"), list) else []
        description = tool_def.get("description") or f"MCP tool {name}"
        self.tool_def = ToolDef(
            name=name,
            description=str(description),
            parameters=dict(properties),
            required=list(required),
        )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        del project_root  # tool MCP não usa cwd local
        raw_name = self._tool_def_mcp.get("name") if isinstance(self._tool_def_mcp, dict) else None
        if not raw_name:
            return ActionResult(success=False, error="MCP tool sem nome canônico")
        try:
            resp = asyncio.run(
                self._client.call_tool(self._server.name, raw_name, params or {})
            )
        except RuntimeError as e:
            # asyncio.run dentro de loop ativo: fallback explícito
            return ActionResult(success=False, error=f"MCP call dentro de loop ativo: {e}")
        except Exception as e:  # noqa: BLE001 -- erros MCP best-effort
            return ActionResult(success=False, error=f"MCP call falhou: {e}")
        if isinstance(resp, dict) and resp.get("error"):
            err = resp["error"]
            return ActionResult(success=False, error=f"MCP error: {err}")
        result = resp.get("result") if isinstance(resp, dict) else None
        output = json.dumps(result, ensure_ascii=False) if result is not None else ""
        return ActionResult(success=True, output=output)


# "O registro é a memória da máquina." -- Alan Turing
