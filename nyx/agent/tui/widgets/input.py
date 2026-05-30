"""InputWidget -- prompt de input do usuário na TUI Textual.

ONDA-30 sub-sprint 202 (TEXTUAL-INPUT-WIDGET-01). Substituirá o BufferControl
atual do nyx/agent/repl_app.py após TEXTUAL-CUTOVER-01.

Funcionalidades essenciais portadas do prompt_toolkit:
  - Slash completer: lista navegável quando texto começa com `/`.
  - Paste handler: trata imagem do clipboard como `[Image #N]`.
  - Submit callback: chamado quando user pressiona Enter (não-newline).

Por enquanto é widget isolado: importável, testável, não composto no
NyxTUI ainda.

Tokens de cor importados de nyx.themes.design_tokens (UX-DESIGN-01):
fonte única de hex para satisfazer invariante #6 de sprint_invariants.sh.
"""

from __future__ import annotations

from typing import Callable

from textual.suggester import SuggestFromList
from textual.widgets import Input

from nyx.themes.design_tokens import NYX_ACCENT  # noqa: F401  (referência de paleta)


class InputWidget(Input):
    """Prompt de input do usuário ancorado no rodapé.

    Parâmetros:
      slash_completer: lista de nomes de slash commands (sem o `/`). Quando
                       texto começa com `/`, suggestions são filtradas dessa
                       lista (case-insensitive).
      on_submit: callback chamado com (text: str) quando user pressiona
                 Enter. Buffer é limpo após o callback.
      placeholder: texto exibido quando o buffer está vazio.
      id: id Textual opcional para seleção via CSS.

    Métodos públicos:
      paste_text(text): cola texto no buffer; se prefixo `[clipboard-image]:`
                        for detectado, insere placeholder `[Image #?]`
                        (lógica de N delegada ao caller via futura sprint).
    """

    # Estilo do widget vive em nyx/agent/tui/styles/nyx.tcss (fonte unica).
    # O bloco DEFAULT_CSS foi removido na SPRINT 285 para eliminar o conflito
    # de height (3 aqui vs 5 no nyx.tcss); a regra de placeholder migrou para
    # o seletor InputWidget > .input--placeholder no arquivo de estilos.

    def __init__(
        self,
        *,
        slash_completer: list[str] | None = None,
        on_submit: Callable[[str], None] | None = None,
        placeholder: str = "Digite uma mensagem ou /comando",
        id: str | None = None,
    ) -> None:
        # Suggester ativa quando há lista de slash commands. SuggestFromList
        # filtra entradas por prefixo (case_sensitive=False permite /HELP
        # casar com `help`).
        suggester: SuggestFromList | None
        if slash_completer:
            full_list = [f"/{c}" for c in slash_completer]
            suggester = SuggestFromList(full_list, case_sensitive=False)
        else:
            suggester = None

        super().__init__(
            placeholder=placeholder,
            suggester=suggester,
            id=id,
        )
        self._on_submit = on_submit

    async def action_submit(self) -> None:
        """Override do action_submit do Textual.

        Chama o callback registrado (se houver) com o conteúdo do buffer e
        em seguida limpa o input para o próximo turno.
        """
        text = self.value
        if self._on_submit is not None:
            self._on_submit(text)
        self.clear()

    def paste_text(self, text: str) -> None:
        """Insere texto no buffer respeitando o prefixo de imagem.

        Quando o texto começa com `[clipboard-image]:` o caller está
        sinalizando que o clipboard continha uma imagem; substituímos pelo
        placeholder visível `[Image #?]`. O número real é calculado por um
        caller externo em sprint futura.
        """
        if text.startswith("[clipboard-image]:"):
            self.insert_text_at_cursor("[Image #?]")
        else:
            self.insert_text_at_cursor(text)


__all__ = ["InputWidget"]
