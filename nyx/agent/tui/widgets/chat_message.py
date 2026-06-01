"""ChatMessage -- mensagem da conversa renderizada por role.

ONDA-32 TUI-CHATMESSAGE-WIDGET-01. Mountada em VerticalScroll(id="chat")
pela sprint TUI-VERTICAL-SCROLL-ADOPT-01.

Roles aceitos: user, assistant, tool, system. Cores e bordas vem
de classes CSS em nyx/agent/tui/styles/nyx.tcss -- widget apenas
seta classes e renderiza texto com prefixo.

Glifo do cabecalho do assistant usa chr(0x25C6) (BLACK DIAMOND)
para imunidade ao sanitizer histórico (ver BRIEF secao Defesa
anti-sanitizer).
"""

from __future__ import annotations

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text
from textual.app import RenderResult
from textual.widgets import Static

from nyx.themes.design_tokens import NYX_ACCENT, NYX_MUTED, NYX_PURPLE

_VALID_ROLES = ("user", "assistant", "tool", "system")

# Glifo via chr() -- defesa anti-sanitizer (padrao do BRIEF).
_DIAMOND = chr(0x25C6)

# TUI-CONVERSATION-SCROLL-TEXTUAL-01 (SPRINT 309): intervalo de coalescing dos
# refreshes durante o streaming. render() reconstroi Markdown(self._content)
# INTEIRO (com pygments no bloco de codigo) a cada repaint; refresh por token
# era O(n^2) e travava a TUI inteira -- medido: 1.6k chars => 75s e ~3250
# parses de Markdown, com scroll e teclado congelados junto (o "travou feio").
# Coalescer em ~1 refresh por 100ms derruba o numero de parses em ordens de
# magnitude, sem perda visual perceptivel (o crescimento de altura segue suave).
_STREAM_REFRESH_INTERVAL = 0.1
# Apos este tempo SEM novos tokens, o streaming "assenta": o conteudo passa a
# ser renderizado como Markdown (com syntax highlight) UMA vez. Durante o
# streaming o render e texto plano (barato) -- evita o re-parse O(n^2) que
# travava a TUI. Cada token reagenda este timer (debounce).
_SETTLE_INTERVAL = 0.3


