## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TEXTUAL-CUTOVER-01
  title: "Compoe NyxTUI com 4 widgets (Banner+Output+Input+Toolbar) + bindings + dispatch via cli.py (com env opt-in)"
  onda: 30
  prioridade: CRÍTICA
  tipo: Feature
  dependencias: [TEXTUAL-TOOLBAR-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "Compoe os 4 widgets via compose() + registra BINDINGS + lifecycle on_mount"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Adicionar dispatch opt-in para NyxTUI via env NYX_TUI_TEXTUAL=1 (default continua prompt_toolkit)"

  creates: []

  forbidden:
    - "Mudar default da CLI para Textual (cutover real fica em sub-sprint futura ONDA-31 quando todos os edge-cases forem testados)"
    - "Tocar nyx/agent/repl_app.py (prompt_toolkit fallback intocado)"
    - "Quebrar smoke ou gauntlet"
    - "Adicionar emoji"

  tests:
    - cmd: "./venv/bin/python -c 'from nyx.agent.tui.app import NyxTUI; app = NyxTUI(); print([w.id for w in [*app.BINDINGS]])'"
      timeout: 10
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "NyxTUI.compose() yields Banner, Output, Input, Toolbar"
    - "BINDINGS inclui c-q (quit), c-d (quit_if_empty), s-tab (cycle_mode), c-v (paste), c-o (recall_last)"
    - "Action handlers correspondentes existem (action_quit, action_cycle_mode, etc.)"
    - "Env NYX_TUI_TEXTUAL=1 dispara dispatch para NyxTUI em cli.py (opt-in)"
    - "Env unset OU =0: continua prompt_toolkit (zero regressao default)"
    - "Smoke + invariantes 14/14 PASS"
    - "Gauntlet rapido PASS"
    - "ZERO touches em nyx/agent/repl_app.py"
```

---

# Sprint TEXTUAL-CUTOVER-01 — A grande final

**Status:** PENDENTE
**Data criacao:** 2026-05-22
**Modelo obrigatorio:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> ULTIMA sub-sprint da ONDA-30. Sprints anteriores fechadas: 197 SCAFFOLD, 198 OUTPUT, 202 INPUT, 205 BANNER, 206 TOOLBAR.
> Esta sprint COMPOE os 4 widgets na NyxTUI App + adiciona dispatch OPT-IN via `NYX_TUI_TEXTUAL=1`. **NAO troca default da CLI** (fica para ONDA-31 cutover real, quando edge-cases tiverem sido testados em uso real).
> Esforco estimado: 4-6h. Critico — toca cli.py.

---

## Decisao de design — opt-in via env

Cutover total (trocar default de prompt_toolkit para Textual) tem riscos:
- 67 slash commands testados em prompt_toolkit, NAO testados em Textual.
- Tool chips, diff boxes, spinners, streaming, quit card, first-run wizard — implementados em prompt_toolkit, ainda nao portados.
- Gauntlet roda em modo headless — pode ter divergencias em comportamento Textual vs prompt_toolkit.

**Solucao:** dispatch OPT-IN via env. Default continua prompt_toolkit (zero regressao). Quando usuario testa real e confirma paridade, sprint follow-up troca default.

```bash
# Comportamento default (prompt_toolkit, intocado):
./run.sh

# Comportamento opt-in (NyxTUI Textual):
NYX_TUI_TEXTUAL=1 ./run.sh
```

---

## Solucao proposta

### 1. `nyx/agent/tui/app.py` — compose + bindings

```python
"""NyxTUI — App Textual principal compondo os 4 widgets da ONDA-30.

Compose:
  - BannerWidget (top, com cursor blink local)
  - OutputWidget (middle, rolling log)
  - Toolbar (bottom-1, status)
  - InputWidget (bottom, prompt ancorado)

Bindings:
  - Ctrl+Q: quit (paridade sprint 188)
  - Ctrl+D: quit_if_empty (paridade sprint 189)
  - Shift+Tab: cycle_mode (paridade SHIFT-TAB-CYCLE-01)
  - Ctrl+V: paste (paridade VISION-02)
  - Ctrl+O: recall_last_input (paridade UX-EXTRA-01)

Dispatch:
  - Default: NUNCA dispatched (CLI continua usando repl_app.py).
  - Opt-in: env NYX_TUI_TEXTUAL=1 em cli.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding

from nyx.agent.tui.widgets.banner import BannerWidget
from nyx.agent.tui.widgets.input import InputWidget
from nyx.agent.tui.widgets.output import OutputWidget
from nyx.agent.tui.widgets.toolbar import Toolbar


class NyxTUI(App):
    """App Textual principal — ONDA-30 sub-sprint 207."""

    CSS_PATH = Path(__file__).parent / "styles" / "nyx.tcss"

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
        Binding("ctrl+d", "quit_if_empty", "Quit (EOF)"),
        Binding("shift+tab", "cycle_mode", "Trocar modo"),
        Binding("ctrl+v", "paste", "Colar"),
        Binding("ctrl+o", "recall_last", "Recall ultimo input"),
    ]

    MODES = ("normal", "plan", "sudo", "bypass")

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

    def compose(self) -> ComposeResult:
        yield BannerWidget(
            model=self._model,
            tools_count=self._tools_count,
            project_name=self._project_name,
            settings=self._settings,
        )
        yield OutputWidget(id="output")
        yield Toolbar(id="toolbar", model=self._model)
        yield InputWidget(
            id="input",
            slash_completer=self._slash_completer,
            on_submit=self._on_input_submit,
        )

    def _on_input_submit(self, text: str) -> None:
        """Callback do InputWidget. Por enquanto so logga no OutputWidget.

        Integração real com Agent loop fica para sub-sprint futura.
        """
        if not text.strip():
            return
        self._last_input = text
        output = self.query_one("#output", OutputWidget)
        output.write_user(text)

    async def action_quit(self) -> None:
        """Ctrl+Q: fecha app + ollama stop all (paridade sprint 188).

        Por enquanto so faz exit; integração com shutdown_repl fica para
        sub-sprint futura. Mensagem documenta intencao.
        """
        self.exit(result="__quit__")

    async def action_quit_if_empty(self) -> None:
        """Ctrl+D: quit se input vazio, senao deleta caractere forward."""
        input_widget = self.query_one("#input", InputWidget)
        if not input_widget.value:
            self.exit(result="__quit__")
        else:
            # Deletar caractere forward (readline default).
            input_widget.action_delete_right()

    async def action_cycle_mode(self) -> None:
        """Shift+Tab: cicla normal -> plan -> sudo -> bypass -> normal."""
        self._mode_idx = (self._mode_idx + 1) % len(self.MODES)
        new_mode = self.MODES[self._mode_idx]
        toolbar = self.query_one("#toolbar", Toolbar)
        toolbar.mode = new_mode  # reactive trigger refresh local

    async def action_paste(self) -> None:
        """Ctrl+V: cola texto do clipboard (real impl. via nyx.agent.clipboard)."""
        from nyx.agent.clipboard import capture_text
        text = capture_text() or ""
        if text:
            input_widget = self.query_one("#input", InputWidget)
            input_widget.paste_text(text)

    async def action_recall_last(self) -> None:
        """Ctrl+O: recarrega ultimo input no buffer."""
        if self._last_input:
            input_widget = self.query_one("#input", InputWidget)
            input_widget.value = self._last_input


__all__ = ["NyxTUI"]
```

### 2. `nyx/cli.py` — dispatch opt-in

Adicionar bloco apos detecção `use_application` (linha ~410), antes do `if use_application:` real:

```python
# TEXTUAL-CUTOVER-01: dispatch opt-in via NYX_TUI_TEXTUAL=1.
# Default continua prompt_toolkit; env=1 troca para NyxTUI Textual.
# Quando ONDA-31 (cutover real) confirmar paridade, este branch vira default.
_tui_textual = os.environ.get("NYX_TUI_TEXTUAL", "").strip() == "1"

if use_application and _tui_textual:
    try:
        from nyx.agent.tui.app import NyxTUI

        nyx_tui_app = NyxTUI(
            model=model,
            tools_count=agent.tools_count,
            project_name=PROJECT_ROOT.name,
            slash_completer=list_command_names(),  # se disponivel; senao []
            settings=settings,
        )
        result = await nyx_tui_app.run_async()
        if result == "__quit__":
            render_quit_card(agent, app_state, PROJECT_ROOT)
            await run_quit_shutdown(proxy_url, logger)
        return
    except Exception as _texc:
        logger.warning("NyxTUI opt-in falhou, fallback prompt_toolkit: %s", _texc)
        # cai para o branch use_application existente (prompt_toolkit)

# ... resto do fluxo prompt_toolkit existente, intocado ...
```

(O exato local de inserção depende do código atual — executor deve usar grep para localizar `use_application=True` e inserir o bloco antes do branch real.)

---

## Diff esperado

```
~ 2 arquivos modificados (app.py +~120L, cli.py +~25L)
+ ~145 linhas
```

---

## Comandos de verificacao

```bash
# 1. Import + bindings
./venv/bin/python -c "
from nyx.agent.tui.app import NyxTUI
app = NyxTUI()
print('Bindings:', [b.key for b in app.BINDINGS])
print('Modes:', app.MODES)
"

# 2. Smoke (default prompt_toolkit, sem regressao)
./run.sh --smoke

# 3. Smoke com opt-in (Textual)
NYX_TUI_TEXTUAL=1 ./run.sh --smoke

# 4. Invariantes
bash scripts/sprint_invariants.sh

# 5. Gauntlet rapido
./run.sh --gauntlet --only rapido

# 6. Acentuacao
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/tui/app.py nyx/cli.py
```

---

## Criterio binario de aceite

- [ ] NyxTUI compõe 4 widgets via compose()
- [ ] 5 BINDINGS registrados (c-q, c-d, s-tab, c-v, c-o)
- [ ] 5 action_* handlers existem e fazem o esperado
- [ ] NYX_TUI_TEXTUAL=1 dispatcha para NyxTUI
- [ ] NYX_TUI_TEXTUAL unset OU =0 continua prompt_toolkit (zero regressao default)
- [ ] Smoke default + smoke opt-in ambos PASS
- [ ] Invariantes 14/14
- [ ] Gauntlet rapido PASS
- [ ] Acentuacao rc=0
- [ ] ZERO touches em nyx/agent/repl_app.py

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| `list_command_names()` nao existir em codebase | Fallback `[]`; usuario digita comandos sem completer ate sprint futura |
| `action_paste` falhar fora de TTY (clipboard) | try/except gracioso; no-op silencioso |
| Imports circulares (cli.py importa tui.app que importa banner que importa cli) | Inspecionar; usar lazy import dentro de funcao se necessario |  <!-- noqa-acento -->
| Gauntlet headless tentar dispatch Textual e falhar | Default zero opt-in protege; gauntlet nao seta NYX_TUI_TEXTUAL |
| Spec mencionar Claude/OpenClaude no contexto | Adicionar markers noqa inline durante redacao |  <!-- noqa-anonimato --><!-- noqa-cli-externo -->

---

## Pos-condicao

ONDA-30 fica fechada com cutover OPT-IN. Usuario pode validar a TUI Textual via `NYX_TUI_TEXTUAL=1 ./run.sh` em uso real. Quando confirmar paridade com prompt_toolkit, sprint futura na ONDA-31 troca o default. Por enquanto:
- Default `./run.sh` -> prompt_toolkit (intocado, zero regressao).
- Opt-in `NYX_TUI_TEXTUAL=1 ./run.sh` -> NyxTUI Textual (novo).

---

*"O cutover certo e o que voce pode desfazer com 1 env var." -- principio refactor Nyx-Code.*
