# SPRINT TUI-REDESIGN-26-04 — Card encerramento grid 3x2 com bordas

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-26-04
  title: "render_session_stats_card vira grid 3x2 com box drawing (cels separadas por │)"
  onda: 26
  bloco: 26.1 Fidelidade visual
  prioridade: ALTA
  tipo: UX
  dependencias: [TUI-REDESIGN-26-03]
  desbloqueia: []
  origem: "Mockup nyx-session-render.jsx mostra encerramento em grid de boxes (Iterações | Arquivos lidos | Arquivos modif) sobre (Tempo | Tokens | Sessão). TUI atual usa 3 linhas tabulares sem bordas."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_session_stats_card reescrito: ╭─┬─┬─╮ ... ├─┼─┼─┤ ... ╰─┴─┴─╯. Fallback linhas inline (versão 25-14) quando cols < 80"

  forbidden:
    - "Quebrar fallback < 80 cols"
    - "Glyphs fora de Box Drawing (U+2500-U+257F)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Grid 3x2 com bordas ╭ ┬ ╮ │ ├ ┼ ┤ ╰ ┴ ╯"
    - "Fallback linhas inline preservado para cols < 80"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-26-04

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
