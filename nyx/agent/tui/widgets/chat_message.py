"""ChatMessage -- mensagem da conversa renderizada por role.

ONDA-32 TUI-CHATMESSAGE-WIDGET-01. Mountada em VerticalScroll(id="chat")
pela sprint TUI-VERTICAL-SCROLL-ADOPT-01.

Roles aceitos: user, assistant, tool, system. Cores e bordas vem
de classes CSS em nyx/agent/tui/styles/nyx.tcss -- widget apenas
seta classes e renderiza texto com prefixo.

Glifo do cabecalho do assistant usa chr(0x25C6) (BLACK DIAMOND)
para imunidade ao sanitizer histórico (ver BRIEF seção Defesa
anti-sanitizer).
"""

from __future__ import annotations

import re

from rich.console import Group
from rich.markdown import Markdown
from rich.text import Text
from textual.app import RenderResult
from textual.selection import Selection
from textual.strip import Strip
from textual.widgets import Static

from nyx.themes.design_tokens import NYX_ACCENT, NYX_MUTED, NYX_PURPLE

_VALID_ROLES = ("user", "assistant", "tool", "system")

# Glifo via chr() -- defesa anti-sanitizer (padrão do BRIEF).
_DIAMOND = chr(0x25C6)

# TUI-COPY-ASSISTANT-MARKDOWN-01: captura o conteudo INTERNO de cada bloco ``` da
# fonte (raw markdown), byte-fiel. A 1a linha da fence pode trazer a linguagem
# (ex.: ```python); o grupo (.*?) so pega o corpo, sem as cercas. Mesmo idioma do
# _CODE_FENCE_RE do app.py (Ctrl+Y) -- drag-select e Ctrl+Y devolvem o MESMO codigo.
_CODE_FENCE_RE = re.compile(r"```[^\n]*\n(.*?)```", re.DOTALL)

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

    def render_line(self, y: int) -> Strip:
        """Injeta metadado de offset (x, y) nas linhas do assistant assentado.

        TUI-COPY-ASSISTANT-MARKDOWN-01 (448): achado empírico -- o compositor do
        Textual (`_compositor.get_widget_and_offset_at`) só resolve um
        `content_offset` (necessário para uma Selection PARCIAL, não
        `Selection(None, None)`) quando os segmentos da linha carregam o
        metadado `"offset"` no style; isso é aplicado automaticamente para
        renders `Text`/`Content` (`textual/content.py`), mas NUNCA para um
        Rich renderable genérico como `Group(label, Markdown(...))` --
        confirmado varrendo toda a área do widget (nenhuma posição produz
        offset). Sem esse metadado, QUALQUER drag sobre o balão do assistant
        vira sempre `Selection(None, None)` (seleção "tudo ou nada"),
        independente de quantas linhas o mouse cobriu -- get_selection nunca
        recebe range algum para mapear. `Strip.apply_offsets(x, y)` é o mesmo
        mecanismo de opt-in que o widget Log usa (único outro consumidor no
        pacote) para ganhar seleção por posição em conteúdo não-Text. Aplicado
        só quando assentado (Markdown) -- streaming é Text puro e já ganha
        offset nativamente; demais roles idem.
        """
        strip = super().render_line(y)
        if self._role == "assistant" and not self._streaming and self._content:
            return strip.apply_offsets(0, y)
        return strip

    def _copyable_source(self) -> str:
        """Texto-fonte BYTE-FIEL desta mensagem para copia.

        TUI-COPY-ASSISTANT-MARKDOWN-01: quando ha bloco(s) de codigo, devolve o
        corpo dos fences concatenado (sem as cercas ```), igual ao que o Ctrl+Y
        copia -- e exatamente "o codigo que a Nyx escreveu". Sem fence, devolve o
        _content cru (prosa byte-fiel). O resultado vem da FONTE, nunca do render
        Markdown -- por isso e imune ao desalinhamento de offset (as linhas
        renderizadas do Markdown ganham padding de caixa e as cercas viram linhas
        em branco; mapear offset renderizado -> fonte copiaria o trecho ERRADO).
        Usado como fallback: seleção cobrindo o widget inteiro, ou seleção que
        não toca nenhuma linha de código mapeada de forma confiável (ver
        _code_line_index).
        """
        blocks = _CODE_FENCE_RE.findall(self._content)
        if blocks:
            return "\n".join(b.rstrip("\n") for b in blocks)
        return self._content

    def _row_matches_code_line(self, y: int, code_line: str) -> bool:
        """A linha visual `y` (ja renderizada, self.render_line) e' esta linha-fonte?

        TUI-COPY-ASSISTANT-MARKDOWN-01 (448): medido empiricamente que o Rich
        Markdown aplica 1 espaco de padding de caixa a esquerda em cada linha de
        codigo (fences viram linhas em branco tambem padded). Exige que o texto
        renderizado (sem os espaços de preenchimento à direita) TERMINE com a
        linha-fonte exata e que só sobre padding (espaços) antes dela -- byte-fiel
        contra o `_content` cru, não contra o render.
        """
        row_text = self.render_line(y).text.rstrip()
        if code_line == "":
            return row_text == ""
        if not row_text.endswith(code_line):
            return False
        pad = row_text[: len(row_text) - len(code_line)]
        return pad == " " * len(pad)

    def _find_code_block_start(
        self, search_from: int, height: int, first_line: str
    ) -> int | None:
        """Acha a 1a linha visual (>= search_from) que bate com `first_line`."""
        for y in range(search_from, height):
            if self._row_matches_code_line(y, first_line):
                return y
        return None

    def _code_line_index(self) -> dict[int, int]:
        """Mapeia linha VISUAL (row do render assentado) -> indice da linha-fonte.

        TUI-COPY-ASSISTANT-MARKDOWN-01 (448, refinamento sobre a 392): usa o
        Strip REALMENTE renderizado (self.render_line -- a mesma fonte que o
        Textual usa para pintar a tela e para as coordenadas y da Selection) para
        cada bloco ``` do `_content`, byte-fiel. So mapeia um bloco quando TODAS
        as suas linhas aparecem CONSECUTIVAS no render e cada uma bate exatamente
        com a linha-fonte correspondente (via _row_matches_code_line); qualquer
        desvio (wrap, bloco corrompido, linha sintética) deixa o bloco INTEIRO de
        fora do índice -- excluído, nunca chutado, conforme a spec 448. Prosa e
        cabeçalhos não entram neste índice (fora do escopo mínimo "fidelidade nos
        blocos de código"); seleção que só toca essas linhas cai no fallback
        _copyable_source().
        """
        index: dict[int, int] = {}
        height = self.size.height
        if height <= 0:
            return index
        search_from = 1  # linha 0 e' sempre o label ("NyxCode" [+ elapsed])
        for match in _CODE_FENCE_RE.finditer(self._content):
            body = match.group(1)
            body_lines = body.split("\n")
            if body_lines and body_lines[-1] == "":
                body_lines = body_lines[:-1]
            if not body_lines or body_lines[0] == "":
                # bloco vazio ou começando em branco: ambíguo contra o padding
                # de caixa (linha em branco também aparece na cerca) -- pula
                # sem mapear, para não arriscar desalinhar os blocos seguintes.
                continue
            source_start = self._content.count("\n", 0, match.start(1))
            start_y = self._find_code_block_start(
                search_from, height, body_lines[0]
            )
            if start_y is None:
                continue
            reliable = True
            for offset, line in enumerate(body_lines):
                y = start_y + offset
                if y >= height or not self._row_matches_code_line(y, line):
                    reliable = False
                    break
            if reliable:
                for offset in range(len(body_lines)):
                    index[start_y + offset] = source_start + offset
                search_from = start_y + len(body_lines)
            else:
                search_from = start_y + 1
        return index

    def get_selection(self, selection: Selection) -> tuple[str, str] | None:
        """Sobrescreve a extração de seleção para o balão Markdown do assistant.

        TUI-COPY-ASSISTANT-MARKDOWN-01. O Widget.get_selection base so extrai
        renders Text/Content; o assistant renderiza Group(label, Markdown(...)),
        entao a base retorna None e o drag-select volta VAZIO -- era justamente
        "copiar o codigo" que o dono queria.

        Refinamento 448 sobre a 392: enquanto em streaming (render ainda é Text
        plano, sem Markdown assentado) ou quando a seleção cobre o widget por
        completo (`Selection(None, None)`), devolve a FONTE inteira via
        _copyable_source (Caminho A, "seleção cobre o widget"). Já assentado e
        com uma seleção parcial (linhas específicas), mapeia cada linha VISUAL
        tocada de volta à sua linha-fonte via _code_line_index -- byte-fiel,
        não o widget inteiro -- e IGNORA (exclui) qualquer linha sem
        correspondência confiável (cabeçalho, prosa reformatada) em vez de
        chutar. Se nenhuma linha da seleção mapear, cai no fallback
        _copyable_source (nunca retorna vazio para conteúdo não-vazio).
        Demais roles (user/tool/system) renderizam Text puro -> caem na
        implementacao base do Textual, preservando o copy-on-select da 390.
        """
        if self._role != "assistant" or not self._content:
            return super().get_selection(selection)
        if self._streaming:
            return self._copyable_source(), "\n"
        start, end = selection
        if start is None and end is None:
            return self._copyable_source(), "\n"
        height = self.size.height
        if height <= 0:
            return self._copyable_source(), "\n"
        start_y = 0 if start is None else start.y
        end_y = height - 1 if end is None else end.y
        start_y = max(0, min(height - 1, start_y))
        end_y = max(0, min(height - 1, end_y))
        if start_y > end_y:
            start_y, end_y = end_y, start_y
        index = self._code_line_index()
        source_lines = self._content.splitlines()
        mapped = [
            source_lines[index[y]]
            for y in range(start_y, end_y + 1)
            if y in index
        ]
        if mapped:
            return "\n".join(mapped), "\n"
        return self._copyable_source(), "\n"


__all__ = ["ChatMessage"]
