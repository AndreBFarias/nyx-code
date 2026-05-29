# SPEC

```yaml
sprint:
  id: TUI-CHATMESSAGE-WIDGET-01
  title: "Cria widget ChatMessage com role-based rendering"
  onda: 32
  prioridade: ALTA
  tipo: Feature
  dependencias: [TUI-CSS-LUNA-ADOPT-01]
  desbloqueia: [TUI-VERTICAL-SCROLL-ADOPT-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/__init__.py
      reason: "Exportar ChatMessage"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/chat_message.py
      reason: "Widget de mensagem com classes user/assistant/tool/system"

  removes: []

  forbidden:
    - "Hex hardcoded no widget (consumir via CSS classes ou design_tokens)"
    - "Adicionar emoji"
    - "Mencionar IA externa" <!-- noqa-anonimato -->
    - "Adicionar pytest/unittest (ADR-014)"

  tests:
    - cmd: "./venv/bin/python -c 'from nyx.agent.tui.widgets.chat_message import ChatMessage; m = ChatMessage(\"user\", \"Olá\"); assert \"user\" in m.classes; print(\"OK\")'"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Arquivo chat_message.py existe (~80L)"
    - "Classe ChatMessage(Static) com 4 roles aceitos: user, assistant, tool, system"
    - "Método append_text(token) atualiza render"
    - "Método _render() retorna string com prefixo correto por role"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-CHATMESSAGE-WIDGET-01 — Widget ChatMessage role-based

**Status:** PENDENTE
**Data criação:** 2026-05-28
**Modelo obrigatório:** Modelo Opus 4.7 (1M) (sem subagentes)

---

## Contexto do projeto (snapshot)

> ADRs: ADR-013 Integração Obrigatória, ADR-014 Testes via Gauntlet (zero pytest).
> Sprint anterior: TUI-CSS-LUNA-ADOPT-01 CONCLUIDA (CSS já tem classes ChatMessage.{user,assistant,tool,system}).
> Estado: `nyx/agent/tui/widgets/` tem 4 widgets (banner, input, output, toolbar).

---

## Problema

A nova arquitetura TUI Textual (ONDA-32) precisa renderizar mensagens da
conversa como widgets discretos mountados em VerticalScroll (paridade Luna
`add_chat_entry`). Hoje não existe esse widget -- OutputWidget(RichLog) trata
tudo como linhas de log indistinguíveis.

---

## Solução proposta

Criar `widgets/chat_message.py` com classe `ChatMessage(Static)`:
- Constructor: `__init__(self, role: str, content: str = "")`
- Roles aceitos: "user", "assistant", "tool", "system" (validar)
- Aplica CSS class via `super().__init__(classes=role)` -- estilos já vivem no nyx.tcss
- `_render()` adiciona prefixo por role: "> " para user, "◆ NyxCode\n" para assistant, "  " para tool/system
- `append_text(token: str)` atualiza self._content e chama self.update(self._render())

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/chat_message.py` (NOVO, ~80L)

```python
"""ChatMessage -- mensagem da conversa renderizada por role.

ONDA-32 TUI-CHATMESSAGE-WIDGET-01. Substitui rendering legacy
em OutputWidget(RichLog). Mountada em VerticalScroll(id="chat")
pela sprint TUI-VERTICAL-SCROLL-ADOPT-01.

Roles aceitos: user, assistant, tool, system. Cores e bordas vem
de classes CSS em nyx/agent/tui/styles/nyx.tcss -- widget apenas
seta classes e renderiza texto com prefixo.
"""

from __future__ import annotations

from textual.widgets import Static


_VALID_ROLES = ("user", "assistant", "tool", "system")


class ChatMessage(Static):
    """Mensagem individual da conversa.

    Role determina CSS class (turquesa user, roxo assistant, dim tool/system).
    append_text(token) suporta streaming -- chamado via call_from_thread
    pelo Agent bridge (sprint TUI-AGENT-BRIDGE-01).
    """

    def __init__(self, role: str, content: str = "") -> None:
        if role not in _VALID_ROLES:
            raise ValueError(f"role deve ser um de {_VALID_ROLES}, got: {role!r}")
        super().__init__(classes=role)
        self._role = role
        self._content = content
        self.update(self._render())

    @property
    def role(self) -> str:
        return self._role

    @property
    def content(self) -> str:
        return self._content

    def append_text(self, token: str) -> None:
        """Append token ao conteudo e re-renderiza.

        Thread-safe quando chamado via call_from_thread; o Textual driver
        garante que update() agenda no event loop.
        """
        if not token:
            return
        self._content += token
        self.update(self._render())

    def set_content(self, content: str) -> None:
        """Substitui conteudo integral (sem append)."""
        self._content = content
        self.update(self._render())

    def _render(self) -> str:
        """Constroi string final a partir do role e content."""
        if self._role == "user":
            return f"> {self._content}"
        if self._role == "assistant":
            if self._content:
                return f"NyxCode\n{self._content}"
            return "NyxCode"
        if self._role == "tool":
            return f"  {self._content}"
        return self._content  # system: sem prefixo


__all__ = ["ChatMessage"]
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/__init__.py`

Adicionar export:

```python
from nyx.agent.tui.widgets.chat_message import ChatMessage  # noqa: F401
```

---

## Diff esperado

```
+ 1 arquivo criado (chat_message.py ~80L)
~ 1 arquivo modificado (__init__.py +1L)
- 0 arquivos removidos
+ ~81 linhas líquidas
```

---

## Comandos de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Smoke boot
./run.sh --smoke
# esperado: "boot ok"

# 2. Validação semântica do widget
./venv/bin/python -c "
from nyx.agent.tui.widgets.chat_message import ChatMessage

for role in ('user', 'assistant', 'tool', 'system'):
    m = ChatMessage(role, 'teste')
    assert role in m.classes, f'{role} ausente nas classes'
    assert m.role == role
    assert 'teste' in m.content

# append_text
m = ChatMessage('assistant')
m.append_text('a')
m.append_text('bc')
assert m.content == 'abc'

# role invalido
try:
    ChatMessage('invalid')
    raise AssertionError('deveria ter lancado ValueError')
except ValueError:
    pass

print('OK 4 roles + append_text + ValueError')
"

# 3. Invariantes
bash scripts/sprint_invariants.sh

# 4. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/tui/widgets/chat_message.py \
    nyx/agent/tui/widgets/__init__.py

# 5. Ruff
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/widgets/chat_message.py
```

---

## Critério binário de aceite

- [ ] `chat_message.py` criado (~80L)
- [ ] `ChatMessage` herda de Static
- [ ] 4 roles aceitos (user, assistant, tool, system); 5º levanta ValueError
- [ ] `append_text` atualiza content e dispara update
- [ ] `_render()` retorna prefixos corretos por role
- [ ] `__init__.py` exporta ChatMessage
- [ ] Smoke ok + invariantes 14/14 + ruff limpo
- [ ] Sem hex hardcoded no .py (cores vêm via CSS classes)

---

## Proof-of-work obrigatório

Conforme template V2. Antes/Depois invariantes + output do comando #2.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `classes` parameter do Static ser ignorado | Validar via `assert role in m.classes` no comando #2 |
| Conflict com OutputWidget que ainda existe | Sprint 3 deleta output.py; aqui só convive |

---

*"O texto precede a tela." -- Roland Barthes (paráfrase)*
