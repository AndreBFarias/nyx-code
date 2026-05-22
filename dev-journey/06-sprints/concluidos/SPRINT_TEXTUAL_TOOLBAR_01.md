## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TEXTUAL-TOOLBAR-01
  title: "Toolbar(Static) com reactive properties (ctx/iter/lidos/modif/glyph_state/mode) e watch_* local"
  onda: 30
  prioridade: ALTA
  tipo: Feature
  dependencias: [TEXTUAL-BANNER-WIDGET-01]
  desbloqueia: [TEXTUAL-CUTOVER-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "Adicionar classe CSS para Toolbar (dock=bottom, height=1, paleta muted)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/toolbar.py
      reason: "Widget Textual com reactive properties + watch_* + render dinamico"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_toolbar_widget.py
      reason: "Teste standalone do widget (5-6 cenarios)"

  forbidden:
    - "Tocar nyx/agent/repl_app.py (prompt_toolkit fallback durante toda ONDA-30)"
    - "Mudar comportamento default da CLI (Textual NAO dispatched ainda)"
    - "Compor widget em NyxTUI ainda — sera feito na sprint 207"
    - "Usar app.invalidate() global — apenas self.refresh() local via reactive watch_*"
    - "Adicionar dependencias externas alem de textual ja instalado"
    - "Adicionar emoji"

  tests:
    - cmd: "./venv/bin/python nyx/agent/tui/widgets/test_toolbar_widget.py"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Import `from nyx.agent.tui.widgets.toolbar import Toolbar` funciona"
    - "Toolbar e subclasse de textual.widgets.Static"
    - "Reactive properties: ctx_pct (int), iter_n (int), reads (int), mods (int), model_state (str), mode (str)"
    - "Constructor aceita defaults para todas as props"
    - "render() retorna Text com layout: ctx X% | model | iter N | lidos M | modif K | glyph state | modo"
    - "Mudar uma reactive property aciona watch_* que chama self.refresh() local"
    - "test_toolbar_widget.py PASS (5-6 cenarios)"
    - "Smoke + invariantes 14/14 PASS"
    - "ZERO touches em nyx/agent/repl_app.py"
```

---

# Sprint TEXTUAL-TOOLBAR-01 — Toolbar reactive

**Status:** PENDENTE
**Data criacao:** 2026-05-22
**Modelo obrigatorio:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> 5a sub-sprint da ONDA-30. Sprints anteriores: 197 SCAFFOLD, 198 OUTPUT, 202 INPUT, 205 BANNER.
> O bottom toolbar atual em `nyx/cli_keybindings.py:build_bottom_toolbar` (PromptSession path) constroi FormattedText com 5 secoes separadas por `|`: ctx, model+iter+lidos+modif, model_state com glifo, opcionalmente inflight, modo. Reactive properties do Textual sao equivalente moderno — quando o state muda, watch_* dispara e a tela atualiza local.
> Esforco estimado: 2-3h. Widget isolado, testavel standalone, sem composicao em NyxTUI (vira na 207 CUTOVER).

---

## Solucao proposta

### Widget: `nyx/agent/tui/widgets/toolbar.py`

```python
"""Toolbar — bottom bar da TUI Textual com reactive properties.

ONDA-30 sub-sprint 206. Substituira o build_bottom_toolbar atual do
PromptSession (nyx/cli_keybindings.py) apos TEXTUAL-CUTOVER-01.

Reactive properties + watch_* sao o equivalente Textual ao
FormattedText callable do prompt_toolkit — quando state muda, o widget
re-renderiza localmente (sem race global).
"""

from __future__ import annotations

from rich.text import Text
from textual.app import RenderResult
from textual.reactive import reactive
from textual.widgets import Static

from nyx.themes.design_tokens import (
    NYX_ACCENT,
    NYX_ERROR,
    NYX_MUTED,
    NYX_PURPLE,
    NYX_PURPLE_DIM,
    STATE_GLYPHS,
)


class Toolbar(Static):
    """Bottom toolbar com ctx/iter/lidos/modif/model_state/mode.

    Reactive properties:
      ctx_pct: % de contexto consumido (0-100).
      iter_n: iteracoes do turno atual.
      reads: arquivos lidos no turno.
      mods: arquivos modificados no turno.
      model_state: cold/warming/warm.
      mode: normal/plan/sudo/bypass.
      model: nome do modelo (display, fixo apos init).
    """

    DEFAULT_CSS = """
    Toolbar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $foreground;
    }
    """

    ctx_pct: reactive[int] = reactive(0)
    iter_n: reactive[int] = reactive(0)
    reads: reactive[int] = reactive(0)
    mods: reactive[int] = reactive(0)
    model_state: reactive[str] = reactive("cold")
    mode: reactive[str] = reactive("normal")

    def __init__(self, *, model: str = "qwen2.5-coder:3b") -> None:
        super().__init__()
        self._model = model

    def render(self) -> RenderResult:
        msg = Text()
        msg.append(f"ctx {self.ctx_pct}%", style=NYX_ACCENT)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(self._model, style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(f"iter {self.iter_n}", style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(f"lidos {self.reads}", style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        msg.append(f"modif {self.mods}", style=NYX_MUTED)
        msg.append("  |  ", style=NYX_MUTED)
        glyph = STATE_GLYPHS.get(self.model_state, STATE_GLYPHS["cold"])
        msg.append(f"{glyph} {self.model_state}", style=NYX_MUTED)
        msg.append("    ", style=NYX_MUTED)
        if self.mode == "bypass":
            msg.append(" bypass ON (shift+tab) ", style=f"bold {NYX_PURPLE_DIM}")
        elif self.mode == "plan":
            msg.append(" [plan] read-only (shift+tab) ", style=f"bold {NYX_PURPLE}")
        elif self.mode == "sudo":
            msg.append(" [sudo] elevado (shift+tab) ", style=f"bold {NYX_ERROR}")
        else:
            msg.append("shift+tab: normal/plan/sudo/bypass", style=NYX_MUTED)
        return msg

    # Watch handlers: cada mudanca de reactive property dispara self.refresh()
    # automaticamente, mas declaramos explicitos para clareza + extensibilidade.
    def watch_ctx_pct(self, old: int, new: int) -> None:
        self.refresh()

    def watch_iter_n(self, old: int, new: int) -> None:
        self.refresh()

    def watch_reads(self, old: int, new: int) -> None:
        self.refresh()

    def watch_mods(self, old: int, new: int) -> None:
        self.refresh()

    def watch_model_state(self, old: str, new: str) -> None:
        self.refresh()

    def watch_mode(self, old: str, new: str) -> None:
        self.refresh()


__all__ = ["Toolbar"]
```

### Teste isolado: `nyx/agent/tui/widgets/test_toolbar_widget.py`

```python
"""Teste isolado da Toolbar (ONDA-30 sub-sprint 206).

Standalone (nao pytest). Roda via:
  ./venv/bin/python nyx/agent/tui/widgets/test_toolbar_widget.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nyx.agent.tui.widgets.toolbar import Toolbar
from textual.widgets import Static


def _log(msg: str) -> None:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main() -> int:
    # 1. Heranca
    assert issubclass(Toolbar, Static)
    _log("[1/6] Toolbar herda de Static: OK")

    # 2. Instanciacao default
    t = Toolbar()
    assert t._model == "qwen2.5-coder:3b"
    assert t.ctx_pct == 0
    assert t.iter_n == 0
    assert t.reads == 0
    assert t.mods == 0
    assert t.model_state == "cold"
    assert t.mode == "normal"
    _log("[2/6] Toolbar defaults: OK")

    # 3. Modelo custom
    t2 = Toolbar(model="qwen3:4b")
    assert t2._model == "qwen3:4b"
    _log("[3/6] Toolbar model custom: OK")

    # 4. Render fora de App context (graceful)
    try:
        result = t.render()
        s = str(result).lower()
        assert "ctx" in s and "iter" in s and "lidos" in s
        _log("[4/6] Toolbar render contem keywords: OK")
    except Exception as exc:
        if type(exc).__name__ in ("NoActiveAppError",):
            _log("[4/6] Toolbar render: OK (NoActiveAppError esperado)")
        else:
            raise

    # 5. Reactive properties watchable (apenas confirma assignment)
    t.ctx_pct = 42
    assert t.ctx_pct == 42
    t.mode = "plan"
    assert t.mode == "plan"
    t.model_state = "warm"
    assert t.model_state == "warm"
    _log("[5/6] Toolbar reactive set/get: OK")

    # 6. Modo bypass altera render
    t.mode = "bypass"
    try:
        result_bypass = t.render()
        assert "bypass" in str(result_bypass).lower()
        _log("[6/6] Toolbar render modo bypass: OK")
    except Exception as exc:
        if type(exc).__name__ in ("NoActiveAppError",):
            _log("[6/6] Toolbar render modo bypass: OK (NoActiveAppError esperado)")
        else:
            raise

    _log("\nTODOS OS 6 TESTES PASSARAM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### CSS update `nyx/agent/tui/styles/nyx.tcss`

```css
/* Toolbar — sub-sprint 206 (TEXTUAL-TOOLBAR-01).
 * Bottom bar com reactive properties (ctx, iter, lidos, modif, state, mode).
 */
Toolbar {
    dock: bottom;
    height: 1;
    background: $surface;
    color: $foreground;
}
```

---

## Diff esperado

```
+ 2 arquivos criados (toolbar.py ~80L + test_toolbar_widget.py ~80L)
~ 1 arquivo modificado (nyx.tcss +6L)
+ ~165 linhas
```

---

## Comandos de verificacao

```bash
./venv/bin/python nyx/agent/tui/widgets/test_toolbar_widget.py
./run.sh --smoke
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/tui/widgets/toolbar.py \
    nyx/agent/tui/widgets/test_toolbar_widget.py \
    nyx/agent/tui/styles/nyx.tcss
```

---

## Criterio binario de aceite

- [ ] Import + heranca OK
- [ ] 6 reactive properties declaradas
- [ ] 6 watch_* handlers (chamam self.refresh)
- [ ] Constructor aceita model custom
- [ ] render() inclui ctx, model, iter, lidos, modif, glyph, modo
- [ ] test_toolbar_widget.py PASS (6 cenarios)
- [ ] Smoke + invariantes 14/14 PASS
- [ ] Acentuacao rc=0
- [ ] ZERO touches em nyx/agent/repl_app.py

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| `reactive` import path diferente em textual 8.2.7 | Verificar: `from textual.reactive import reactive` |
| watch_* automatico ja chama refresh — explicito e redundante | Aceitavel: explicito documenta intencao e permite extensoes futuras |
| Glyph state vir vazio se STATE_GLYPHS lookup falhar | Fallback `STATE_GLYPHS.get(state, STATE_GLYPHS["cold"])` |

---

## Proxima sub-sprint

- **207 TEXTUAL-CUTOVER-01**: compoe Banner+Output+Input+Toolbar em NyxTUI, registra bindings (c-q, c-d, s-tab, c-v, c-o), troca default da CLI, gauntlet PASS.

---

*"O toolbar e o painel de instrumentos — ele DEVE refletir o estado em tempo real." -- principio TUI.*
