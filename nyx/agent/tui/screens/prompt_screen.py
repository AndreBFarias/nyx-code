"""PromptScreen -- ModalScreen Textual para uma resposta de texto livre.

Usada pelo ask_user (nyx/agent/tools/ask_user.py) quando a pergunta não tem
options. Espelha select_screen.py; substitui o input() bloqueante do REPL
(cli_callbacks.py:101) por um modal async compativel com o event loop do Textual.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Input, Static


class PromptScreen(ModalScreen[str]):
    """Modal de resposta em texto livre.

    Uso:
        answer = await self.push_screen_wait(PromptScreen("Qual o nome do modulo?"))
        # answer vem como str (texto) ou None (ESC cancelou)
    """

    DEFAULT_CSS = """
    PromptScreen { align: center middle; }
    PromptScreen > Container {
        width: 60%;
        max-width: 80;
        height: auto;
        background: $surface;
        border: heavy $accent;
        padding: 1 2;
    }
    PromptScreen Vertical { height: auto; }
    PromptScreen #modal-title {
        color: $accent;
        text-style: bold;
        margin: 0 0 1 0;
    }
    PromptScreen Input { width: 100%; }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancelar", priority=True),
    ]

    def __init__(self, title: str) -> None:
        super().__init__()
        self._title = title

    def compose(self) -> ComposeResult:
        with Container():
            with Vertical():
                yield Static(self._title, id="modal-title")
                yield Input(placeholder="Resposta...", id="prompt-input")

    def on_mount(self) -> None:
        self.query_one("#prompt-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self.dismiss(event.value.strip())

    def action_cancel(self) -> None:
        self.dismiss(None)


__all__ = ["PromptScreen"]
