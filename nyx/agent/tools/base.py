"""Interface base para tools do Nyx Agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from nyx.agent.models import ActionResult, ActionType


@dataclass
class ToolDef:
    """Definição de tool para o LLM (formato function calling)."""

    name: str
    description: str
    parameters: dict[str, Any]
    required: list[str]

    def to_openai(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": self.parameters,
                    "required": self.required,
                },
            },
        }


class RegisteredTool(ABC):
    action_type: ActionType
    tool_def: ToolDef

    @abstractmethod
    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        ...


# "A abstração é a arma mais poderosa do programador." -- Edsger Dijkstra
