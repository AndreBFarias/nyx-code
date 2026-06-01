"""SuggestionPanel -- painel de sugestões de slash commands.

TUI-SLASH-SUGGEST-PANEL-01 (BLOCO 3 da ONDA-36 RESSURREIÇÃO). Decisão do dono
(2026-05-31): em vez do ghost-inline de UMA sugestão (sutil, fácil de não
perceber), mostrar um painel de >=3 linhas com os comandos/valores prováveis que
casam o que está sendo digitado. Reergue a descoberta de comandos que existia no
completer rico (prompt_toolkit, `nyx/agent/completer.py`) e regrediu na migração
para Textual -- sem reintroduzir um overlay navegável completo (escopo do dono).

Vive como PRIMEIRO filho do #bottombar (acima do InputWidget). Vazio => some
(classe -empty com display:none), então não ocupa espaço quando não há `/`.
Tokens de cor de design_tokens (invariante #6 de sprint_invariants.sh).
"""

from __future__ import annotations

from rich.text import Text
from textual.app import RenderResult
from textual.widgets import Static

from nyx.themes.design_tokens import NYX_ACCENT, NYX_MUTED, NYX_PURPLE

# Máximo de linhas exibidas (cap visual). O dono pediu "ao menos 3 linhas"; o teto
# evita o painel engolir a tela quando o prefixo é muito curto (ex.: só "/").
_MAX_ROWS = 6
# Largura reservada para o nome do comando antes da descrição (alinhamento).
_NAME_COL = 14


class SuggestionPanel(Static):
    """Painel de sugestões ancorado acima do input.

    update_items([("/model", "troca o modelo"), ...]) popula; lista vazia esconde.
    A primeira sugestão é destacada (a que o Tab aceita no InputWidget).
    """

    DEFAULT_CSS = """
    SuggestionPanel {
        height: auto;
        max-height: 7;
        background: $surface;
        color: $foreground;
        padding: 0 1;
    }
    SuggestionPanel.-empty {
        display: none;
    }
    """

    def __init__(self, *, id: str | None = None) -> None:
        super().__init__(id=id)
        self._items: list[tuple[str, str]] = []
        # Começa escondido: sem `/` digitado, sem painel.
        self.add_class("-empty")

    def update_items(self, items: list[tuple[str, str]]) -> None:
        """Atualiza as sugestões. `items`: lista de (/nome, descrição).

        Lista vazia => esconde o painel (classe -empty). Cap em _MAX_ROWS.
        """
        self._items = list(items[:_MAX_ROWS])
        if self._items:
            self.remove_class("-empty")
        else:
            self.add_class("-empty")
        self.refresh(layout=True)

    def render(self) -> RenderResult:
        if not self._items:
            return Text("")
        msg = Text()
        last = len(self._items) - 1
        for i, (name, desc) in enumerate(self._items):
            # Primeira linha destacada (turquesa); demais em roxo dim.
            marker = "> " if i == 0 else "  "
            name_style = NYX_ACCENT if i == 0 else NYX_PURPLE
            msg.append(marker, style=NYX_MUTED)
            msg.append(f"{name:<{_NAME_COL}}", style=name_style)
            if desc:
                shown = desc if len(desc) <= 48 else desc[:47] + "..."
                msg.append(f" {shown}", style=NYX_MUTED)
            if i < last:
                msg.append("\n")
        return msg


__all__ = ["SuggestionPanel"]
