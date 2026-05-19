# SPRINT TUI-REDESIGN-27-02 — Prompt customizado com nome do usuário + template

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-27-02
  title: "prompt_str ganha template configurável; default '> {user_name}' (mockup-faithful)"
  onda: 27
  bloco: 27.1 Refinamento visual prompt_toolkit
  prioridade: ALTA
  tipo: UX
  dependencias: [TUI-REDESIGN-26-05, TUI-REDESIGN-27-01]
  desbloqueia: []
  origem: "Feedback do usuário: 'quando eu digito tá escrito nyx'. Mockups mostram '> andré' (nome do user). Atual: 'nyx>' hardcoded."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "prompt_str usa app_state['user_display_name']; lê NYX_PROMPT_TEMPLATE env opcional com placeholders {user_name}/{schema}/{model}"

  forbidden:
    - "Permitir \\033 (ANSI raw) em NYX_PROMPT_TEMPLATE user-defined"
    - "Quebrar prompt em terminais sem TTY"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"
    - cmd: "NYX_PROMPT_TEMPLATE='> {user_name} ' ./venv/bin/python -c 'import os; print(os.environ.get(\"NYX_PROMPT_TEMPLATE\"))'"
      timeout: 5
      deve_passar: "echo do template"

  acceptance_criteria:
    - "Default prompt mostra '> {nome}' em accent (sem 'nyx>')"
    - "NYX_PROMPT_TEMPLATE='{schema}» ' renderiza 'hybrid» '"
    - "Placeholders suportados: {user_name}, {schema}, {model}"
    - "Validação anti-ANSI: template com '\\033' rejeitado, fallback default"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-27-02

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
