# SPEC

```yaml
sprint:
  id: TUI-BANNER-DOCK-TOP-01
  title: "BannerWidget recebe dock:top no DEFAULT_CSS para ficar fixo no topo"
  onda: 32
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [TUI-CSS-LUNA-ADOPT-01]
  desbloqueia: [TUI-AGENT-BRIDGE-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/banner.py
      reason: "Adicionar dock: top + height: auto ao DEFAULT_CSS interno"

  creates: []
  removes: []

  forbidden:
    - "Modificar nyx.tcss (CSS canônico já tem BannerWidget {dock: top} da sprint 1; aqui só DEFAULT_CSS do widget para defesa)"
    - "Adicionar emoji"
    - "Mencionar IA externa" <!-- noqa-anonimato -->

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "./venv/bin/python -c 'from nyx.agent.tui.widgets.banner import BannerWidget; assert \"dock: top\" in BannerWidget.DEFAULT_CSS; print(\"OK dock top no DEFAULT_CSS\")'"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "BannerWidget.DEFAULT_CSS contém `dock: top`"
    - "BannerWidget.DEFAULT_CSS contém `height: auto`"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-BANNER-DOCK-TOP-01 — Banner fixo no topo via dock

**Status:** PENDENTE
**Data criação:** 2026-05-28
**Modelo obrigatório:** Modelo Opus 4.7 (1M) (sem subagentes)

---

## Contexto

> Bug L2 do AUDIT_LAYOUT_2026_05_28: banner sumia ao rolar conversa porque vivia
> dentro do output_buffer (caminho prompt_toolkit). Na nova TUI Textual, banner
> deve ser Widget separado com dock: top.
>
> Sprint anterior: TUI-CSS-LUNA-ADOPT-01 já tem `BannerWidget { dock: top }`
> no nyx.tcss. Esta sprint reforça via DEFAULT_CSS interno do widget para defesa
> contra ausência de CSS_PATH (testes isolados, fallback).

---

## Problema

`BannerWidget` (sprint 205) tem `DEFAULT_CSS` mas sem `dock: top`. Quando usado
fora do contexto NyxTUI (testes isolados, futura reutilização), o banner pode
cair no fluxo do compose como widget normal -- defeito de defesa.

---

## Solução proposta

Adicionar `dock: top` + `height: auto` ao `DEFAULT_CSS` do `BannerWidget`.
Defesa em profundidade: CSS canônico (nyx.tcss) define para o app principal;
DEFAULT_CSS garante para qualquer instanciação isolada.

---

## Arquivos alvo

### `/home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/banner.py`

**Antes (DEFAULT_CSS atual):**
```python
DEFAULT_CSS = """
BannerWidget {
    height: auto;
    background: $surface;
}
"""
```

**Depois:**
```python
DEFAULT_CSS = """
BannerWidget {
    dock: top;
    height: auto;
    background: $surface;
    padding: 0 1;
}
"""
```

**Mudanças:**
- Adiciona `dock: top` (banner fixo)
- Mantém `height: auto`
- Adiciona `padding: 0 1` (paridade com nyx.tcss canônico da sprint 1)

---

## Diff esperado

```
~ 1 arquivo modificado (banner.py)
+ ~2 linhas líquidas no DEFAULT_CSS
```

---

## Comandos de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Smoke
./run.sh --smoke

# 2. DEFAULT_CSS contém dock: top
./venv/bin/python -c "
from nyx.agent.tui.widgets.banner import BannerWidget
css = BannerWidget.DEFAULT_CSS
assert 'dock: top' in css, f'dock: top ausente: {css!r}'
assert 'height: auto' in css, f'height: auto ausente'
print('OK BannerWidget.DEFAULT_CSS = ', repr(css))
"

# 3. NyxTUI opt-in ainda sobe
NYX_TUI_TEXTUAL=1 timeout 5 ./run.sh --smoke || true
# (smoke não dispara TUI; teste runtime fica para validação visual final)

# 4. Invariantes
bash scripts/sprint_invariants.sh

# 5. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/tui/widgets/banner.py

# 6. Ruff
/home/andrefarias/.local/bin/ruff check nyx/agent/tui/widgets/banner.py
```

---

## Critério binário de aceite

- [ ] `BannerWidget.DEFAULT_CSS` contém `dock: top`
- [ ] `BannerWidget.DEFAULT_CSS` contém `height: auto`
- [ ] Smoke ok + invariantes 14/14
- [ ] Ruff limpo

---

## Proof-of-work obrigatório

Conforme template V2.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `dock: top` + `height: auto` é redundante com nyx.tcss | Aceitável -- defense in depth; CSS_PATH sobrescreve DEFAULT_CSS quando ambos existem |

---

*"Que o teto seja firme, mas o céu ainda visível." -- Manoel de Barros (paráfrase)*
