"""Detecção inteligente de repetição para o AgentLoop.

Port de Luna src/skills/code_agent/repetition.py.

Três níveis de detecção:
1. Exact: mesma ação com mesmos parâmetros
2. Semantic: mesma ação no mesmo path (ignora params diferentes)
3. Cycle: detecta padrões A->B->A->B em janela de histórico
"""

from __future__ import annotations

from enum import Enum

from nyx.agent.services.logging_service import get_logger

from .models import ActionType, AgentAction
from .session import HistoryEntry

logger = get_logger("nyx.repetition")


class SkipStrategy(Enum):
    CONTINUE = "continue"
    SKIP = "skip"
    FORCE_DONE = "force_done"


def is_exact_repeat(
    action: AgentAction,
    last_action: AgentAction | None,
    key: str | None = None,
    last_key: str | None = None,
) -> bool:
    """Mesma ação com mesmos parâmetros.

    LOOP-ACTIONTYPE-FALLBACK-DONE-01: tools fora do enum ActionType (multi_edit,
    skill, task_*, ...) não têm valor canônico; o loop as identifica pelo `name`
    real (`key`/`last_key`). Sem isso, duas tools distintas colapsadas no mesmo
    rótulo opaco (ex.: MCP_TOOL) seriam confundidas como repetição exata. Quando
    `key` é None usa-se `action_type.value` (caminho canônico, comportamento da
    344 intocado: valor == identidade do enum).
    """
    if last_action is None:
        return False
    cur = key if key is not None else action.action_type.value
    prev = last_key if last_key is not None else last_action.action_type.value
    return prev == cur and last_action.params == action.params


def is_semantic_repeat(
    action: AgentAction,
    history: list[HistoryEntry],
    files_modified: set[str],
    key: str | None = None,
) -> bool:
    """Mesma ação no mesmo path (params podem diferir).

    `key` (LOOP-ACTIONTYPE-FALLBACK-DONE-01): nome real da tool para casar com
    `entry.tool_name` do histórico. Os casos especiais (CREATE/WRITE/READ/
    ANALYZE/SEARCH) seguem gateados pelo `action_type` canônico; tools fora do
    enum não têm path no topo (multi_edit usa `edits=[{file_path}]`) e caem no
    detector `is_in_recent`.
    """
    cur = key if key is not None else action.action_type.value
    if action.action_type in (ActionType.CREATE_FILE, ActionType.WRITE_FILE) and action.path:
        if action.path in files_modified:
            return True

    if not action.path:
        return False

    window = history[-5:] if len(history) >= 5 else history
    for entry in window:
        if not entry.tool_name:
            continue
        entry_path = entry.tool_args.get("path", entry.tool_args.get("file_path", ""))
        if entry.tool_name != cur:
            continue
        if entry_path == action.path:
            if action.action_type in (ActionType.READ_FILE, ActionType.ANALYZE):
                return True
            if action.action_type == ActionType.SEARCH:
                if entry.tool_args.get("pattern") == action.params.get("pattern"):
                    return True

    return False


def is_in_recent(
    action: AgentAction,
    history: list[HistoryEntry],
    window: int = 3,
    key: str | None = None,
) -> bool:
    """Verifica se ação idêntica ocorreu nas últimas N entradas.

    `key` (LOOP-ACTIONTYPE-FALLBACK-DONE-01): nome real da tool. O histórico
    guarda `tool_name` real (ex.: "multi_edit"); chavear por `action_type.value`
    (que para tools fora do enum era "done") nunca casava -- repetição real
    passava batido. Com `key` o nome real é comparado ao do histórico.
    """
    if len(history) < window:
        return False

    cur = key if key is not None else action.action_type.value
    new_key = (cur, tuple(sorted(action.params.items())))
    for entry in history[-window:]:
        if not entry.tool_name:
            continue
        entry_key = (entry.tool_name, tuple(sorted(entry.tool_args.items())))
        if new_key == entry_key:
            return True
    return False


def is_cycle(history: list[HistoryEntry], window: int = 6) -> bool:
    """Detecta padrões A->B->A->B em janela de histórico."""
    tool_entries = [e for e in history if e.tool_name]
    if len(tool_entries) < 4:
        return False

    recent = tool_entries[-window:] if len(tool_entries) >= window else tool_entries
    keys = [(e.tool_name, e.tool_args.get("path", e.tool_args.get("file_path", ""))) for e in recent]

    for cycle_len in (2, 3):
        if len(keys) < cycle_len * 2:
            continue
        tail = keys[-cycle_len:]
        prev = keys[-(cycle_len * 2) : -cycle_len]
        if tail == prev:
            logger.info("Ciclo detectado (len=%d): %s", cycle_len, tail)
            return True

    return False


def get_skip_strategy(
    action: AgentAction,
    last_action: AgentAction | None,
    history: list[HistoryEntry],
    files_modified: set[str],
    consecutive_skips: int,
    has_results: bool = False,
    force_done_threshold: int = 1,
    key: str | None = None,
    last_key: str | None = None,
) -> SkipStrategy:
    """Decide estratégia: continuar, pular ou forçar done.

    `key`/`last_key` (LOOP-ACTIONTYPE-FALLBACK-DONE-01): nome real da tool atual
    e da anterior, usados como chave de identidade para tools fora do enum
    ActionType. None => caminho canônico (chave = action_type.value), idêntico
    à 344.
    """
    if consecutive_skips >= 3:
        return SkipStrategy.FORCE_DONE

    if consecutive_skips >= force_done_threshold and has_results:
        return SkipStrategy.FORCE_DONE

    if is_cycle(history):
        return SkipStrategy.FORCE_DONE

    if is_exact_repeat(action, last_action, key=key, last_key=last_key):
        return SkipStrategy.SKIP

    if is_semantic_repeat(action, history, files_modified, key=key):
        return SkipStrategy.SKIP

    if is_in_recent(action, history, key=key):
        return SkipStrategy.SKIP

    return SkipStrategy.CONTINUE


def detect_repetition(
    action: AgentAction,
    last_action: AgentAction | None,
    history: list[HistoryEntry],
    files_modified: set[str],
    key: str | None = None,
    last_key: str | None = None,
) -> bool:
    """Atalho: retorna True se ação é repetida de qualquer forma."""
    return (
        is_exact_repeat(action, last_action, key=key, last_key=last_key)
        or is_semantic_repeat(action, history, files_modified, key=key)
        or is_in_recent(action, history, key=key)
    )


# "Insanidade é fazer a mesma coisa e esperar resultados diferentes." -- Rita Mae Brown
