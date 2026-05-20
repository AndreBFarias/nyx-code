# SPRINT VISUAL-LAYOUT-04 — Glifos por aesthetic (box, junctions, spinners)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISUAL-LAYOUT-04
  title: "Glifos de box/junctions/spinners variam por aesthetic"
  onda: 24
  bloco: 24.2 Visual Layout
  prioridade: BAIXA
  tipo: Feature
  dependencias: [VISUAL-LAYOUT-01, VISUAL-LAYOUT-03]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Resolver box chars + spinner via theme_manager em vez de hardcode"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/theme_manager.py
      reason: "Adicionar get_glyphs() que respeita aesthetic"
  creates: []
  removes: []

  forbidden:
    - "Tocar invariante #14 (○ ◐ ●) — esses são canônicos universais, não viram alternáveis"

  tests:
    - cmd: "NYX_AESTHETIC=cyberpunk ./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Box chars de aesthetic 'cyberpunk' = ┏┓┗┛ ━ ┃ (pesado)"
    - "Box chars de aesthetic 'arcano' = ╭╮╰╯ ─ │ (suave, padrão)"
    - "Glifos warming/cold/warm (○ ◐ ●) preservados em TODOS aesthetics (invariante #14)"
    - "Smoke ok em todos aesthetics"
```

---

# Sprint VISUAL-LAYOUT-04 — Glifos por aesthetic

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

VISUAL-LAYOUT-01 já define glifos em cada aesthetic. VISUAL-LAYOUT-04 conecta o consumo nos pontos de render (output.py). Cuidado: ○ ◐ ● são canônicos por invariante #14 (UX-BUG-02B + UX-LOOP-VISIBILITY-01) e NÃO alternáveis por aesthetic.

---

## Solução

`theme_manager.get_glyphs()` retorna dict com chaves `tl, tr, bl, br, h, v`. Funções de render em `output.py` (ex: `render_box`, `render_card`) consomem via essa função.

Cyberpunk usa box pesado (┏┓┗┛); arcano usa suave (╭╮╰╯); brutalist usa ASCII puro (+-|); etc.

---

## Critério binário de aceite

- [ ] `theme_manager.get_glyphs()` implementado
- [ ] `output.py` consome via get_glyphs em render_box/render_card
- [ ] `NYX_AESTHETIC=cyberpunk ./run.sh` mostra box ┏┓
- [ ] `NYX_AESTHETIC=brutalist ./run.sh` mostra box ASCII puro
- [ ] `○ ◐ ●` permanecem em qualquer aesthetic (toolbar warming/cold/warm)
- [ ] Invariantes 14/14
- [ ] Sprint movida → `concluidos/`
- [ ] Commit `feat(VISUAL-LAYOUT-04): glifos de box/junctions variam por aesthetic; ○ ◐ ● preservados`

---

*"O contorno desenha a cultura." — VISUAL-LAYOUT-04*
