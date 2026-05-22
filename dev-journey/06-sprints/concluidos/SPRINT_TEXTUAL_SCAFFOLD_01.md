## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TEXTUAL-SCAFFOLD-01
  title: "Scaffold ONDA-30: adiciona textual>=0.76 + cria nyx/agent/tui/ vazio (primeira sub-sprint)"
  onda: 30
  prioridade: ALTA
  tipo: Infra
  dependencias: [TUI-TEXTUAL-MIGRATION-PLAN-01]
  desbloqueia: [TEXTUAL-OUTPUT-WIDGET-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/pyproject.toml
      reason: "Adicionar `textual>=0.76` como dependência opcional ou principal"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/requirements.txt
      reason: "Adicionar textual se este arquivo for fonte de instalação"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/__init__.py
      reason: "Placeholder do pacote tui"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "App principal Textual (placeholder com docstring e classe NyxTUI(App) vazia)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/__init__.py
      reason: "Placeholder do sub-pacote widgets"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "CSS placeholder com paleta turquesa+roxo+verde (ADR-023) — só tokens iniciais"

  forbidden:
    - "Migrar features ainda — só scaffold"
    - "Tocar nyx/agent/repl_app.py (fica intocado durante toda a ONDA-30 como fallback NYX_LEGACY_REPL)"
    - "Quebrar smoke ou gauntlet"
    - "Adicionar emoji"
    - "Mudar comportamento padrão da CLI — Textual NÃO é dispatched ainda"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
    - cmd: "./venv/bin/python -c 'from nyx.agent.tui.app import NyxTUI; print(NyxTUI.__name__)'"
      timeout: 10
      deve_passar: true
    - cmd: "./venv/bin/python -c 'import textual; print(textual.__version__)'"
      timeout: 10
      deve_passar: true

  acceptance_criteria:
    - "textual>=0.76 instalado no venv (verificar via `pip show textual`)"
    - "Imports `from nyx.agent.tui.app import NyxTUI` funciona sem erro"
    - "NyxTUI é subclasse de textual.app.App"
    - "nyx/agent/tui/styles/nyx.tcss existe e é parsable pelo Textual (validação via App carregando CSS_PATH)"
    - "Smoke + invariantes 14/14 PASS"
    - "CLI continua usando prompt_toolkit como default (NYX_LEGACY_REPL=1 path ainda principal)"
    - "Acentuação PT-BR rc=0"
```

---

# Sprint TEXTUAL-SCAFFOLD-01 — Primeira sub-sprint ONDA-30

**Status:** PENDENTE
**Data criação:** 2026-05-22
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> Sprint 194 (TUI-TEXTUAL-MIGRATION-PLAN-01) materializou o planejamento da ONDA-30: migrar TUI Nyx-Code de prompt_toolkit para Textual. 6 sub-sprints projetadas (196-201). Esta é a primeira.
> Esforço estimado: 1-2h. Escopo: scaffold puro — adicionar dependência + criar estrutura de diretórios e placeholders. Zero feature.

---

## Solução proposta

### 1. Adicionar dependência

Em `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existentes ...
    "textual>=0.76",
]
```

Em `requirements.txt` (se for fonte ativa):

```
textual>=0.76
```

Instalar: `./venv/bin/pip install textual>=0.76`

### 2. Criar estrutura

```
nyx/agent/tui/
├── __init__.py           # docstring do pacote
├── app.py                # NyxTUI(App) placeholder
├── widgets/
│   └── __init__.py       # docstring
└── styles/
    └── nyx.tcss          # CSS placeholder
```

### 3. Conteúdo dos placeholders

`nyx/agent/tui/__init__.py`:

```python
"""Pacote da TUI Textual do Nyx-Code (ONDA-30).

Substituirá nyx/agent/repl_app.py após a sub-sprint TEXTUAL-CUTOVER-01.
Durante a transição, é apenas estrutura placeholder; o caminho default
da CLI continua usando prompt_toolkit via nyx.agent.repl_app.
"""
```

`nyx/agent/tui/app.py`:

```python
"""App principal Textual do Nyx-Code (placeholder ONDA-30 SCAFFOLD).

Esta classe é o ponto de entrada Textual que substituirá repl_app.py
após a cutover. Por ora, é apenas scaffold — sem widgets, sem bindings,
sem lifecycle.

Validação: from nyx.agent.tui.app import NyxTUI; NyxTUI deve ser
subclasse de textual.app.App.
"""

