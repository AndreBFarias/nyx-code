# SPRINT TUI-REDESIGN-26-02 — Header inline-leading com meta dinâmica

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-26-02
  title: "render_assistant_start abre turno com '◆ Nyx · Ns · tokens N' ANTES do streaming"
  onda: 26
  bloco: 26.1 Fidelidade visual
  prioridade: ALTA
  tipo: UX
  dependencias: [TUI-REDESIGN-26-01]
  desbloqueia: []
  origem: "Mockup nyx-session-render.jsx mostra header ◆ Nyx · 1.4s · 78 tokens NO TOPO do turno. Hoje meta aparece só no fim via render_assistant_end."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_assistant_start aceita start_monotonic e imprime header com placeholder de tempo (--s) que será preenchido pelo spinner. render_assistant_end só fecha (não duplica meta)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Passar request_started para render_assistant_start"

  forbidden:
    - "Duplicar meta entre start e end"
    - "Quebrar streaming (header precisa aparecer antes dos tokens)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "render_assistant_start emite '◆ Nyx · Ns · tokens N' antes do streaming"
    - "render_assistant_end emite divisor de fechamento (sem repetir meta inteira)"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-26-02

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
