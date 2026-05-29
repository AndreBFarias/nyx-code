"""BannerWidget -- banner Nyx com cursor blink local na TUI Textual.

ONDA-30 sub-sprint TEXTUAL-BANNER-WIDGET-01. Redenção empírica da sprint
187 BLINK_SOFT (revertida pela 193): a animação que causou flicker no
prompt_toolkit agora funciona porque Textual `Static.refresh()` é refresh
LOCAL por widget -- sem race com `app.invalidate()` global.

O cursor alterna entre U+258C (full block) e U+258F (thin block) a cada
`blink_period` segundos. Estado e timer são locais ao widget; nenhuma
invalidação global é disparada.

Padrão referenciado: Luna `BannerGlitchWidget` em
``/home/andrefarias/Desenvolvimento/Luna/src/ui/banner/widgets.py``
(timer local com `set_interval`, `self.refresh()` por widget).

Tokens de cor são consumidos indiretamente via `build_banner()` em
``nyx/agent/banner.py`` (que importa de ``nyx.themes.design_tokens``).
"""

from __future__ import annotations

import os
from typing import Any

from rich.text import Text
from textual.app import RenderResult
from textual.widgets import Static

from nyx.agent.banner import build_banner

# Glifos do cursor (parametrizados via chr() para sobreviver a sanitizers
# hostis que removem literais Unicode em massa -- ver BRIEF seção
# "Defesa anti-sanitizer").
_CURSOR_FULL = chr(0x258C)  # ▌ bloco cheio
_CURSOR_THIN = chr(0x258F)  # ▏ bloco fino


class BannerWidget(Static):
    """Banner Nyx com cursor `▌` <-> `▏` piscando local a cada 0.5s.

    Constructor:
      model: nome do modelo Ollama em uso.
      tools_count: quantidade de tools registradas.
      project_name: nome do projeto (CWD basename).
      settings: NyxSettings opcional para banner detalhado.
      blink_period: intervalo do toggle em segundos. Default 0.5.

    Lifecycle:
      `on_mount()` registra `self.set_interval(blink_period, _toggle)` se
      a env var `NYX_NO_ANIMATION` não estiver setada para "1". `_toggle()`
      inverte o estado e chama `self.refresh()` -- refresh LOCAL ao widget,
      não `app.invalidate()` global (essa foi a causa do flicker da 187).
    """

    DEFAULT_CSS = """
    BannerWidget {
        dock: top;
        height: auto;
        background: $surface;
        padding: 0 1;
    }
    """

    def __init__(
        self,
        *,
        model: str,
        tools_count: int,
        project_name: str,
        settings: Any = None,
        blink_period: float = 0.5,
    ) -> None:
        super().__init__()
        self._model = model
        self._tools_count = tools_count
        self._project_name = project_name
        self._settings = settings
        self._blink_period = blink_period
        self._cursor_full = True  # True -> U+258C, False -> U+258F
        self._blink_timer: Any = None

    def render(self) -> RenderResult:
        """Constrói o banner via build_banner(cursor=...) e retorna Text ANSI.

        Quando invocado fora de um App context (ex.: testes isolados), pode
        levantar NoActiveAppError; o caller deve tratar graciosamente.
        """
        cursor = _CURSOR_FULL if self._cursor_full else _CURSOR_THIN
        ansi_str = build_banner(
            self._model,
            self._tools_count,
            self._project_name,
            settings=self._settings,
            cursor=cursor,
        )
        return Text.from_ansi(ansi_str)

    def on_mount(self) -> None:
        """Agenda o timer de blink local após mount.

        Skip silencioso quando `NYX_NO_ANIMATION=1` (CI/headless). Sem TTY
        check explícito porque Textual já gerencia headless via driver.
        """
        if os.environ.get("NYX_NO_ANIMATION") == "1":
            return
        self._blink_timer = self.set_interval(self._blink_period, self._toggle)

    def _toggle(self) -> None:
        """Alterna o estado do cursor e re-renderiza LOCALMENTE.

        Crucial: usa `self.refresh()` (escopo widget) em vez de
        `app.invalidate()` (escopo global). Essa foi a causa raiz do flicker
        da sprint 187 BLINK_SOFT -- o invalidate global criava race com
        streaming de output e outros redraws.
        """
        self._cursor_full = not self._cursor_full
        self.refresh()


__all__ = ["BannerWidget"]
