# SPEC

```yaml
sprint:
  id: TUI-AGENT-BRIDGE-01
  title: "NyxTUI integra AgentLoop via worker thread + callbacks call_from_thread"
  onda: 32
  prioridade: CRITICA
  tipo: Feature
  dependencias: [TUI-VERTICAL-SCROLL-ADOPT-01, TUI-BANNER-DOCK-TOP-01]
  desbloqueia: [TUI-SLASH-DISPATCH-MODAL-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "Adicionar _process_turn worker + callbacks; constructor aceita agent"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/toolbar.py
      reason: "Adicionar reactive inflight: bool com watch handler"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Passar agent ao NyxTUI no dispatch opt-in (linha ~419-439)"

  creates: []
  removes: []

  forbidden:
    - "Modificar AgentLoop signature (callbacks já existem: on_token, on_tool, on_tool_result)"
    - "Chamar self.update/mount fora de call_from_thread no worker"
    - "Adicionar emoji"
    - "Mencionar IA externa" <!-- noqa-anonimato -->

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "./venv/bin/python -c 'import inspect; from nyx.agent.tui.app import NyxTUI; src = inspect.getsource(NyxTUI); assert \"_process_turn\" in src and \"call_from_thread\" in src and \"run_worker\" in src; print(\"OK bridge methods present\")'"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true

  acceptance_criteria:
    - "NyxTUI.__init__ aceita agent: AgentLoop | None"
    - "_on_input_submit dispara run_worker(_process_turn, thread=True, exclusive=True)"
    - "_process_turn agarda agent.run() e atualiza toolbar.inflight via call_from_thread"
    - "on_token / on_tool / on_tool_result registrados via call_from_thread"
    - "Toolbar tem reactive inflight: bool com render mostrando 'executando' quando True"
    - "cli.py passa agent ao NyxTUI(...) no dispatch opt-in"
    - "Smoke ok + gauntlet rapido APROVADO + invariantes 14/14"
```

---

# Sprint TUI-AGENT-BRIDGE-01 — Bridge NyxTUI <-> AgentLoop

**Status:** PENDENTE
**Data criação:** 2026-05-28
**Modelo obrigatório:** Modelo Opus 4.7 (1M) (sem subagentes)

---

## Contexto

> Sprint anterior: TUI-VERTICAL-SCROLL-ADOPT-01 + TUI-BANNER-DOCK-TOP-01.
> ChatMessage mountado em #chat. Agora falta WIRING com AgentLoop.
>
> AgentLoop tem callbacks síncronos (`on_token`, `on_tool`, `on_tool_result`,
> `on_model_state`, `on_thinking`) registrados via constructor (`nyx/cli.py:300-313`).
> No prompt_toolkit, callbacks chamam print/render direto. Em Textual precisa
> de call_from_thread.

---

## Problema

`NyxTUI._on_input_submit` atualmente só registra texto no OutputWidget (sprint 207).
Não chama agent.run(), não recebe streaming, não atualiza toolbar. Sem isso, TUI
nova é shell vazio.

---

## Solução proposta

1. `NyxTUI.__init__` recebe `agent: AgentLoop` opcional. Registra callbacks
   próprios (`_on_token`, `_on_tool`, `_on_tool_result`) na instância do agent.
2. `_on_input_submit(text)`:
   - Mounta `ChatMessage("user", text)` (já feito na sprint 3)
   - Mounta `ChatMessage("assistant", "")` que será o destino do streaming
   - Salva ref em `self._current_assistant`
   - Seta `toolbar.inflight = True`
   - Dispara `self.run_worker(self._process_turn(text), thread=True, exclusive=True)`
3. `_process_turn` é coroutine async (run_worker permite ambos):
   - `await self._agent.run(user_input)` -- callbacks disparam durante
   - `finally: self.call_from_thread(setattr, toolbar, 'inflight', False)`
4. Callbacks usam `self.call_from_thread(self._current_assistant.append_text, token)`.
5. `Toolbar` ganha `inflight: reactive[bool]`. Render mostra "executando (Ctrl+C cancela)"
   na seção do modo quando True.

