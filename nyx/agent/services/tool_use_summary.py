"""ToolUseSummary -- Acumula e resume uso de tools por sessão."""

from __future__ import annotations

from collections import Counter

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.services.tool_use_summary")


class ToolUseSummary:
    """Acumula tool calls e gera resumo da sessão."""

    def __init__(self) -> None:
        self._calls: list[tuple[str, dict]] = []
        self._counter: Counter = Counter()

    def track(self, tool_name: str, args: dict | None = None) -> None:
        self._calls.append((tool_name, args or {}))
        self._counter[tool_name] += 1

    def get_summary(self) -> str:
        if not self._calls:
            return "Nenhuma tool usada."
        lines = [f"  Tools usadas ({len(self._calls)} chamadas):"]
        for name, count in self._counter.most_common(10):
            lines.append(f"    {name}: {count}x")
        return "\n".join(lines)

    @property
    def total_calls(self) -> int:
        return len(self._calls)

    @property
    def unique_tools(self) -> int:
        return len(self._counter)

    def reset(self) -> None:
        self._calls.clear()
        self._counter.clear()

    def status(self) -> dict:
        return {
            "service": "tool_use_summary",
            "ativo": True,
            "total_calls": self.total_calls,
            "unique_tools": self.unique_tools,
            "top_3": self._counter.most_common(3),
        }


# "A ordem é o primeiro passo para a liberdade." -- Aristóteles
