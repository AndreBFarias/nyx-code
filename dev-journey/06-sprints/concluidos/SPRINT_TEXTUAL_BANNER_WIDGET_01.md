## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TEXTUAL-BANNER-WIDGET-01
  title: "BannerWidget(Static) com timer blink local cursor ▌  ▏ (sem race com app.invalidate global)"
  onda: 30
  prioridade: ALTA
  tipo: Feature
  dependencias: [TEXTUAL-INPUT-WIDGET-01]
  desbloqueia: [TEXTUAL-TOOLBAR-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Re-adicionar parametro `cursor: str` em build_banner / _build_compact / _build_wide (subset minimo do que a 187 fez e a 193 reverteu)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "Adicionar classe CSS para BannerWidget (height auto, background)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/banner.py
      reason: "Widget Textual com timer blink local"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_banner_widget.py
      reason: "Teste standalone (5 cenarios)"

  forbidden:
    - "Tocar nyx/agent/repl_app.py (prompt_toolkit fallback durante toda ONDA-30)"
    - "Mudar comportamento default da CLI (Textual NAO e dispatched ainda)"
    - "Compor widget em NyxTUI ainda — so widget isolado"
    - "Re-introduzir helpers build_banner_frame_a/b da sprint 187 (revertidos pela 193)"
    - "Usar app.invalidate() global — apenas self.refresh() local"
    - "Adicionar emoji"

  tests:
    - cmd: "./venv/bin/python nyx/agent/tui/widgets/test_banner_widget.py"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Import `from nyx.agent.tui.widgets.banner import BannerWidget` funciona"
    - "BannerWidget e subclasse de textual.widgets.Static"
    - "Constructor aceita `model`, `tools_count`, `project_name`, `settings`, `blink_period`"
    - "Estado interno `_cursor_full` alterna entre True e False via `_toggle()`"
    - "`_toggle()` chama `self.refresh()` (NAO `app.invalidate()`)"
    - "Skip em NYX_NO_ANIMATION=1 ou sem-TTY"
    - "build_banner() aceita parametro `cursor: str` opcional (default chr(0x258C))"
    - "test_banner_widget.py PASS (5 cenarios)"
    - "Smoke + invariantes 14/14 PASS"
    - "ZERO touches em nyx/agent/repl_app.py"
```

---

# Sprint TEXTUAL-BANNER-WIDGET-01 — BannerWidget redenção

**Status:** PENDENTE
**Data criacao:** 2026-05-22
**Modelo obrigatorio:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> 4a sub-sprint da ONDA-30 (migracao TUI prompt_toolkit -> Textual). Sprints anteriores fechadas: 197 SCAFFOLD (textual==8.2.7), 198 OUTPUT_WIDGET(RichLog), 202 INPUT_WIDGET(Input).
> Esta sprint resgata empiricamente o que a sprint 187 BLINK_SOFT tentou e falhou no prompt_toolkit: cursor `▌` ao lado de `$ nyx.code` piscando suave entre `▌` (U+258C full block) e `▏` (U+258F thin block) a cada 0.5s, sempre visivel.
> Sprint 187 causou flicker observavel porque `banner_blink_loop` async chamava `app.invalidate()` global a cada 0.5s, criando race com streaming de output. Foi revertida pela sprint 193 (commit 1548c10).
> Solucao na ONDA-30: Textual `Static.refresh()` e refresh LOCAL por widget — nenhuma race com outros redraws. Luna `BannerGlitchWidget(Static)` em /home/andrefarias/Desenvolvimento/Luna/src/ui/banner/widgets.py prova viabilidade com timer 150ms em producao.

---

## Solucao proposta

### 1. Re-adicionar parametro `cursor` em `nyx/agent/banner.py`

A sprint 187 introduziu `cursor: str = chr(0x258C)` em `build_banner`, `_build_compact`, `_build_wide`. A sprint 193 reverteu tudo (incluindo helpers `build_banner_frame_a/b`).

Esta sprint re-adiciona APENAS o parametro `cursor`, sem helpers (forbidden re-introducao). Subset minimo:

```python
def build_banner(
    model: str,
    tools_count: int,
    project: str,
    settings: "NyxSettings | None" = None,
    cols: int | None = None,
    memory_count: int | None = None,
    commands_count: int | None = None,
    session_type: str = "REPL",
    cursor: str = chr(0x258C),  # NOVO: default mantem comportamento atual
) -> str:
    """..."""
    if cols is None:
        cols = shutil.get_terminal_size().columns
    if cols < 80:
        return _build_compact(model, tools_count, project, ..., cursor=cursor)
    return _build_wide(model, tools_count, project, ..., cursor=cursor)


def _build_compact(..., cursor: str = chr(0x258C)) -> str:
    # substituir hardcoded {purple}▌{nc} por {purple}{cursor}{nc}
    ...


def _build_wide(..., cursor: str = chr(0x258C)) -> str:
    # substituir hardcoded {purple}▌{nc} por {purple}{cursor}{nc}
    ...
```

Callsites existentes do prompt_toolkit (que nao passam `cursor`) continuam funcionando com default `▌` — zero regressao.

### 2. Criar `nyx/agent/tui/widgets/banner.py`

```python
"""BannerWidget — banner $ nyx.code com cursor blink local na TUI Textual.

ONDA-30 sub-sprint 205. Redencao empirica da sprint 187 BLINK_SOFT
(revertida pela 193): a animacao que causou flicker no prompt_toolkit
agora funciona porque Textual Static.refresh() e refresh LOCAL por
widget — sem race com app.invalidate() global.

Padrao referenciado: Luna BannerGlitchWidget em
/home/andrefarias/Desenvolvimento/Luna/src/ui/banner/widgets.py.
"""

from __future__ import annotations

import os
from typing import Any

from rich.text import Text
from textual.app import RenderResult
from textual.widgets import Static

from nyx.agent.banner import build_banner


class BannerWidget(Static):
    """Banner Nyx com cursor `▌` <-> `▏` piscando local a cada 0.5s.

    Constructor:
      model: nome do modelo Ollama em uso.
      tools_count: quantidade de tools registradas.
      project_name: nome do projeto (CWD basename).
      settings: NyxSettings opcional para banner detalhado.
      blink_period: intervalo do toggle em segundos. Default 0.5.

    Lifecycle:
      on_mount() registra `self.set_interval(blink_period, _toggle)` se TTY
      e !NYX_NO_ANIMATION. _toggle() inverte estado e chama self.refresh()
      — refresh LOCAL ao widget, nao app.invalidate() global.
    """

    DEFAULT_CSS = """
    BannerWidget {
        height: auto;
        background: $surface;
    }
    """

    def __init__(
        self,
        *,
        model: str,
        tools_count: int,
        project_name: str,
        settings: Any = None,
        blink_period: float = 0.5,
    ) -> None:
        super().__init__()
        self._model = model
        self._tools_count = tools_count
        self._project_name = project_name
        self._settings = settings
        self._blink_period = blink_period
        self._cursor_full = True  # True -> chr(0x258C), False -> chr(0x258F)
        self._blink_timer = None

    def render(self) -> RenderResult:
        cursor = chr(0x258C) if self._cursor_full else chr(0x258F)
        ansi_str = build_banner(
            self._model,
            self._tools_count,
            self._project_name,
            settings=self._settings,
            cursor=cursor,
        )
        return Text.from_ansi(ansi_str)

    def on_mount(self) -> None:
        if os.environ.get("NYX_NO_ANIMATION") == "1":
            return  # skip silencioso em CI/headless
        self._blink_timer = self.set_interval(self._blink_period, self._toggle)

    def _toggle(self) -> None:
        self._cursor_full = not self._cursor_full
        self.refresh()  # refresh LOCAL — sem race global


__all__ = ["BannerWidget"]
```

### 3. Teste isolado `nyx/agent/tui/widgets/test_banner_widget.py`

```python
"""Teste isolado da BannerWidget (ONDA-30 sub-sprint 205).

Standalone (nao pytest — ADR-014). Roda via:
  ./venv/bin/python nyx/agent/tui/widgets/test_banner_widget.py

Esperado: imports OK, instanciacao OK, 5 cenarios PASS, exit 0.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Bootstrap sys.path quando invocado via path direto.
_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from nyx.agent.tui.widgets.banner import BannerWidget
from textual.widgets import Static


def _log(msg: str) -> None:
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()


def main() -> int:
    # 1. Heranca
    assert issubclass(BannerWidget, Static), "BannerWidget deve herdar de Static"
    _log("[1/5] BannerWidget herda de Static: OK")

    # 2. Instanciacao padrao
    widget = BannerWidget(
        model="qwen2.5-coder:3b",
        tools_count=35,
        project_name="Nyx-Code",
    )
    assert widget._cursor_full is True, "Estado inicial deve ser True (full block)"
    assert widget._blink_period == 0.5, "Default blink_period deve ser 0.5"
    _log("[2/5] BannerWidget instanciacao padrao: OK")

    # 3. Constructor com blink_period custom
    widget2 = BannerWidget(
        model="qwen2.5-coder:3b",
        tools_count=35,
        project_name="Nyx-Code",
        blink_period=1.0,
    )
    assert widget2._blink_period == 1.0
    _log("[3/5] BannerWidget blink_period custom: OK")

    # 4. _toggle alterna estado
    initial = widget._cursor_full
    widget._toggle()
    assert widget._cursor_full == (not initial), "_toggle deve inverter _cursor_full"
    _log("[4/5] BannerWidget _toggle alterna estado: OK")

    # 5. render() retorna Text (ou NoActiveAppError fora de App)
    try:
        result = widget.render()
        assert "nyx" in str(result).lower(), "render deve conter 'nyx'"
        _log("[5/5] BannerWidget render: OK")
    except Exception as exc:
        if type(exc).__name__ in ("NoActiveAppError",):
            _log("[5/5] BannerWidget render: OK (NoActiveAppError esperado fora de App context)")
        else:
            raise

    _log("\nTODOS OS 5 TESTES PASSARAM")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 4. CSS update `nyx/agent/tui/styles/nyx.tcss`

```css
/* BannerWidget -- sub-sprint 205 (TEXTUAL-BANNER-WIDGET-01).
 * Banner Nyx com cursor blink local; refresh por-widget, sem race global.
 */
BannerWidget {
    height: auto;
    background: $surface;
}
```

---

## Diff esperado

```
~ 3 arquivos modificados (banner.py, nyx.tcss, e na verdade banner.py modificado)
+ 2 arquivos criados (banner.py do widget + test)
+ ~120 linhas
```

---

## Comandos de verificacao

```bash
# 1. Imports + teste isolado
./venv/bin/python nyx/agent/tui/widgets/test_banner_widget.py

# 2. Smoke (CLI ainda prompt_toolkit, sem regressao)
./run.sh --smoke

# 3. Invariantes
bash scripts/sprint_invariants.sh

# 4. Acentuacao
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/banner.py \
    nyx/agent/tui/widgets/banner.py \
    nyx/agent/tui/widgets/test_banner_widget.py \
    nyx/agent/tui/styles/nyx.tcss

# 5. Validacao visual standalone (opcional)  <!-- noqa-acento -->
cat > /tmp/nyx_banner_demo.py << 'PYEOF'
import sys
sys.path.insert(0, "/home/andrefarias/Desenvolvimento/Nyx-Code")
from textual.app import App, ComposeResult
from nyx.agent.tui.widgets.banner import BannerWidget

class DemoApp(App):
    def compose(self) -> ComposeResult:
        yield BannerWidget(
            model="qwen2.5-coder:3b",
            tools_count=35,
            project_name="Nyx-Code",
        )

if __name__ == "__main__":
    DemoApp().run()
PYEOF
# rodar manualmente: ./venv/bin/python /tmp/nyx_banner_demo.py
# observar cursor piscando suave (alternando 2 glifos, nunca apagando)
```

---

## Criterio binario de aceite

- [ ] `from nyx.agent.tui.widgets.banner import BannerWidget` funciona
- [ ] BannerWidget e subclasse de Static
- [ ] Constructor aceita 5 parametros nomeados (model, tools_count, project_name, settings, blink_period)
- [ ] _toggle alterna _cursor_full e chama self.refresh()
- [ ] Skip em NYX_NO_ANIMATION=1
- [ ] test_banner_widget.py PASS (5 cenarios)
- [ ] Smoke + invariantes 14/14 PASS
- [ ] Acentuacao rc=0 nos 4 arquivos
- [ ] ZERO touches em nyx/agent/repl_app.py

---

## Riscos

| Risco | Mitigacao |
|-------|-----------|
| `cursor` param em build_banner quebrar callsites prompt_toolkit | Default `chr(0x258C)` mantem comportamento; callsites antigos nao passam o param |
| `Text.from_ansi()` nao renderizar cores ANSI inline corretamente em Static | Testar empiricamente via demo standalone antes de marcar CONCLUIDA |
| Timer 0.5s consumir CPU em background | Luna prova viabilidade com timer 150ms em producao; 500ms e ainda mais leve |
| Race entre _toggle e outras tasks | Textual `Static.refresh()` e LOCAL — invalidacao por widget, nao por app |  <!-- noqa-acento -->
| Sanitizer atacar arquivos protegidos durante a sprint | Defense-in-depth 5 camadas ativa; invariante #14 bloqueia commit corrompido |

---

## Proximas sub-sprints (preview)

- **206 TEXTUAL-TOOLBAR-01**: Toolbar(Static) com reactive properties para ctx/iter/lidos/modif/glyph_state/modo.
- **207 TEXTUAL-CUTOVER-01**: Compoe 4 widgets em NyxTUI, registra bindings (c-q, c-d, s-tab), trocar default da CLI, gauntlet PASS.

---

*"A redencao empirica de uma sprint revertida e a melhor licao sobre arquitetura." -- principio refactor Nyx-Code.*