from __future__ import annotations

from pathlib import Path

from textual.app import App


class NyxTUI(App):
    """Placeholder ONDA-30. Sub-sprints filhas (197+) adicionam features."""

    CSS_PATH = Path(__file__).parent / "styles" / "nyx.tcss"

    BINDINGS: list = []  # TEXTUAL-CUTOVER-01 popula com c-q, c-d, s-tab, etc.

    async def on_mount(self) -> None:
        """Mount placeholder — features virão das sub-sprints filhas."""
        pass


__all__ = ["NyxTUI"]
```

`nyx/agent/tui/widgets/__init__.py`:

```python
"""Widgets do pacote tui — banner, output, input, toolbar.

Sub-sprints filhas (197-200) implementam cada um.
"""
```

`nyx/agent/tui/styles/nyx.tcss`:

```css
/* Nyx-Code TUI styles — ONDA-30 SCAFFOLD placeholder.
 * Paleta canônica (ADR-023): turquesa #00D4AA + roxo #9D4EDD + verde #4ADE80.
 * Sub-sprints filhas populam cada widget classes.
 */

App {
    background: $surface;
}

/* Tokens de cor reservados para uso pelas sub-sprints. */
$accent: #00D4AA;
$primary: #9D4EDD;
$success: #4ADE80;
```

---

## Diff esperado

```
+ 4 arquivos criados (~80 linhas)
~ 1-2 arquivos modificados (pyproject.toml, possivelmente requirements.txt)
+ ~5 linhas (dependência)
```

---

## Comandos de verificação

```bash
# 1. Install
./venv/bin/pip install textual>=0.76 2>&1 | tail -3
./venv/bin/pip show textual | head -3

# 2. Imports
./venv/bin/python -c "from nyx.agent.tui.app import NyxTUI; print(NyxTUI.__name__, NyxTUI.__mro__[1].__name__)"
# esperado: "NyxTUI App"

# 3. CSS parseable
./venv/bin/python -c "
from nyx.agent.tui.app import NyxTUI
app = NyxTUI()
print('CSS_PATH:', app.CSS_PATH, 'exists:', app.CSS_PATH.exists())
"

# 4. Smoke + invariantes
./run.sh --smoke
bash scripts/sprint_invariants.sh

# 5. CLI default continua prompt_toolkit (não regrediu)
./run.sh &
PID=$!
sleep 4
tmux capture-pane -t 0 -p 2>/dev/null | head -5 || ps -p $PID > /dev/null && echo "CLI default ainda roda"
kill $PID 2>/dev/null

# 6. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/tui/__init__.py \
    nyx/agent/tui/app.py \
    nyx/agent/tui/widgets/__init__.py
```

---

## Critério binário de aceite

- [ ] `pip show textual` retorna 0.76+
- [ ] `from nyx.agent.tui.app import NyxTUI` funciona
- [ ] NyxTUI é subclasse de App
- [ ] nyx.tcss existe e é encontrado pelo CSS_PATH
- [ ] Smoke `boot ok` exit 0
- [ ] Invariantes 14/14 PASS
- [ ] CLI default continua prompt_toolkit (sem regressão)
- [ ] Acentuação rc=0

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Textual instalado puxa muitas deps (rich, markdown-it, linkify, ...) | Aceito — Textual é pesado mas todas as deps são puras Python; sem ABI C |
| Versão Textual mínima 0.76 conflitar com rich do projeto | Verificar pip resolve antes; se conflitar, downgrade textual para versão compatível |
| Mudança em pyproject.toml quebra install scripts | `./run.sh --smoke` cobre boot; se quebrar, ajustar fallback |
| CSS_PATH com Path(__file__).parent não resolve no install editable | Testar; alternativa: hardcoded relative |

---

## Próximas sub-sprints (preview)

- **197 TEXTUAL-OUTPUT-WIDGET-01**: OutputWidget(RichLog) recebendo append de mensagens.
- **198 TEXTUAL-INPUT-WIDGET-01**: InputWidget(Input) ancorado no rodapé + completer.
- **199 TEXTUAL-BANNER-WIDGET-01**: BannerWidget(Static) com timer blink local.
- **200 TEXTUAL-TOOLBAR-01**: Toolbar(Static) com reactive properties.
- **201 TEXTUAL-CUTOVER-01**: Trocar default + gauntlet PASS.

---

*"O primeiro passo de uma migração é admitir que ela existe." -- princípio refactor Nyx-Code.*
