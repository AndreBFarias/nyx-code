# SPRINT TUI-REDESIGN-26-01 — Bubble user soft-box ANSI

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-26-01
  title: "render_user_input emite caixa ╭─ Nome ─╮ + corpo + ╰────────╯ em ACCENT (schema hybrid)"
  onda: 26
  bloco: 26.1 Fidelidade visual
  prioridade: ALTA
  tipo: UX
  dependencias: [COCKPIT-WEB-REDESIGN-03]
  desbloqueia: []
  origem: "Mockup nyx-session-render.jsx mostra bubble user com border arredondado (soft-box). TUI atual usa Rich Panel (sem border distintivo)."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_user_input ganha caminho schema-aware: schema=hybrid usa ANSI soft-box, outros mantém Rich Panel"

  forbidden:
    - "Quebrar fallback Rich (terminais sem support)"
    - "Hardcode hex fora de design_tokens*"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "render_user_input com schema=hybrid emite ╭─ Nome ─╮ + body + ╰─...─╯"
    - "Fallback Rich Panel preservado quando schema != hybrid"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-26-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Critério binário

- [ ] Soft-box ANSI implementado
- [ ] Fallback Rich preservado
- [ ] Smoke + invariantes 14/14

## Rollback

`git reset --hard HEAD~1`
