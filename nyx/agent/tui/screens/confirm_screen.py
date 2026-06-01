"""ConfirmScreen -- modal de confirmação de ação (TUI-PERMISSION-CONFIRM-01, ONDA-37).

Pergunta ao usuário ANTES de a Nyx executar uma tool que altera (write/edit/run) no
modo Normal -- "vai por x ou y?", como um CLI de código moderno. Padrão do SelectScreen. Retorna
True (aprovado) / False (negado) via `dismiss`, consumido por `push_screen_wait` no
callback `_on_agent_permission` da NyxTUI.

Modelo do dono (ONDA-37): perguntar antes de alterar é o comportamento BASE; o Bypass
desliga (auto-aprova, nunca chega aqui), o Plan bloqueia a escrita antes (no loop).
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class ConfirmScreen(ModalScreen[bool]):
    """Modal Sim/Não. `dismiss(True)` aprova, `dismiss(False)` nega (ESC = nega)."""

    DEFAULT_CSS = """
    ConfirmScreen { align: center middle; }
    ConfirmScreen > Container {
        width: 70%;
        max-width: 90;
        height: auto;
        background: $surface;
        border: heavy $accent;
        padding: 1 2;
    }
    ConfirmScreen Vertical { height: auto; }
    ConfirmScreen Horizontal { height: auto; align: center middle; }
    ConfirmScreen #confirm-title { color: $accent; text-style: bold; margin: 0 0 1 0; }
    ConfirmScreen #confirm-detail { color: $foreground; margin: 0 0 1 0; }
    ConfirmScreen Button { margin: 0 1; }
    """

    BINDINGS = [
        Binding("escape", "deny", "Negar", priority=True),
        Binding("s", "approve", "Sim"),
        Binding("n", "deny", "Nao"),
    ]

    def __init__(self, action: str, detail: str = "") -> None:
        super().__init__()
        self._action = action
        self._detail = detail

    def compose(self) -> ComposeResult:
        with Container():
            with Vertical():
                yield Static(f"A Nyx quer executar: {self._action}", id="confirm-title")
                if self._detail:
                    yield Static(self._detail, id="confirm-detail")
                with Horizontal():
                    yield Button("Aprovar (s)", id="confirm-yes", variant="success")
                    yield Button("Negar (n)", id="confirm-no", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-yes")

    def action_approve(self) -> None:
        self.dismiss(True)

    def action_deny(self) -> None:
        self.dismiss(False)


__all__ = ["ConfirmScreen"]
