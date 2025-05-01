"""Detecção inteligente de repetição para o AgentLoop.

Port de Luna src/skills/code_agent/repetition.py.

Três níveis de detecção:
1. Exact: mesma ação com mesmos parâmetros
2. Semantic: mesma ação no mesmo path (ignora params diferentes)
3. Cycle: detecta padrões A->B->A->B em janela de histórico
"""

from __future__ import annotations

import logging
from enum import Enum

from .models import ActionType, AgentAction
from .session import HistoryEntry

logger = logging.getLogger("nyx.repetition")


class SkipStrategy(Enum):
    CONTINUE = "continue"
    SKIP = "skip"
    FORCE_DONE = "force_done"


def is_exact_repeat(action: AgentAction, last_action: AgentAction | None) -> bool:
    """Mesma ação com mesmos parâmetros."""
    if last_action is None:
        return False
    return last_action.action_type == action.action_type and last_action.params == action.params


def is_semantic_repeat(
    action: AgentAction,
    history: list[HistoryEntry],
    files_modified: set[str],
) -> bool:
    """Mesma ação no mesmo path (params podem diferir)."""
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
        if entry.tool_name != action.action_type.value:
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
) -> bool:
    """Verifica se ação idêntica ocorreu nas últimas N entradas."""
    if len(history) < window:
        return False

    new_key = (action.action_type.value, tuple(sorted(action.params.items())))
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
        prev = keys[-(cycle_len * 2):-cycle_len]
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
) -> SkipStrategy:
    """Decide estratégia: continuar, pular ou forçar done."""
    if consecutive_skips >= 3:
        return SkipStrategy.FORCE_DONE

    if consecutive_skips >= force_done_threshold and has_results:
        return SkipStrategy.FORCE_DONE

    if is_cycle(history):
        return SkipStrategy.FORCE_DONE

    if is_exact_repeat(action, last_action):
        return SkipStrategy.SKIP

    if is_semantic_repeat(action, history, files_modified):
        return SkipStrategy.SKIP

    if is_in_recent(action, history):
        return SkipStrategy.SKIP

    return SkipStrategy.CONTINUE


def detect_repetition(
    action: AgentAction,
    last_action: AgentAction | None,
    history: list[HistoryEntry],
    files_modified: set[str],
) -> bool:
    """Atalho: retorna True se ação é repetida de qualquer forma."""
    return (
        is_exact_repeat(action, last_action)
        or is_semantic_repeat(action, history, files_modified)
        or is_in_recent(action, history)
    )


# "Insanidade é fazer a mesma coisa e esperar resultados diferentes." -- Rita Mae Brown
