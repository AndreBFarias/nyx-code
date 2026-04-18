"""Interface base para tools do Nyx Agent."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType

logger = logging.getLogger("nyx.tools.base")

MAX_FILE_SIZE = 1_048_576  # 1 MB

_NYX_DATA_DIR = Path.home() / ".nyx"

_ALLOWED_ROOTS: list[Path] | None = None


def _get_allowed_roots(project_root: str) -> list[Path]:
    """Retorna raízes permitidas para acesso a arquivos."""
    global _ALLOWED_ROOTS
    if _ALLOWED_ROOTS is None or _ALLOWED_ROOTS[0] != Path(project_root).resolve():
        _ALLOWED_ROOTS = [
            Path(project_root).resolve(),
            _NYX_DATA_DIR.resolve(),
        ]
    return _ALLOWED_ROOTS


def validate_path(file_path: str, project_root: str) -> Path:
    """Valida e resolve path, bloqueando traversal fora do projeto.

    Paths permitidos:
    - Dentro de project_root (relativo ou absoluto)
    - Dentro de ~/.nyx/ (dados do agente)

    Paths bloqueados:
    - Qualquer path que resolva para fora dessas raízes
    - Symlinks cujo target está fora das raízes permitidas

    Raises:
        ValueError: se o path está fora das raízes permitidas.
    """
    if not file_path or not file_path.strip():
        raise ValueError("Path vazio")

    raw = Path(file_path.strip())
    if raw.is_absolute():
        resolved = raw.resolve()
    else:
        resolved = (Path(project_root) / raw).resolve()

    allowed = _get_allowed_roots(project_root)
    for root in allowed:
        try:
            resolved.relative_to(root)
            logger.debug("Path validado: %s -> %s (raiz: %s)", file_path, resolved, root)
            return resolved
        except ValueError:
            continue

    logger.warning("Path bloqueado por traversal: %s -> %s", file_path, resolved)
    project_name = Path(project_root).name or "projeto"
    raise ValueError(f"Fora do projeto {project_name}: '{file_path}'. Para acessar outro projeto, inicie o Nyx lá.")


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
    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult: ...


# "A abstração é a arma mais poderosa do programador." -- Edsger Dijkstra
