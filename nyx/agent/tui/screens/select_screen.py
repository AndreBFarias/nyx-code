"""SelectScreen -- ModalScreen Textual para seleção entre N opções.

Substitui radiolist_dialog do prompt_toolkit usado em cli_boot.run_select_modal
para aesthetic_select, theme_select, schema_select.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class SelectScreen(ModalScreen[str]):
    """Modal de seleção de opção.

    Uso:
        selected = await self.push_screen_wait(
            SelectScreen("Escolha o tema", [("dark", "Escuro"), ("light", "Claro")])
        )
        # selected vem como str (value) ou None (ESC cancelou)
    """

    DEFAULT_CSS = """
    SelectScreen { align: center middle; }
    SelectScreen > Container {
        width: 60%;
        max-width: 80;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: heavy $accent;
        padding: 1 2;
    }
    SelectScreen Vertical { height: auto; }
    SelectScreen #modal-title {
        color: $accent;
        text-style: bold;
        margin: 0 0 1 0;
    }
    SelectScreen Button {
        width: 100%;
        margin: 0 0 1 0;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancelar", priority=True),
    ]

    def __init__(self, title: str, options: list[tuple[str, str]]) -> None:
        super().__init__()
        self._title = title
        self._options = options

    def compose(self) -> ComposeResult:
        with Container():
            with Vertical():
                yield Static(self._title, id="modal-title")
                for value, label in self._options:
                    yield Button(label, id=f"opt-{value}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id is None:
            return
        value = event.button.id.removeprefix("opt-")
        self.dismiss(value)

    def action_cancel(self) -> None:
        self.dismiss(None)


__all__ = ["SelectScreen"]