`nyx/cli.py` passa `agent` ao NyxTUI no dispatch opt-in (linha 419-439).

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/toolbar.py`

**Antes (declaração reactives):**
```python
ctx_pct: reactive[int] = reactive(0)
iter_n: reactive[int] = reactive(0)
reads: reactive[int] = reactive(0)
mods: reactive[int] = reactive(0)
model_state: reactive[str] = reactive("cold")
mode: reactive[str] = reactive("normal")
```

**Depois:**
```python
ctx_pct: reactive[int] = reactive(0)
iter_n: reactive[int] = reactive(0)
reads: reactive[int] = reactive(0)
mods: reactive[int] = reactive(0)
model_state: reactive[str] = reactive("cold")
mode: reactive[str] = reactive("normal")
inflight: reactive[bool] = reactive(False)
```

**No render(), adicionar antes da seção do modo:**
```python
if self.inflight:
    msg.append("  |  ", style=NYX_MUTED)
    msg.append("executando (Ctrl+C cancela)", style=NYX_ACCENT)
```

**Adicionar watch handler:**
```python
def watch_inflight(self, old: bool, new: bool) -> None:
    self.refresh()
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py`

**Antes (constructor):**
```python
def __init__(
    self,
    *,
    model: str = "qwen2.5-coder:3b",
    tools_count: int = 35,
    project_name: str = "Nyx-Code",
    slash_completer: list[str] | None = None,
    settings: Any = None,
) -> None:
    super().__init__()
    self._model = model
    self._tools_count = tools_count
    self._project_name = project_name
    self._slash_completer = slash_completer or []
    self._settings = settings
    self._mode_idx = 0
    self._last_input: str = ""
```

**Depois:**
```python
def __init__(
    self,
    *,
    model: str = "qwen2.5-coder:3b",
    tools_count: int = 35,
    project_name: str = "Nyx-Code",
    slash_completer: list[str] | None = None,
    settings: Any = None,
    agent: Any = None,
) -> None:
    super().__init__()
    self._model = model
    self._tools_count = tools_count
    self._project_name = project_name
    self._slash_completer = slash_completer or []
    self._settings = settings
    self._agent = agent
    self._mode_idx = 0
    self._last_input: str = ""
    self._current_assistant = None
    if agent is not None:
        agent.on_token = self._on_agent_token
        agent.on_tool = self._on_agent_tool
        agent.on_tool_result = self._on_agent_tool_result
```

**Antes (_on_input_submit):**
```python
def _on_input_submit(self, text: str) -> None:
    if not text.strip():
        return
    self._last_input = text
    chat = self.query_one("#chat", VerticalScroll)
    chat.mount(ChatMessage("user", text))
    chat.scroll_end(animate=False)
```

**Depois:**
```python
def _on_input_submit(self, text: str) -> None:
    if not text.strip():
        return
    self._last_input = text
    chat = self.query_one("#chat", VerticalScroll)
    chat.mount(ChatMessage("user", text))
    if self._agent is None:
        chat.scroll_end(animate=False)
        return
    assistant = ChatMessage("assistant", "")
    chat.mount(assistant)
    chat.scroll_end(animate=False)
    self._current_assistant = assistant
    toolbar = self.query_one(Toolbar)
    toolbar.inflight = True
    self.run_worker(self._process_turn(text), thread=True, exclusive=True)

async def _process_turn(self, text: str) -> None:
    try:
        await self._agent.run(text)
    except Exception:
        self.call_from_thread(setattr, self.query_one(Toolbar), "inflight", False)
        raise
    self.call_from_thread(setattr, self.query_one(Toolbar), "inflight", False)
    self.call_from_thread(self.query_one("#chat", VerticalScroll).scroll_end, False)

def _on_agent_token(self, token: str) -> None:
    if self._current_assistant is not None:
        self.call_from_thread(self._current_assistant.append_text, token)

def _on_agent_tool(self, name: str, args: dict | None = None) -> None:
    chat = self.query_one("#chat", VerticalScroll)
    args_str = "" if args is None else str(args)
    tool_msg = ChatMessage("tool", f"{name}({args_str})")
    self.call_from_thread(chat.mount, tool_msg)

