"""InputWidget -- prompt de input do usuário na TUI Textual.

ONDA-30 sub-sprint 202 (TEXTUAL-INPUT-WIDGET-01); migrado para base TextArea
na ONDA-34 sprint 286 (TUI-INPUT-TEXTAREA-MULTILINE-01).

Funcionalidades essenciais portadas do prompt_toolkit:
  - Multiline: Ctrl+J insere nova linha; Enter submete (semântica invertida
    do TextArea, que por padrão insere `\\n` no Enter).
  - Slash completer ghost-inline: lista filtrada por prefixo quando o texto
    começa com `/`; sugestão renderizada dim, aceita por Tab.
  - Paste handler: trata imagem do clipboard como `[Image #N]`.
  - Submit callback: chamado quando o usuário pressiona Enter (não-newline).

Base TextArea (Textual 8.2.7): herdamos crescimento de altura, edição
multiline natural e o mecanismo nativo de ghost via o reactive `suggestion`
e o hook `update_suggestion()`. O TextArea NÃO possui `suggester`/`SuggestFromList`
(exclusivo do `Input`), mas expõe o reactive `suggestion` que o `_render_line`
desenha na posição do cursor com a classe `text-area--suggestion`; basta popular
esse reactive no hook para reerguer o ghost-completer da sprint 284 sem overlay
custom.

Tokens de cor importados de nyx.themes.design_tokens (UX-DESIGN-01):
fonte única de hex para satisfazer invariante #6 de sprint_invariants.sh.
"""

from __future__ import annotations

from typing import Callable

from textual import events
from textual.widgets import TextArea

from nyx.themes.design_tokens import NYX_ACCENT  # noqa: F401  (referência de paleta)


class InputWidget(TextArea):
    """Prompt de input do usuário ancorado no rodapé.

    Parâmetros:
      slash_completer: lista de nomes de slash commands (sem o `/`). Quando o
                       texto começa com `/`, a sugestão ghost é o 1º match por
                       prefixo case-insensitive da lista `/<nome>`.
      on_submit: callback chamado com (text: str) quando o usuário pressiona
                 Enter. Buffer é limpo após o callback.
      placeholder: texto exibido quando o buffer está vazio.
      id: id Textual opcional para seleção via CSS.

    Teclas:
      Enter      -> submete (chama on_submit, limpa o buffer).
      Ctrl+J     -> insere nova linha (multiline; o widget cresce em altura
                    até o max-height do CSS e depois scrolla internamente).
      Tab        -> aceita a sugestão ghost ativa; sem sugestão, comportamento
                    padrão (troca de foco, pois tab_behavior="focus").

    Métodos públicos:
      paste_text(text): cola texto no buffer; se prefixo `[clipboard-image]:`
                        for detectado, insere `[Image #N]`, com N vindo de um
                        contador interno incremental por sessão (1, 2, 3, ...).
    """

    # Estilo do widget vive em nyx/agent/tui/styles/nyx.tcss (fonte unica).
    # O bloco DEFAULT_CSS foi removido na SPRINT 285 para eliminar o conflito
    # de height; a regra de placeholder/ghost migrou para os seletores
    # InputWidget > .text-area--placeholder e .text-area--suggestion no
    # arquivo de estilos.

    def __init__(
        self,
        *,
        slash_completer: list[str] | None = None,
        on_submit: Callable[[str], None] | None = None,
        placeholder: str = "Digite uma mensagem ou /comando",
        id: str | None = None,
    ) -> None:
        # Lista de slash commands completos (`/<nome>`) usada pelo ghost manual.
        # O TextArea não tem suggester; computamos a sugestão em update_suggestion.
        self._slash_full = [f"/{c}" for c in (slash_completer or [])]

        # tab_behavior="focus": Tab não indenta (reservado para aceitar o ghost
        # ou trocar foco); soft_wrap=True para quebra visual de linhas longas.
        super().__init__(
            placeholder=placeholder,
            id=id,
            soft_wrap=True,
            tab_behavior="focus",
        )
        self._on_submit = on_submit

        # Contador monotônico de imagens coladas na sessão; vira [Image #N] em
        # paste_text. Acumulativo enquanto a instância viver (sem reset por turno).
        self._image_count: int = 0

    def update_suggestion(self) -> None:
        """Hook do TextArea: recalcula o ghost-completer do slash (sprint 284).

        Chamado pelo TextArea a cada edição. Quando o texto inteiro começa com
        `/` (sem nova linha) e há um match por prefixo case-insensitive em
        `self._slash_full`, expomos o sufixo restante no reactive `suggestion`,
        que o `_render_line` do TextArea desenha dim na posição do cursor.
        Sem match, limpamos a sugestão.
        """
        text = self.text
        if not self._slash_full or not text.startswith("/") or "\n" in text:
            self.suggestion = ""
            return
        lowered = text.lower()
        for full in self._slash_full:
            if full.lower().startswith(lowered) and full != text:
                self.suggestion = full[len(text) :]
                return
        self.suggestion = ""

    async def _on_key(self, event: events.Key) -> None:
        """Inverte a semântica de Enter/Ctrl+J e aceita o ghost com Tab.

        - Enter (`enter`): SUBMETE -- consome o evento, chama on_submit com o
          texto atual e limpa o buffer. Diferente do TextArea padrão, que
          insere `\\n` no Enter.
        - Ctrl+J (`ctrl+j`): insere nova linha -- consome o evento e insere
          `\\n` no cursor (multiline). O byte LF (0x0a) chega como `ctrl+j`.
        - Tab (`tab`) com sugestão ativa: aceita o ghost (insere o sufixo).
        - Demais teclas: delega ao TextArea para preservar a edição normal.
        """
        if event.key == "enter":
            event.stop()
            event.prevent_default()
            text = self.text
            if self._on_submit is not None:
                self._on_submit(text)
            self.clear()
            return
        if event.key == "ctrl+j":
            event.stop()
            event.prevent_default()
            self.insert("\n")
            return
        if event.key == "tab" and self.suggestion:
            event.stop()
            event.prevent_default()
            self.insert(self.suggestion)
            return
        await super()._on_key(event)

    def paste_text(self, text: str) -> None:
        """Insere texto no buffer respeitando o prefixo de imagem.

        Quando o texto começa com `[clipboard-image]:` o caller está
        sinalizando que o clipboard continha uma imagem; substituímos por
        `[Image #N]`, onde N é um contador monotônico de instância incrementado
        a cada imagem colada na sessão (TUI-IMAGE-PASTE-COUNTER-01). A primeira
        imagem vira `[Image #1]`, a segunda `[Image #2]`, e assim por diante.
        """
        if text.startswith("[clipboard-image]:"):
            self._image_count += 1
            self.insert(f"[Image #{self._image_count}]")
        else:
            self.insert(text)


__all__ = ["InputWidget"]
