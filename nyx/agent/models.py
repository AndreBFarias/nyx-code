"""Modelos de dados do Nyx Agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionType(Enum):
    READ_FILE = "read_file"
    CREATE_FILE = "create_file"
    WRITE_FILE = "write_file"
    EDIT_FILE = "edit_file"
    RUN_COMMAND = "run_command"
    GLOB = "glob"
    SEARCH = "search"
    LIST_FILES = "list_files"
    ANALYZE = "analyze"
    PATCH = "patch"
    REPL = "repl"
    TODO_WRITE = "todo_write"
    WEB_FETCH = "web_fetch"
    WEB_SEARCH = "web_search"
    WRITE_MEMORY = "write_memory"
    MCP_TOOL = "mcp_tool"
    DONE = "done"


class ParseLevel(Enum):
    EXACT = "exact"
    FUNCTION_CALL = "function_call"
    RELAXED = "relaxed"
    BARE_TOOL = "bare_tool"
    CODE_BLOCK = "code_block"
    PATH_INTENT = "path_intent"
    IMPLICIT_DONE = "implicit_done"


class SessionState(Enum):
    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    MAX_ITERATIONS = "max_iterations"
    CANCELLED = "cancelled"


@dataclass
class AgentAction:
    action_type: ActionType
    params: dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""
    raw_block: str = ""

    @property
    def path(self) -> str:
        return self.params.get("path", self.params.get("file_path", ""))


@dataclass
class ParseResult:
    action: AgentAction | None
    level: ParseLevel
    success: bool
    error: str = ""
    raw_text: str = ""


@dataclass
class ActionResult:
    success: bool
    output: str = ""
    error: str = ""
    files_read: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)


@dataclass
class SessionStatus:
    state: SessionState
    iterations: int = 0
    summary: str = ""


# "Nomear é conhecer." -- Confúcio
