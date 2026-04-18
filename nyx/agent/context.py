"""Context Manager -- Compactação progressiva e token budgeting.

Port de Luna src/skills/code_agent/context_manager.py.

4 níveis de compactação:
  Nível 0 (< 40% budget): Histórico completo
  Nível 1 (40-60% budget): Últimas 3 entradas full + resto ultra-compact
  Nível 2 (60-85% budget): Apenas key_decisions + files_context
  Nível 3 (> 85% budget): Truncar agressivamente + warning
"""

from __future__ import annotations

import logging

from .session import CodeSession, HistoryEntry

logger = logging.getLogger("nyx.context")

DEFAULT_MAX_TOKENS = 12000
MAX_PARTIAL_ENTRIES = 8
COMPACT_RECENT = 3

LEVEL_THRESHOLDS = (0.4, 0.6, 0.85)


def estimate_tokens(text: str) -> int:
    """Heurística: ~4 chars por token (rápido, sem dependência)."""
    return len(text) // 4


class ContextBudget:
    def __init__(self, max_tokens: int = DEFAULT_MAX_TOKENS) -> None:
        self.max_tokens = max_tokens
        self._last_pct = 0.0
        self._compactions = 0

    def estimate(self, system: str, user: str) -> dict:
        system_tokens = estimate_tokens(system)
        user_tokens = estimate_tokens(user)
        total = system_tokens + user_tokens
        pct = total / self.max_tokens if self.max_tokens > 0 else 0.0
        self._last_pct = pct

        if pct > 1.0:
            logger.warning(
                "[CONTEXT] Budget ESTOURADO: %d/%d tokens (%.0f%%). System: %d, User: %d",
                total, self.max_tokens, pct * 100, system_tokens, user_tokens,
            )
        elif pct > 0.85:
            logger.info("[CONTEXT] Budget alto: %.0f%% (%d/%d)", pct * 100, total, self.max_tokens)

        return {
            "system_tokens": system_tokens,
            "user_tokens": user_tokens,
            "total_tokens": total,
            "max_tokens": self.max_tokens,
            "pct": min(pct, 1.0),
            "warning": pct > 0.7,
            "overflow": pct > 1.0,
        }

    def _history_pct(self, session: CodeSession) -> float:
        history = session.get_compressed_history()
        history_tokens = estimate_tokens(history)
        if self.max_tokens <= 0:
            return 0.0
        return history_tokens / self.max_tokens

    def get_compaction_level(self, session: CodeSession) -> int:
        pct = self._history_pct(session)
        if pct < LEVEL_THRESHOLDS[0]:
            return 0
        if pct < LEVEL_THRESHOLDS[1]:
            return 1
        if pct < LEVEL_THRESHOLDS[2]:
            return 2
        return 3

    def should_compact(self, session: CodeSession) -> bool:
        return self._history_pct(session) > LEVEL_THRESHOLDS[0]

    def compact_history(self, session: CodeSession) -> str:
        level = self.get_compaction_level(session)
        self._compactions += 1

        if level == 0:
            return session.get_compressed_history()
        if level == 1:
            return self._compact_partial(session.get_full_history())
        if level == 2:
            return self._compact_heavy(session)
        return self._compact_emergency(session)

    def _compact_partial(self, history: list[HistoryEntry]) -> str:
        if not history:
            return ""

        parts: list[str] = []

        if len(history) > COMPACT_RECENT:
            older = history[:-COMPACT_RECENT]
            visible = older[-MAX_PARTIAL_ENTRIES:]
            omitted = len(older) - len(visible)
            if omitted > 0:
                parts.append(f"[{omitted} ações omitidas]")
            for entry in visible:
                parts.append(entry.ultra_compact())

        recent = history[-COMPACT_RECENT:]
        for entry in recent:
            parts.append(entry.compress())

        return "\n".join(parts)

    def _compact_heavy(self, session: CodeSession) -> str:
        decisions = session.get_key_decisions()
        files_ctx = session.get_files_context()
        summary = getattr(session, "summary", "")

        parts: list[str] = []
        if summary:
            parts.append(f"[RESUMO]\n{summary}")
        if decisions:
            parts.append("Decisões: " + "; ".join(decisions[-5:]))
        if files_ctx:
            parts.append(files_ctx)

        return "\n".join(parts) if parts else ""

    def _compact_emergency(self, session: CodeSession) -> str:
        """Nível 3: truncar agressivamente."""
        logger.warning("[CONTEXT] Compactação de emergência (nível 3, %d compactações)", self._compactions)

        decisions = session.get_key_decisions()
        last_decision = decisions[-1] if decisions else ""

        history = session.get_full_history()
        last_entry = history[-1].ultra_compact() if history else ""
        summary = getattr(session, "summary", "")

        parts = []
        if summary:
            parts.append(f"[RESUMO]\n{summary}")
        elif last_decision:
            parts.append(f"[RESUMO] {last_decision}")
        if last_entry:
            parts.append(last_entry)

        result = "\n".join(parts)
        max_chars = self.max_tokens * 2
        if len(result) > max_chars:
            result = result[:max_chars] + "\n[... truncado por emergência]"

        return result


def render_context_bar(budget: dict, width: int = 20) -> str:
    """Barra visual de uso do budget."""
    pct = budget.get("pct", 0.0)
    filled = int(pct * width)
    empty = width - filled

    bar = "|" * filled + " " * empty
    pct_display = f"{pct:.0%}"

    return f"[{bar}] ctx: {pct_display}"


# "Medir é o primeiro passo para controlar." -- H. James Harrington
