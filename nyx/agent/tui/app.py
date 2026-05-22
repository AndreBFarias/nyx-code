"""NyxTUI -- App Textual principal compondo os 4 widgets da ONDA-30.

Compose:
  - BannerWidget (top, com cursor blink local).
  - OutputWidget (middle, rolling log).
  - Toolbar (bottom-1, status).
  - InputWidget (bottom, prompt ancorado).

Bindings:
  - Ctrl+Q: quit (paridade sprint 188).
  - Ctrl+D: quit_if_empty (paridade sprint 189).
  - Shift+Tab: cycle_mode (paridade SHIFT-TAB-CYCLE-01).
  - Ctrl+V: paste (paridade VISION-02).
  - Ctrl+O: recall_last_input (paridade UX-EXTRA-01).

Dispatch:
  - Default: NUNCA dispatched (CLI continua usando repl_app.py).
  - Opt-in: env NYX_TUI_TEXTUAL=1 em cli.py dispara branch dedicado.

Sub-sprint TEXTUAL-CUTOVER-01 da ONDA-30. Integração com Agent loop
fica para sub-sprint ONDA-31 (cutover real). Por enquanto _on_input_submit
apenas registra o texto no OutputWidget; a sprint atual entrega a UI shell
estável e o dispatch opt-in.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding

from nyx.agent.tui.widgets.banner import BannerWidget
from nyx.agent.tui.widgets.input import InputWidget
from nyx.agent.tui.widgets.output import OutputWidget
from nyx.agent.tui.widgets.toolbar import Toolbar


class NyxTUI(App):
    """App Textual principal -- sub-sprint TEXTUAL-CUTOVER-01.

    Composição em quatro widgets que reproduzem a estrutura visual da
    REPL prompt_toolkit existente. Ordem de yield definida pelo spec
    (Banner, Output, Toolbar, Input). O empilhamento final do layout
    é governado pelo CSS (`dock: bottom` em Input/Toolbar; `height: 1fr`
    em Output) -- compose() apenas registra os filhos.
    """

    CSS_PATH = Path(__file__).parent / "styles" / "nyx.tcss"

    # priority=True garante que o App captura o key event antes do widget
    # focado (InputWidget consome shift+tab/ctrl+v/ctrl+o por padrão). Sem
    # priority, atalhos globais ficam refens do focus -- comportamento
    # incompatível com a paridade prompt_toolkit dos sprints 188-189 e
    # SHIFT-TAB-CYCLE-01.
    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
        Binding("ctrl+d", "quit_if_empty", "Quit (EOF)", priority=True),
        Binding("shift+tab", "cycle_mode", "Trocar modo", priority=True),
        Binding("ctrl+v", "paste", "Colar", priority=True),
        Binding("ctrl+o", "recall_last", "Recall último input", priority=True),
    ]

    # Atenção: `App.MODES` em Textual é dict[str, Screen] -- redefinir como
    # tupla aqui colide com a metaclasse e crasha em class-creation. Mantemos
    # o ciclo de modos em um atributo distinto.
    MODE_CYCLE = ("normal", "plan", "sudo", "bypass")

    def __init__(
        self,
        *,
        model: str = "qwen2.5-coder:3b",
        tools_count: int = 35,
        project_name: str = "Nyx-Code",
        slash_completer: list[str] | None = None,
        settings: Any = None,
    ) -> None:
        super().__init__()
        self._model = model
        self._tools_count = tools_count
        self._project_name = project_name
        self._slash_completer = slash_completer or []
        self._settings = settings
        self._mode_idx = 0
        self._last_input: str = ""

    def compose(self) -> ComposeResult:
        """Yield Banner, Output, Toolbar, Input nessa ordem.

        BannerWidget e Toolbar não aceitam `id=` no construtor (não
        repassam ao super). Atribuímos `.id` após instanciar -- atributo
        público herdado de `textual.widget.Widget`.
        """
        banner = BannerWidget(
            model=self._model,
            tools_count=self._tools_count,
            project_name=self._project_name,
            settings=self._settings,
        )
        banner.id = "banner"
        yield banner

        output = OutputWidget(id="output")
        yield output

        toolbar = Toolbar(model=self._model)
        toolbar.id = "toolbar"
        yield toolbar

        yield InputWidget(
            id="input",
            slash_completer=self._slash_completer,
            on_submit=self._on_input_submit,
        )

    def _on_input_submit(self, text: str) -> None:
        """Callback do InputWidget.

        Por enquanto apenas registra o input no OutputWidget e guarda o
        último valor para recall via Ctrl+O. Integração com Agent loop
        fica para sub-sprint ONDA-31.
        """
        if not text.strip():
            return
        self._last_input = text
        output = self.query_one("#output", OutputWidget)
        output.write_user(text)

    async def action_quit(self) -> None:
        """Ctrl+Q: fecha app via Application.exit(result=__quit__).

        Paridade sprint 188: cli.py reconhece o sentinel `__quit__` e
        dispara `render_quit_card` + `run_quit_shutdown`. A integração
        completa (chamada explícita do shutdown_repl) será feita quando
        ONDA-31 fizer o cutover real.
        """
        self.exit(result="__quit__")

    async def action_quit_if_empty(self) -> None:
        """Ctrl+D: quit se input vazio, senão deleta caractere forward."""
        input_widget = self.query_one("#input", InputWidget)
        if not input_widget.value:
            self.exit(result="__quit__")
        else:
            input_widget.action_delete_right()

    async def action_cycle_mode(self) -> None:
        """Shift+Tab: cicla normal -> plan -> sudo -> bypass -> normal."""
        self._mode_idx = (self._mode_idx + 1) % len(self.MODE_CYCLE)
        new_mode = self.MODE_CYCLE[self._mode_idx]
        toolbar = self.query_one("#toolbar", Toolbar)
        toolbar.mode = new_mode

    async def action_paste(self) -> None:
        """Ctrl+V: cola texto do clipboard (lazy import VISION-02).

        Falhas (clipboard inacessível fora de TTY, X11 ausente, etc.)
        viram no-op silencioso -- o agent não pode crashar por causa
        de um colar best-effort.
        """
        try:
            from nyx.agent.clipboard import capture_text

            text = capture_text() or ""
        except Exception:
            text = ""
        if text:
            input_widget = self.query_one("#input", InputWidget)
            input_widget.paste_text(text)

    async def action_recall_last(self) -> None:
        """Ctrl+O: recarrega último input no buffer (UX-EXTRA-01)."""
        if self._last_input:
            input_widget = self.query_one("#input", InputWidget)
            input_widget.value = self._last_input


__all__ = ["NyxTUI"]
