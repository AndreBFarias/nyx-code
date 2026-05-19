"""Interface base para tools do Nyx Agent."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.tools.base")

MAX_FILE_SIZE = 1_048_576  # 1 MB

_NYX_DATA_DIR = Path.home() / ".nyx"

# PROJECT-ROOTS-MULTI-01: roots permitidos em runtime.
#
# _ACTIVE_ROOT começa None e é populado na primeira chamada a
# _get_allowed_roots() pelo project_root recebido (compat com chamadas
# antigas). Pode ser trocado em runtime via set_active_project_root()
# quando o usuário invoca /cd <path>.
#
# _EXTRA_ROOTS é populado por add_extra_root() (via /sandbox add ou env
# NYX_EXTRA_ROOTS no boot). Sessão-only por design -- persistência via
# ~/.nyx/config.toml é opt-in do usuário (não toca aqui).
_ACTIVE_ROOT: Path | None = None
_EXTRA_ROOTS: list[Path] = []


def _resolve(p: str | Path) -> Path:
    return Path(p).expanduser().resolve()


def set_active_project_root(path: str | Path) -> Path:
    """Troca o project_root corrente da sessão (handler de /cd).

    Se o novo root coincide com algum extra anteriormente autorizado, o
    extra é removido (evita listagem duplicada). O chamador (cli.py)
    registra o root antigo via add_extra_root() APÓS esta chamada para
    preservar acesso ao projeto original.
    """
    global _ACTIVE_ROOT
    new_root = _resolve(path)
    if new_root in _EXTRA_ROOTS:
        _EXTRA_ROOTS.remove(new_root)
    _ACTIVE_ROOT = new_root
    logger.info("active project_root trocado para %s", _ACTIVE_ROOT)
    return _ACTIVE_ROOT


def add_extra_root(path: str | Path) -> Path:
    """Adiciona root permitido (handler de /sandbox add).

    Idempotente: paths já presentes não são duplicados. Retorna o Path
    resolvido (canonical).
    """
    target = _resolve(path)
    if target in _EXTRA_ROOTS:
        return target
    if _ACTIVE_ROOT is not None and target == _ACTIVE_ROOT:
        return target
    _EXTRA_ROOTS.append(target)
    logger.info("extra root adicionado: %s", target)
    return target


def remove_extra_root(path: str | Path) -> bool:
    """Remove root extra (handler de /sandbox remove).

    Retorna True se removido, False se não estava na lista. project_root
    ativo NÃO pode ser removido por esta função (cli.py valida antes).
    """
    target = _resolve(path)
    if target in _EXTRA_ROOTS:
        _EXTRA_ROOTS.remove(target)
        logger.info("extra root removido: %s", target)
        return True
    return False


def list_extra_roots() -> list[Path]:
    """Retorna cópia da lista de extras (handler de /sandbox list)."""
    return list(_EXTRA_ROOTS)


def get_active_project_root() -> Path | None:
    """Retorna project_root corrente (None se ainda não inicializado)."""
    return _ACTIVE_ROOT


def _get_allowed_roots(project_root: str) -> list[Path]:
    """Retorna raízes permitidas para acesso a arquivos.

    Ordem: [project_root ativo, ~/.nyx, *extras].
    project_root recebido só é usado se _ACTIVE_ROOT ainda não foi setado.
    """
    global _ACTIVE_ROOT
    if _ACTIVE_ROOT is None:
        _ACTIVE_ROOT = _resolve(project_root)
    roots: list[Path] = [_ACTIVE_ROOT, _NYX_DATA_DIR.resolve()]
    roots.extend(_EXTRA_ROOTS)
    return roots


def validate_path(file_path: str, project_root: str) -> Path:
    """Valida e resolve path, bloqueando traversal fora dos roots permitidos.

    Paths permitidos:
    - Dentro de project_root ativo (relativo ou absoluto)
    - Dentro de ~/.nyx/ (dados do agente)
    - Dentro de qualquer extra_root adicionado via /sandbox add ou
      NYX_EXTRA_ROOTS (PROJECT-ROOTS-MULTI-01)

    Paths bloqueados:
    - Qualquer path que resolva para fora dessas raízes
    - Symlinks cujo target está fora das raízes permitidas

    Raises:
        ValueError: se o path está fora das raízes permitidas. Mensagem
        em PT-BR sugere o comando exato (/sandbox add <root>) para
        autorizar -- output.py já tem ação correspondente registrada.
    """
    if not file_path or not file_path.strip():
        raise ValueError("Path vazio")

    raw = Path(file_path.strip())
    if raw.is_absolute():
        resolved = raw.resolve()
    else:
        # Caminho relativo: usa _ACTIVE_ROOT se já inicializado, senão
        # cai no project_root recebido (boot inicial).
        base = _ACTIVE_ROOT if _ACTIVE_ROOT is not None else _resolve(project_root)
        resolved = (base / raw).resolve()

    allowed = _get_allowed_roots(project_root)
    for root in allowed:
        try:
            resolved.relative_to(root)
            logger.debug("Path validado: %s -> %s (raiz: %s)", file_path, resolved, root)
            return resolved
        except ValueError:
            continue

    logger.warning("Path bloqueado por traversal: %s -> %s", file_path, resolved)
    # PROJECT-ROOTS-MULTI-01: mensagem actionable cita /sandbox add com o
    # path-pai (parent) inferido para reduzir atrito do usuário.
    suggest = resolved.parent if resolved.parent != resolved else resolved
    raise ValueError(
        f"Fora dos projetos permitidos: '{file_path}'. "
        f"Para autorizar: /sandbox add {suggest}"
    )


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
