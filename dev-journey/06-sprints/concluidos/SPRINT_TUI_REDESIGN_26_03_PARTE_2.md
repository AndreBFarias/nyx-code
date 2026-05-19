# SPRINT TUI-REDESIGN-26-03-PARTE-2 — Ações de erro alinhadas à direita do tool chip

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-26-03-PARTE-2
  title: "render_tool_chip aceita error_actions e alinha chips clicaveis à direita da mesma linha"
  onda: 26
  bloco: 26.meta (refinamento)
  prioridade: MÉDIA
  tipo: UX
  dependencias: [TUI-REDESIGN-26-03]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_tool_chip aceita error_actions; alinha à direita quando cabe"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "on_tool_result passa error_actions classificadas dentro de render_tool_chip"

  acceptance_criteria:
    - "render_tool_chip aceita error_actions=[(key, label, cmd), ...]"
    - "Cols >= 80: ações em chips [a] label  [b] label à direita da MESMA linha do chip"
    - "Cols < 80: fallback render_error_with_actions abaixo"
    - "Smoke + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-26-03-PARTE-2

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7
