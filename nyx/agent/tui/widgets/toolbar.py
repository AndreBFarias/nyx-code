"""Toolbar -- bottom bar da TUI Textual com reactive properties.

ONDA-30 sub-sprint TEXTUAL-TOOLBAR-01. Substituirá o build_bottom_toolbar
atual do PromptSession (`nyx/cli_keybindings.py:build_bottom_toolbar`) após
a sub-sprint TEXTUAL-CUTOVER-01.

Reactive properties + watch_* são o equivalente Textual ao FormattedText
callable do prompt_toolkit -- quando o state muda, o widget re-renderiza
LOCALMENTE (via `self.refresh()`), sem race com `app.invalidate()` global.

Padrão referenciado: BannerWidget (sub-sprint 205) -- refresh por-widget,
sem invalidação global. Tokens de cor consumidos via design_tokens.
"""

from __future__ import annotations

from rich.text import Text
from textual.app import RenderResult
from textual.reactive import reactive
from textual.widgets import Static

from nyx.themes.design_tokens import (
    NYX_ACCENT,
    NYX_ERROR,
    NYX_MUTED,
    NYX_PURPLE,
    NYX_PURPLE_DIM,
    STATE_GLYPHS,
)


class Toolbar(Static):
    """Bottom toolbar com ctx/iter/lidos/modif/model_state/mode.

    Reactive properties:
      ctx_pct: % de contexto consumido (0-100).
      iter_n: iterações do turno atual.
      reads: arquivos lidos no turno.
      mods: arquivos modificados no turno.
      model_state: cold/warming/warm.
      mode: normal/plan/sudo/bypass.

    Constructor:
      model: nome do modelo Ollama (display fixo após init).

    Lifecycle:
      Cada watch_* dispara `self.refresh()` LOCAL ao widget. Crucial:
      mesma lição do BannerWidget (185 BLINK_SOFT revertida pela 193) --
      refresh por-widget evita race com streaming de output e outros
      redraws orquestrados pelo Textual driver.
    """

    DEFAULT_CSS = """
    Toolbar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $foreground;
    }
    """

    ctx_pct: reactive[int] = reactive(0)
    iter_n: reactive[int] = reactive(0)
    reads: reactive[int] = reactive(0)
    mods: reactive[int] = reactive(0)
    model_state: reactive[str] = reactive("cold")
    mode: reactive[str] = reactive("normal")
    # TUI-AGENT-BRIDGE-01: True enquanto worker do turno esta rodando.
    # NyxTUI seta antes de run_worker e reseta no finally do _process_turn.
    inflight: reactive[bool] = reactive(False)

    def __init__(self, *, model: str = "qwen2.5-coder:3b") -> None:
        super().__init__()
        self._model = model

    def render(self) -> RenderResult:
        """Constrói Text com layout:

            Ctx X% | model | Iter N | Lidos M | Modif K | glyph state | modo

        Fallback do glyph: `STATE_GLYPHS.get(state, STATE_GLYPHS["cold"])`
        garante render mesmo se reactive `model_state` receber valor fora
        do conjunto canônico (cold/warming/warm).
        """
        msg = Text()
        msg.append(f"Ctx {self.ctx_pct}%", style=NYX_ACCENT)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(self._model, style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(f"Iter {self.iter_n}", style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(f"Lidos {self.reads}", style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(f"Modif {self.mods}", style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        glyph = STATE_GLYPHS.get(self.model_state, STATE_GLYPHS["cold"])
        msg.append(f"{glyph} {self.model_state}", style=NYX_MUTED)
        # TUI-AGENT-BRIDGE-01: indicador de turno em execução com hint
        # de cancelamento via Ctrl+C. Inserido antes da secao do modo
        # para preservar legibilidade da extrema direita (modo) intacta.
        if self.inflight:
            msg.append("  |  ", style=NYX_MUTED)
            msg.append("executando (Ctrl+C cancela)", style=NYX_ACCENT)
        msg.append("    ", style=NYX_MUTED)
        if self.mode == "bypass":
            msg.append(" bypass ON (shift+tab) ", style=f"bold {NYX_PURPLE_DIM}")
        elif self.mode == "plan":
            msg.append(" [plan] read-only (shift+tab) ", style=f"bold {NYX_PURPLE}")
        elif self.mode == "sudo":
            msg.append(" [sudo] elevado (shift+tab) ", style=f"bold {NYX_ERROR}")
        else:
            msg.append("shift+tab: normal/plan/sudo/bypass", style=NYX_MUTED)
        return msg

    # Watch handlers: cada mudança de reactive property dispara
    # self.refresh() automaticamente, mas declaramos explícitos para
    # clareza + extensibilidade (logging futuro, hooks de telemetria).
    def watch_ctx_pct(self, old: int, new: int) -> None:
        self.refresh()

    def watch_iter_n(self, old: int, new: int) -> None:
        self.refresh()

    def watch_reads(self, old: int, new: int) -> None:
        self.refresh()

    def watch_mods(self, old: int, new: int) -> None:
        self.refresh()

    def watch_model_state(self, old: str, new: str) -> None:
        self.refresh()

    def watch_mode(self, old: str, new: str) -> None:
        self.refresh()

    def watch_inflight(self, old: bool, new: bool) -> None:
        self.refresh()


__all__ = ["Toolbar"]
