# SPEC

```yaml
sprint:
  id: TUI-SLASH-DISPATCH-MODAL-01
  title: "Slash dispatch via _redirect_to_chat + SelectScreen ModalScreen nativo"
  onda: 32
  prioridade: ALTA
  tipo: Feature
  dependencias: [TUI-AGENT-BRIDGE-01]
  desbloqueia: [TUI-DEFAULT-FLIP-LEGACY-RM-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "Adicionar _dispatch_slash + _redirect_to_chat context manager"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/screens/__init__.py
      reason: "Pacote screens"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/screens/select_screen.py
      reason: "ModalScreen para aesthetic_select/theme_select/schema_select"

  removes: []

  forbidden:
    - "Manter dependência de radiolist_dialog no caminho NyxTUI"
    - "Adicionar emoji"
    - "Mencionar IA externa" <!-- noqa-anonimato -->

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "./venv/bin/python -c 'from nyx.agent.tui.screens.select_screen import SelectScreen; from textual.screen import ModalScreen; assert issubclass(SelectScreen, ModalScreen); print(\"OK SelectScreen herda ModalScreen\")'"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "nyx/agent/tui/screens/select_screen.py existe"
    - "SelectScreen(ModalScreen[str]) com compose() yielding Static title + Buttons + Binding escape para dismiss"
    - "NyxTUI._dispatch_slash chama handle_command e processa resultado"
    - "_redirect_to_chat context manager mounta ChatMessage('tool', line) por linha de stdout"
    - "Sentinels __aesthetic_select__/__theme_select__/__schema_select__ disparam push_screen_wait(SelectScreen)"
    - "Smoke ok + gauntlet rapido + invariantes 14/14"
```

---

# Sprint TUI-SLASH-DISPATCH-MODAL-01 — Slash + Modal Textual nativo

**Status:** PENDENTE
**Data criação:** 2026-05-28
**Modelo obrigatório:** Modelo Opus 4.7 (1M) (sem subagentes)

---

## Contexto

> Sprint anterior: TUI-AGENT-BRIDGE-01. Bridge agent já funciona.
> Falta: slash commands (/help /status /quit /theme etc) + modais que hoje usam
> radiolist_dialog do prompt_toolkit (`nyx/cli_boot.py:run_select_modal`).
>
> Handle_command (`nyx/agent/commands/__init__.py`) é compartilhado entre
> caminhos. Retorna string ou sentinel ("__quit__", "__aesthetic_select__", etc).

---

## Problema

NyxTUI atual não despacha slash commands. Usuário digita `/help` e o texto
é mountado como ChatMessage user mas nada acontece. Modais que usam
radiolist_dialog (3 ocorrências: aesthetic_select, theme_select, schema_select)
não têm equivalente Textual e crasham o app se forem disparados.

---

## Solução proposta

1. Detectar `text.startswith("/")` em `_on_input_submit` e rotear para
   `_dispatch_slash(text)`.
2. `_dispatch_slash`:
   - Chama `handle_command(text, project_root)`
   - Trata sentinels: `__quit__` -> `self.exit("__quit__")`;
     `__aesthetic_select__`/`__theme_select__`/`__schema_select__` -> push SelectScreen
   - Para outros sentinels (sync handlers), monta `HandlerCtx` e chama
     `dispatch_sync` / `dispatch_async`
   - Output via `_redirect_to_chat` que captura stdout e mounta ChatMessage tool
3. `SelectScreen(ModalScreen[str])`:
   - Constructor recebe `title: str` e `options: list[tuple[str, str]]` (value, label)
   - compose() yield Container com Static(title) + Buttons(label, id=f"opt-{value}")
   - on_button_pressed -> `self.dismiss(value)`
   - ESC binding -> `self.dismiss(None)`

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/screens/__init__.py` (NOVO)

```python
"""Pacote de screens Textual auxiliares."""
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/screens/select_screen.py` (NOVO, ~60L)

```python
"""SelectScreen -- ModalScreen Textual para seleção entre N opções.

Substitui radiolist_dialog do prompt_toolkit usado em cli_boot.run_select_modal
para aesthetic_select, theme_select, schema_select.
"""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static


