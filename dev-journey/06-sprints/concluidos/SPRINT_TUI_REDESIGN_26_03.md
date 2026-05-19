# SPRINT TUI-REDESIGN-26-03 — Tool chip com glyph-per-tool + ações chip à direita

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-26-03
  title: "render_tool_chip usa TOOL_GLYPHS por tool (≡, +, ▸, ⌕) e alinha ações de erro à direita"
  onda: 26
  bloco: 26.1 Fidelidade visual
  prioridade: ALTA
  tipo: UX
  dependencias: [TUI-REDESIGN-26-02]
  desbloqueia: []
  origem: "Mockup tem glyph distintivo por tool e ações de erro como chips alinhados à direita da linha do chip."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "Novo mapa TOOL_GLYPHS = {Read:≡, Write:+, Edit:*, Bash:▸, Grep:⌕, Glob:..., Multi:◆}"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_tool_chip usa TOOL_GLYPHS.get(name, ●). Erros classificáveis: chips de ações alinhados à direita ou fallback abaixo se sem largura"

  forbidden:
    - "Emoji (Unicode Other_Symbol fora de geometric shapes)"
    - "Hardcode hex"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"
    - cmd: "./venv/bin/python -c 'from nyx.themes.design_tokens import TOOL_GLYPHS; assert len(TOOL_GLYPHS) >= 6'"
      timeout: 5
      deve_passar: true

  acceptance_criteria:
    - "TOOL_GLYPHS com >= 6 entries"
    - "render_tool_chip usa glyph apropriado"
    - "Ações de erro chips alinhados à direita quando largura permite"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-26-03

**Status:** CONCLUIDA_PARCIAL
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18 (glyph-per-tool feito, alinhamento ações à direita pendente refinamento — sincronizado em SPRINT_ORDER-REFRESH-01 2026-05-19)
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
