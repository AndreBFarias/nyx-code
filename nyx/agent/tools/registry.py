"""ToolRegistry -- Carrega e executa tools do Nyx Agent."""

from __future__ import annotations

import json
from typing import Any

from nyx.agent.models import ActionResult
from nyx.agent.services.hooks import ToolHooks
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import RegisteredTool

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


# "O registro é a memória da máquina." -- Alan Turing