def _on_agent_tool_result(self, name: str, result: str = "") -> None:
    chat = self.query_one("#chat", VerticalScroll)
    tool_msg = ChatMessage("tool", f"-> {name}: {result}")
    self.call_from_thread(chat.mount, tool_msg)
```

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py`

**Antes (linha ~419-439):**
```python
if use_application and _tui_textual:
    try:
        from nyx.agent.tui.app import NyxTUI

        nyx_tui_app = NyxTUI(
            model=model,
            tools_count=agent.tools_count,
            project_name=PROJECT_ROOT.name,
            slash_completer=[],
            settings=settings,
        )
```

**Depois:**
```python
if use_application and _tui_textual:
    try:
        from nyx.agent.tui.app import NyxTUI

        nyx_tui_app = NyxTUI(
            model=model,
            tools_count=agent.tools_count,
            project_name=PROJECT_ROOT.name,
            slash_completer=[],
            settings=settings,
            agent=agent,
        )
```

---

## Diff esperado

```
~ 3 arquivos modificados (app.py, toolbar.py, cli.py)
+ ~70 linhas líquidas
```

---

## Comandos de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Smoke
./run.sh --smoke

# 2. Bridge methods presentes
./venv/bin/python -c "
import inspect
from nyx.agent.tui.app import NyxTUI
src = inspect.getsource(NyxTUI)
for sym in ('_process_turn', 'call_from_thread', 'run_worker', '_on_agent_token', '_on_agent_tool', '_on_agent_tool_result', '_current_assistant', 'agent'):
    assert sym in src, f'falta: {sym}'
print('OK bridge methods present')

from nyx.agent.tui.widgets.toolbar import Toolbar
tsrc = inspect.getsource(Toolbar)
assert 'inflight' in tsrc, 'reactive inflight ausente em Toolbar'
print('OK Toolbar.inflight')
"

# 3. Invariantes
bash scripts/sprint_invariants.sh

# 4. Gauntlet rapido
./run.sh --gauntlet --only rapido

# 5. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/tui/app.py \
    nyx/agent/tui/widgets/toolbar.py \
    nyx/cli.py

# 6. Ruff
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/ nyx/cli.py
```

---

## Critério binário de aceite

- [ ] `NyxTUI.__init__` aceita `agent` kwarg
- [ ] Constructor registra `agent.on_token = self._on_agent_token` (e on_tool, on_tool_result)
- [ ] `_on_input_submit` mounta ChatMessage user + assistant, seta inflight=True, dispara run_worker
- [ ] `_process_turn` await agent.run() e atualiza inflight=False no finally
- [ ] Callbacks `_on_agent_*` usam `call_from_thread`
- [ ] `Toolbar.inflight` reactive[bool] com watch handler
- [ ] `Toolbar.render` mostra "executando (Ctrl+C cancela)" quando inflight=True
- [ ] `cli.py` passa `agent=agent` ao NyxTUI(...)
- [ ] Smoke ok + gauntlet rapido APROVADO + invariantes 14/14

---

## Proof-of-work obrigatório

Conforme template V2.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `run_worker(thread=True)` cria thread; agent.run() é async | Textual run_worker aceita ambos; `await agent.run()` funciona dentro de async function |
| Callback `on_token` é chamado de dentro do agent.run() (que é thread daemon do streaming)  | call_from_thread agenda no event loop main; thread-safe por design |
| `_current_assistant` pode ser None se outro turno disparar antes | exclusive=True garante 1 worker por vez; entre turnos, _current_assistant é atualizado em _on_input_submit |
| AgentLoop não tem on_tool com signature (name, args) -- pode ser (name, args, result) | Verificar `nyx/agent/loop.py` antes; ajustar signature do `_on_agent_tool` conforme |
| Exception no agent.run() deixa inflight=True | Try/except no _process_turn já reseta inflight no exception path |

---

*"O sinal só atravessa quando o cabo está limpo." -- adágio empírico*
