# SPEC

```yaml
sprint:
  id: TUI-VERTICAL-SCROLL-ADOPT-01
  title: "NyxTUI.compose troca OutputWidget(RichLog) por VerticalScroll + ChatMessage"
  onda: 32
  prioridade: ALTA
  tipo: Refactor
  dependencias: [TUI-CHATMESSAGE-WIDGET-01]
  desbloqueia: [TUI-AGENT-BRIDGE-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "compose() yields VerticalScroll(id='chat') no lugar de OutputWidget"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/__init__.py
      reason: "Remover export de OutputWidget"

  creates: []

  removes:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/output.py
      reason: "OutputWidget(RichLog) substituido por VerticalScroll+ChatMessage"

  forbidden:
    - "Manter import de OutputWidget em app.py"
    - "Pular validação opt-in (NYX_TUI_TEXTUAL=1)"
    - "Mencionar IA externa" <!-- noqa-anonimato -->

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "NYX_TUI_TEXTUAL=1 ./venv/bin/python -c 'from nyx.agent.tui.app import NyxTUI; from textual.containers import VerticalScroll; assert NyxTUI is not None; print(\"OK NyxTUI importa sem OutputWidget\")'"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "app.py.compose() yield VerticalScroll(id='chat') em vez de OutputWidget"
    - "widgets/output.py removido"
    - "widgets/__init__.py sem export de OutputWidget"
    - "_on_input_submit mounta ChatMessage('user', text) no chat scroll"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-VERTICAL-SCROLL-ADOPT-01 — VerticalScroll nativo + ChatMessage

**Status:** PENDENTE
**Data criação:** 2026-05-28
**Modelo obrigatório:** Modelo Opus 4.7 (1M) (sem subagentes)

---

## Contexto

> Sprint anterior: TUI-CHATMESSAGE-WIDGET-01 CONCLUIDA. ChatMessage existe.
> CSS já tem `#chat { ... scrollbar-color: $primary 30%; ... }` (sprint 1).
> NyxTUI.compose() atual yield BannerWidget + OutputWidget + Toolbar + InputWidget.

---

## Problema

`OutputWidget(RichLog)` (`widgets/output.py`) é placeholder da ONDA-30 -- tudo é
linha de log indistinguível. Não dá para distinguir mensagem user de assistant
visualmente, scroll é manual via RichLog limitado, e mensagens não podem ser
mountadas/atualizadas dinamicamente como widgets.

`VerticalScroll` nativo do Textual resolve: scrollbar funciona com mouse wheel,
click-arrasta, PgUp/PgDn/Home/End -- tudo de graça. Mensagens viram
`ChatMessage` widgets mountados.

---

## Solução proposta

Substituir em `nyx/agent/tui/app.py`:
- Import `OutputWidget` -> import `VerticalScroll` (de `textual.containers`)
- `compose()` yield `VerticalScroll(id="chat")` no lugar do OutputWidget
- `_on_input_submit` deixa de chamar `output.write_user(text)` e passa a
  `chat.mount(ChatMessage("user", text))` + `chat.scroll_end(animate=False)`

Deletar `nyx/agent/tui/widgets/output.py` e remover export do `__init__.py`.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py`

**Antes (trechos):**
```python
from nyx.agent.tui.widgets.output import OutputWidget
...
def compose(self) -> ComposeResult:
    ...
    output = OutputWidget(id="output")
    yield output
    ...
def _on_input_submit(self, text: str) -> None:
    if not text.strip():
        return
    self._last_input = text
    output = self.query_one("#output", OutputWidget)
    output.write_user(text)
```

**Depois:**
```python
from textual.containers import VerticalScroll
from nyx.agent.tui.widgets.chat_message import ChatMessage
...
def compose(self) -> ComposeResult:
    ...
    yield VerticalScroll(id="chat")
    ...
def _on_input_submit(self, text: str) -> None:
    if not text.strip():
        return
    self._last_input = text
    chat = self.query_one("#chat", VerticalScroll)
    chat.mount(ChatMessage("user", text))
    chat.scroll_end(animate=False)
```

**Mudanças:** remove import OutputWidget; adiciona import VerticalScroll +
ChatMessage; compose yields VerticalScroll(id="chat"); _on_input_submit usa
mount.

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/__init__.py`

Remover linha de export de `OutputWidget` (mantém ChatMessage, banner, input,
toolbar).

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/output.py`

DELETAR (rm).

---

## Diff esperado

```
+ 0 arquivos criados
~ 2 arquivos modificados (app.py, widgets/__init__.py)
- 1 arquivo removido (widgets/output.py 67L)
~  ~10 linhas líquidas (modificações em app.py)
```

---

## Comandos de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Smoke
./run.sh --smoke

# 2. app.py importa sem OutputWidget e usa VerticalScroll
./venv/bin/python -c "
import inspect
from nyx.agent.tui import app
src = inspect.getsource(app)
assert 'OutputWidget' not in src, 'OutputWidget ainda referenciado em app.py'
assert 'VerticalScroll' in src, 'VerticalScroll nao importado'
assert 'ChatMessage' in src, 'ChatMessage nao importado'
assert 'id=\"chat\"' in src or \"id='chat'\" in src, 'id chat nao usado'
print('OK app.py: VerticalScroll + ChatMessage, sem OutputWidget')
"

# 3. Arquivo output.py removido
test ! -f nyx/agent/tui/widgets/output.py && echo "OK output.py deletado" || (echo "FAIL output.py ainda existe"; exit 1)

# 4. Invariantes
bash scripts/sprint_invariants.sh

# 5. Gauntlet --only rapido (sanidade)
./run.sh --gauntlet --only rapido

# 6. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/tui/app.py \
    nyx/agent/tui/widgets/__init__.py

# 7. Ruff
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/
```

---

## Critério binário de aceite

- [ ] `nyx/agent/tui/widgets/output.py` deletado
- [ ] `app.py` sem referência a OutputWidget
- [ ] `app.py` importa VerticalScroll + ChatMessage
- [ ] `app.py.compose()` yield VerticalScroll(id="chat")
- [ ] `_on_input_submit` mounta ChatMessage("user", text)
- [ ] `__init__.py` sem export de OutputWidget
- [ ] Smoke ok + invariantes 14/14
- [ ] Gauntlet --only rapido APROVADO

---

## Proof-of-work obrigatório

Conforme template V2. Antes/Depois invariantes + outputs comandos #2, #3, #5.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Algum outro arquivo importa OutputWidget | `grep -rn OutputWidget nyx/` antes/depois; se sobrar, ajustar; tipicamente só app.py |
| VerticalScroll precisa height fixed/percent | CSS `#chat { height: 1fr; ... }` já existe da sprint 1 |

---

*"O movimento é o lugar onde nada se prende." -- Ailton Krenak (paráfrase)*