def _format_elapsed(seconds: float) -> str:
    """TUI-TURN-ELAPSED-01: duração do turno legível.

    < 60s -> '3.2s'; >= 60s -> '2m04s' (respostas longas em CPU degradado).
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, secs = divmod(int(seconds), 60)
    return f"{minutes}m{secs:02d}s"


class ChatMessage(Static):
    """Mensagem individual da conversa.

    Role determina a CSS class + border-left (turquesa user, roxo assistant,
    dim tool/system). Desde TUI-CHAT-LABELS-COLORS-01 o NOME (label) leva a cor
    de destaque da role e o CONTEÚDO fica em $foreground (neutro), via spans Rich.
    append_text(token) suporta streaming -- chamado via call_from_thread
    pelo Agent bridge (sprint TUI-AGENT-BRIDGE-01).
    """

    def __init__(
        self, role: str, content: str = "", *, display_name: str = ""
    ) -> None:
        if role not in _VALID_ROLES:
            raise ValueError(
                f"role deve ser um de {_VALID_ROLES}, got: {role!r}"
            )
        super().__init__(classes=role)
        self._role = role
        self._content = content
        # TUI-CHAT-LABELS-COLORS-01: nome de exibição do usuário (vindo de
        # resolve_user_display_name via cli.py -> NyxTUI). Só usado no role
        # "user"; o assistant rotula sempre "NyxCode".
        self._display_name = display_name
        # TUI-CONVERSATION-SCROLL-TEXTUAL-01 (SPRINT 309): coalescing do refresh
        # durante o streaming (ver append_text). _refresh_pending: ha refresh
        # agendado. _streaming: tokens ainda chegando (render = texto plano
        # barato); vira False no settle (render = Markdown 1x). _settle_timer:
        # timer de debounce reagendado a cada token.
        self._refresh_pending = False
        self._streaming = False
        self._settle_timer = None
        # TUI-TURN-ELAPSED-01: duração do turno em segundos, setada por
        # set_elapsed() ao fim do _process_turn. None = ainda não medido (durante
        # o streaming) ou role não-assistant. Aparece no label do balão NyxCode.
        self._elapsed_s: float | None = None

    @property
    def role(self) -> str:
        return self._role

    @property
    def content(self) -> str:
        return self._content

    def append_text(self, token: str) -> None:
        """Append token ao conteudo; agenda um refresh COALESCIDO (não por token).

        TUI-FIX-CHATMESSAGE-RELAYOUT-01 (ONDA-33): o refresh usa layout=True --
        um ChatMessage assistant cresce de 1 linha ("◆ NyxCode") para N linhas
        conforme o streaming chega (muda de ALTURA), e layout=True força o
        Textual a recalcular a altura no container de scroll.

        TUI-CONVERSATION-SCROLL-TEXTUAL-01 (SPRINT 309): o refresh NÃO é mais por
        token. render() reconstrói Markdown(self._content) inteiro a cada repaint
        (com pygments no bloco de código); chamar refresh por token era O(n^2) --
        medido: 1.6k chars => 75s e ~3250 parses, travando a TUI e o scroll. Agora
        o 1º token agenda um único timer (_STREAM_REFRESH_INTERVAL); os tokens que
        chegam nesse meio-tempo só acumulam em _content. Quando o timer dispara
        (_flush_refresh), faz UM refresh com todo o conteúdo acumulado. O último
        token sempre é renderizado: seu timer pendente dispara após o fim do stream.
        """
        if not token:
            return
        self._content += token
        self._streaming = True
        self._bump_settle()
        if self._refresh_pending:
            return
        self._refresh_pending = True
        self.set_timer(_STREAM_REFRESH_INTERVAL, self._flush_refresh)

    def _flush_refresh(self) -> None:
        """Refresh coalescido do streaming (texto plano; TUI-CONVERSATION-SCROLL-TEXTUAL-01)."""
        self._refresh_pending = False
        self.refresh(layout=True)

    def _bump_settle(self) -> None:
        """Reagenda o timer de settle (debounce): cada token adia o fim do stream."""
        if self._settle_timer is not None:
            self._settle_timer.stop()
        self._settle_timer = self.set_timer(_SETTLE_INTERVAL, self._settle)

    def _settle(self) -> None:
        """Stream assentou: re-renderiza como Markdown (syntax highlight) UMA vez."""
        self._settle_timer = None
        if self._streaming:
            self._streaming = False
            self.refresh(layout=True)

    def set_content(self, content: str) -> None:
        """Substitui conteudo integral (sem append). Renderiza Markdown direto."""
        self._content = content
        self._streaming = False  # substituicao integral não e streaming
        self.refresh(layout=True)

    def set_elapsed(self, seconds: float) -> None:
        """TUI-TURN-ELAPSED-01: registra a duração do turno (segundos).

        Chamado no finally do _process_turn quando há um balão de assistant no
        turno. Aparece no label do balão como ' NyxCode  ·  3.2s', dando de volta
        o feedback de tempo de resposta que existia antes da migração Textual.
        """
        self._elapsed_s = seconds
        self.refresh(layout=True)

    def render(self) -> RenderResult:
        """Render via Text (não str) para evitar bug get_height do Textual 8.x.

        Static.update(str) faz wrapping interno que em alguns paths de
        arrange dispara `AttributeError: 'str' has no attribute get_height`.
        Sobrescrever render() retornando renderables Rich (nunca str) contorna
        o issue de forma idiomática (BannerWidget e Toolbar seguem o padrão).
        O assistant retorna Group(label, Markdown(content)) -- Markdown traz
        syntax highlight aos blocos ``` (TUI-CHAT-MARKDOWN-SYNTAX-01); os demais
        roles retornam Text simples.
        """
        if self._role == "user":
            # TUI-CHAT-LABELS-COLORS-01: nome em cor de destaque (turquesa,
            # NYX_ACCENT); conteúdo neutro ($foreground via CSS). O Text vazio
            # não tem cor-base, então o span do nome colore só o label e o
            # append do conteúdo herda a cor do widget.
            name = self._display_name or "Você"
            text = Text()
            text.append(f"> {name}", style=NYX_ACCENT)
            if self._content:
                text.append(f"\n{self._content}")
            return text
        if self._role == "assistant":
            label = Text(f"{_DIAMOND} NyxCode", style=NYX_PURPLE)
            # TUI-TURN-ELAPSED-01: tempo de resposta em muted, logo após o nome.
            if self._elapsed_s is not None:
                label.append(
                    f"  ·  {_format_elapsed(self._elapsed_s)}", style=NYX_MUTED
                )
            if self._content:
                # TUI-CHAT-MARKDOWN-SYNTAX-01: conteúdo do assistant renderizado
                # como Markdown -- blocos ``` ganham syntax highlight (Rich/pygments),
                # listas e ênfase formatadas.
                # TUI-CONVERSATION-SCROLL-TEXTUAL-01 (309): enquanto _streaming,
                # renderiza TEXTO PLANO (barato). Re-parsear Markdown a cada
                # refresh durante o stream era O(n^2) e travava a TUI/scroll
                # (1.6k chars => 75s). O Markdown (pygments) entra UMA vez quando
                # o stream assenta (_settle), trocando o texto plano pelo formatado.
                if self._streaming:
                    return Group(label, Text(self._content))
                return Group(label, Markdown(self._content))
            return label
        if self._role == "tool":
            return Text(f"  {self._content}")
        return Text(self._content)  # system: sem prefixo


__all__ = ["ChatMessage"]
