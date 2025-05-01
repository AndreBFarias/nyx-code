"""Session -- Estado da conversa do agent.

Port de Luna src/skills/code_agent/session.py.
Mantém histórico, arquivos lidos/modificados, e métodos de compactação
para o ContextBudget (P1-B).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class HistoryEntry:
    role: str
    content: str
    tool_name: str = ""
    tool_args: dict[str, Any] = field(default_factory=dict)
    tool_result: str = ""
    is_key_decision: bool = False

    def compress(self) -> str:
        """Versão compacta (últimas N entradas no nível 1)."""
        if self.tool_name:
            result_preview = self.tool_result[:200] if self.tool_result else ""
            return f"[{self.tool_name}] {str(self.tool_args)[:80]} -> {result_preview}"
        return self.content[:300]

    def ultra_compact(self) -> str:
        """Versão ultra-compacta (entradas antigas no nível 1+)."""
        if self.tool_name:
            return f"[{self.tool_name}] {self.tool_args.get('path', self.tool_args.get('file_path', ''))}"
        return self.content[:80]


class CodeSession:
    def __init__(self) -> None:
        self.history: list[HistoryEntry] = []
        self.iteration: int = 0
        self._files_read: set[str] = set()
        self._files_modified: set[str] = set()

    def add_user(self, content: str) -> None:
        self.history.append(HistoryEntry(role="user", content=content))

    def add_assistant(self, content: str) -> None:
        self.history.append(HistoryEntry(role="assistant", content=content))

    def add_tool_call(self, tool_name: str, args: dict[str, Any], result: str,
                      is_key: bool = False) -> None:
        self.history.append(HistoryEntry(
            role="tool",
            content=result[:4000],
            tool_name=tool_name,
            tool_args=args,
            tool_result=result[:4000],
            is_key_decision=is_key,
        ))

    def track_files(self, files_read: list[str], files_modified: list[str]) -> None:
        self._files_read.update(files_read)
        self._files_modified.update(files_modified)

    def to_messages(self) -> list[dict[str, str]]:
        """Converte histórico para formato de mensagens do LLM."""
        msgs: list[dict[str, str]] = []
        for entry in self.history:
            if entry.role == "tool":
                msgs.append({"role": "user",
                             "content": f"[resultado de {entry.tool_name}]\n{entry.tool_result}"})
            else:
                msgs.append({"role": entry.role, "content": entry.content})
        return msgs

    # ── Métodos de compactação (usados pelo ContextBudget) ───────────

    def get_full_history(self) -> list[HistoryEntry]:
        return list(self.history)

    def get_compressed_history(self) -> str:
        """Histórico comprimido para estimativa de tokens."""
        parts = [entry.compress() for entry in self.history]
        return "\n".join(parts)

    def get_key_decisions(self) -> list[str]:
        """Decisões importantes (tool calls que modificaram arquivos)."""
        decisions = []
        for entry in self.history:
            if entry.is_key_decision:
                decisions.append(entry.compress())
            elif entry.tool_name and entry.tool_name in ("write_file", "edit_file", "create_file", "run_command"):
                decisions.append(entry.compress())
        return decisions

    def get_files_context(self) -> str:
        """Contexto de arquivos lidos e modificados."""
        parts = []
        if self._files_read:
            parts.append(f"Lidos: {', '.join(sorted(self._files_read)[:10])}")
        if self._files_modified:
            parts.append(f"Modificados: {', '.join(sorted(self._files_modified)[:10])}")
        return " | ".join(parts)

    # ── Propriedades ─────────────────────────────────────────────────

    @property
    def files_read_count(self) -> int:
        return len(self._files_read)

    @property
    def files_modified_count(self) -> int:
        return len(self._files_modified)

    def reset(self) -> None:
        self.history.clear()
        self.iteration = 0
        self._files_read.clear()
        self._files_modified.clear()


# "O contexto é tudo." -- Wittgenstein
