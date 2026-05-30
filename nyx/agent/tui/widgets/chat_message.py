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

from nyx.themes.design_tokens import NYX_ACCENT, NYX_PURPLE

_VALID_ROLES = ("user", "assistant", "tool", "system")

# Glifo via chr() -- defesa anti-sanitizer (padrao do BRIEF).
_DIAMOND = chr(0x25C6)


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

    @property
    def role(self) -> str:
        return self._role

    @property
    def content(self) -> str:
        return self._content

    def append_text(self, token: str) -> None:
        """Append token ao conteudo e re-renderiza.

        TUI-FIX-CHATMESSAGE-RELAYOUT-01 (ONDA-33): usa refresh(layout=True).
        Um ChatMessage assistant cresce de 1 linha ("◆ NyxCode") para N linhas
        conforme o streaming chega -- muda de ALTURA. refresh() simples só
        repinta o widget na altura antiga; o texto novo não aparece (o input,
        single-line, não tinha o problema). layout=True força o Textual a
        recalcular a altura do widget no container de scroll.
        """
        if not token:
            return
        self._content += token
        self.refresh(layout=True)

    def set_content(self, content: str) -> None:
        """Substitui conteudo integral (sem append)."""
        self._content = content
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
            if self._content:
                # TUI-CHAT-MARKDOWN-SYNTAX-01: conteúdo do assistant renderizado
                # como Markdown -- blocos ``` ganham syntax highlight (Rich/pygments),
                # listas e ênfase formatadas. Seguro no streaming (testado: sem o
                # crash get_height; Markdown tolera ``` ainda aberto mid-stream).
                return Group(label, Markdown(self._content))
            return label
        if self._role == "tool":
            return Text(f"  {self._content}")
        return Text(self._content)  # system: sem prefixo


__all__ = ["ChatMessage"]
