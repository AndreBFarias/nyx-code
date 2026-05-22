"""OutputWidget -- rolling log de mensagens user/assistant/tool da TUI Textual.

ONDA-30 sub-sprint 198. Substituirá a renderização atual de output via
nyx.agent.output._emit (prompt_toolkit) após TEXTUAL-CUTOVER-01.

Por enquanto, é widget isolado: importável, testável, não composto no
NyxTUI ainda.

Tokens de cor importados de nyx.themes.design_tokens (UX-DESIGN-01):
fonte única de hex para satisfazer invariante #6 de sprint_invariants.sh.
"""

from __future__ import annotations

from rich.text import Text
from textual.widgets import RichLog

from nyx.themes.design_tokens import NYX_ACCENT, NYX_PURPLE


class OutputWidget(RichLog):
    """Rolling log de mensagens user/assistant/tool.

    Métodos públicos:
      - write_user(text): append de input do usuário (turquesa NYX_ACCENT).
      - write_assistant(text): append de resposta do modelo (roxo NYX_PURPLE).
      - write_tool(name, args, result=None): append de tool call/result (dim).

    O widget usa o RichLog do Textual que gerencia scroll automático e
    rendering otimizado por linha (sem invalidate global como prompt_toolkit).

    Paleta canônica (ADR-023): turquesa + roxo + dim/muted via design_tokens.
    """

    DEFAULT_CSS = """
    OutputWidget {
        height: 1fr;
        background: $surface;
    }
    """

    def write_user(self, text: str) -> None:
        """Append de input do usuário em turquesa."""
        msg = Text()
        msg.append("> ", style=f"bold {NYX_ACCENT}")
        msg.append(text, style=NYX_ACCENT)
        self.write(msg)

    def write_assistant(self, text: str) -> None:
        """Append de resposta do modelo em roxo."""
        msg = Text(text, style=NYX_PURPLE)
        self.write(msg)

    def write_tool(self, name: str, args: str = "", result: str | None = None) -> None:
        """Append de tool call/result em dim/muted. Result é opcional."""
        msg = Text()
        msg.append("  ", style="dim")
        msg.append(name, style="bold dim")
        if args:
            msg.append(f"({args})", style="dim")
        if result is not None:
            msg.append(f" -> {result}", style="dim italic")
        self.write(msg)


__all__ = ["OutputWidget"]
