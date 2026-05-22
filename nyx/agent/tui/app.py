"""App principal Textual do Nyx-Code (placeholder ONDA-30 SCAFFOLD).

Esta classe é o ponto de entrada Textual que substituirá repl_app.py
após a sub-sprint TEXTUAL-CUTOVER-01. Por ora, é apenas scaffold — sem
widgets, sem bindings, sem lifecycle.

Validação:
    from nyx.agent.tui.app import NyxTUI
    assert issubclass(NyxTUI, textual.app.App)
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App


class NyxTUI(App):
    """Placeholder ONDA-30 SCAFFOLD.

    Sub-sprints filhas adicionam features:
      - TEXTUAL-OUTPUT-WIDGET-01: OutputWidget(RichLog).
      - TEXTUAL-INPUT-WIDGET-01: InputWidget(Input) ancorado no rodapé.
      - TEXTUAL-BANNER-WIDGET-01: BannerWidget(Static) com timer blink.
      - TEXTUAL-TOOLBAR-01: Toolbar(Static) com reactive properties.
      - TEXTUAL-CUTOVER-01: bindings + dispatch via cli.
    """

    CSS_PATH = Path(__file__).parent / "styles" / "nyx.tcss"

    BINDINGS: list = []

    async def on_mount(self) -> None:
        """Mount placeholder — features virão das sub-sprints filhas."""
        return None


__all__ = ["NyxTUI"]