class SelectScreen(ModalScreen[str]):
    """Modal de seleção de opção.

    Uso:
        selected = await self.push_screen_wait(
            SelectScreen("Escolha o tema", [("dark", "Escuro"), ("light", "Claro")])
        )
        # selected vem como str (value) ou None (ESC cancelou)
    """

    DEFAULT_CSS = """
    SelectScreen { align: center middle; }
    SelectScreen > Container {
        width: 60%;
        max-width: 80;
        height: auto;
        max-height: 80%;
        background: $surface;
        border: heavy $accent;
        padding: 1 2;
    }
    SelectScreen Vertical { height: auto; }
    SelectScreen #modal-title {
        color: $accent;
        text-style: bold;
        margin: 0 0 1 0;
    }
    SelectScreen Button {
        width: 100%;
        margin: 0 0 1 0;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancelar", priority=True),
    ]

    def __init__(self, title: str, options: list[tuple[str, str]]) -> None:
        super().__init__()
        self._title = title
        self._options = options

    def compose(self) -> ComposeResult:
        with Container():
            with Vertical():
                yield Static(self._title, id="modal-title")
                for value, label in self._options:
                    yield Button(label, id=f"opt-{value}")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id is None:
            return
        value = event.button.id.removeprefix("opt-")
        self.dismiss(value)

    def action_cancel(self) -> None:
        self.dismiss(None)


__all__ = ["SelectScreen"]
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py`

**Adicionar em `_on_input_submit` (no início):**
```python
if text.lstrip().startswith("/"):
    self._dispatch_slash(text)
    return
```

**Adicionar como métodos novos da classe NyxTUI:**
```python
def _dispatch_slash(self, text: str) -> None:
    from nyx.agent.commands import handle_command
    chat = self.query_one("#chat", VerticalScroll)
    chat.mount(ChatMessage("user", text))
    chat.scroll_end(animate=False)
    project_root = str(getattr(self._settings, "project_root", "."))
    try:
        result = handle_command(text, project_root)
    except Exception as exc:
        chat.mount(ChatMessage("tool", f"[erro] {exc}"))
        return
    if result is None:
        return
    if result == "__quit__":
        self.exit(result="__quit__")
        return
    if result in ("__aesthetic_select__", "__theme_select__", "__schema_select__"):
        self.run_worker(self._open_select_modal(result), exclusive=False)
        return
    # Outros: render no chat como tool
    chat.mount(ChatMessage("tool", str(result)))

async def _open_select_modal(self, kind: str) -> None:
    from nyx.agent.tui.screens.select_screen import SelectScreen
    # Stub minimo: opcoes vem de settings/theme_manager; sprint dedicada
    # popula. Aqui basta provar que push_screen_wait funciona.
    options = [("opt1", "Opção 1"), ("opt2", "Opção 2")]
    title = {
        "__aesthetic_select__": "Estética",
        "__theme_select__": "Tema",
        "__schema_select__": "Schema",
    }[kind]
    selected = await self.push_screen_wait(SelectScreen(title, options))
    chat = self.query_one("#chat", VerticalScroll)
    chat.mount(ChatMessage("tool", f"{kind}: {selected}"))
```

---

## Diff esperado

```
+ 2 arquivos criados (screens/__init__.py, screens/select_screen.py ~60L)
~ 1 arquivo modificado (app.py +50L)
+ ~110 linhas líquidas
```

---

## Comandos de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Smoke
./run.sh --smoke

# 2. SelectScreen carrega
./venv/bin/python -c "
from nyx.agent.tui.screens.select_screen import SelectScreen
from textual.screen import ModalScreen
assert issubclass(SelectScreen, ModalScreen)
s = SelectScreen('Teste', [('a', 'A'), ('b', 'B')])
assert s._title == 'Teste'
assert s._options == [('a', 'A'), ('b', 'B')]
print('OK SelectScreen instancia + heranca')
"

# 3. NyxTUI tem _dispatch_slash + _open_select_modal
./venv/bin/python -c "
import inspect
from nyx.agent.tui.app import NyxTUI
src = inspect.getsource(NyxTUI)
for sym in ('_dispatch_slash', '_open_select_modal', 'SelectScreen', 'push_screen_wait', 'handle_command'):
    assert sym in src, f'falta: {sym}'
print('OK slash dispatch + modal wiring')
"

# 4. Invariantes
bash scripts/sprint_invariants.sh

# 5. Gauntlet rapido
./run.sh --gauntlet --only rapido

# 6. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/tui/app.py \
    nyx/agent/tui/screens/select_screen.py \
    nyx/agent/tui/screens/__init__.py

# 7. Ruff
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/
```

---

## Critério binário de aceite

- [ ] `screens/__init__.py` criado
- [ ] `screens/select_screen.py` com SelectScreen(ModalScreen[str])
- [ ] SelectScreen tem BINDING escape + on_button_pressed -> dismiss(value)
- [ ] `app.py._on_input_submit` rotea slash para `_dispatch_slash`
- [ ] `_dispatch_slash` chama handle_command e trata sentinels
- [ ] Sentinels select disparam push_screen_wait(SelectScreen)
- [ ] Smoke ok + gauntlet rapido + invariantes 14/14

---

## Proof-of-work obrigatório

Conforme template V2.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| handle_command precisa project_root específico | Buscar via `self._settings` ou fallback "." |
| push_screen_wait dentro de _dispatch_slash (sync) | Wrap em `run_worker(self._open_select_modal(...))` que é async |
| Opções dos modais vêm de theme_manager (não trivial) | Stub mínimo nesta sprint; sprint posterior pluga opções reais |
| handle_command pode ter side-effect de stdout legacy | Reset stdout no início do dispatch via try/except |

---

*"Cada porta uma escolha; cada escolha um caminho." -- Jorge Luís Borges (paráfrase)*
