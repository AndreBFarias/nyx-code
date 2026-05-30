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

from rich.text import Text
from textual.app import RenderResult
from textual.widgets import Static

_VALID_ROLES = ("user", "assistant", "tool", "system")

# Glifo via chr() -- defesa anti-sanitizer (padrao do BRIEF).
_DIAMOND = chr(0x25C6)


class ChatMessage(Static):
    """Mensagem individual da conversa.

    Role determina CSS class (turquesa user, roxo assistant, dim tool/system).
    append_text(token) suporta streaming -- chamado via call_from_thread
    pelo Agent bridge (sprint TUI-AGENT-BRIDGE-01).
    """

    def __init__(self, role: str, content: str = "") -> None:
        if role not in _VALID_ROLES:
            raise ValueError(
                f"role deve ser um de {_VALID_ROLES}, got: {role!r}"
            )
        super().__init__(classes=role)
        self._role = role
        self._content = content

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
        Sobrescrever render() retornando Text contorna o issue de forma
        idiomática (BannerWidget e Toolbar seguem o mesmo padrão).
        """
        if self._role == "user":
            return Text(f"> {self._content}")
        if self._role == "assistant":
            if self._content:
                return Text(f"{_DIAMOND} NyxCode\n{self._content}")
            return Text(f"{_DIAMOND} NyxCode")
        if self._role == "tool":
            return Text(f"  {self._content}")
        return Text(self._content)  # system: sem prefixo


__all__ = ["ChatMessage"]
