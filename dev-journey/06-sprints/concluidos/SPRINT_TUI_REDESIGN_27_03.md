# SPRINT TUI-REDESIGN-27-03 — Listas navegáveis (radiolist_dialog) para /aesthetic /schema /theme

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-27-03
  title: "/aesthetic select, /schema select, /theme select abrem modal radiolist com setinhas + Enter"
  onda: 27
  bloco: 27.1 Refinamento visual prompt_toolkit
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [TUI-REDESIGN-27-01]
  desbloqueia: []
  origem: "Feedback do usuário: 'não temos listas navegáveis pelas setinhas pra eu escolher o que eu quero configurar'."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/aesthetic.py
      reason: "Aceitar 'select' como subcomando; retornar __aesthetic_select__"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/schema.py
      reason: "Aceitar 'select'; retornar __schema_select__"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/system.py
      reason: "cmd_theme aceita 'select'; retornar __theme_select__"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Handlers das 3 sentinelas usam radiolist_dialog (run_async); reusa _build_prompt_style() para cor"

  forbidden:
    - "Quebrar modo list atual (texto + marker *)"
    - "Modal full-screen sem retornar ao REPL"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"
    - cmd: "./venv/bin/python -c 'from prompt_toolkit.shortcuts import radiolist_dialog; print(radiolist_dialog)'"
      timeout: 5
      deve_passar: "import OK"

  acceptance_criteria:
    - "/aesthetic select abre modal com 6 opções; setas navegam, Enter confirma"
    - "/schema select abre modal com 4 schemas"
    - "/theme select abre modal com themes do ThemeManager"
    - "Cor do modal puxa de _build_prompt_style() (theme Nyx)"
    - "Cancel (Esc) volta ao REPL sem mudar runtime"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-27-03

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18 (sincronizado em SPRINT_ORDER-REFRESH-01 2026-05-19)
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
