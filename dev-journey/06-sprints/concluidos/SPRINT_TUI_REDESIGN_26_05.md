# SPRINT TUI-REDESIGN-26-05 — Onboarding pede nome + persiste em ~/.nyx/config.toml

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-26-05
  title: "First-run pergunta nome (git config como hint), persiste em config.toml; runs subsequentes leem do config"
  onda: 26
  bloco: 26.3 Onboarding nome
  prioridade: MÉDIA
  tipo: UX
  dependencias: [STREAMING-SIDE-RULE-01, TUI-REDESIGN-25-09-PARTE-2]
  desbloqueia: []
  origem: "Pedido do usuário 2026-05-18: nome do user vem de git config silenciosamente; onboarding deve perguntar interativamente e persistir."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py
      reason: "resolve_user_display_name passa a ler config.toml primeiro. Novo helper _persist_user_name(name). run_first_time_tutorial pergunta nome se não persistido."

  forbidden:
    - "Bloquear pipe/CI (não-tty) com prompt"
    - "Sobrescrever campos pré-existentes em config.toml fora user_display_name"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "resolve_user_display_name lê ~/.nyx/config.toml chave user_display_name primeiro"
    - "Fallback: git config user.name se config.toml ausente"
    - "Fallback final: 'visitante'"
    - "run_first_time_tutorial pergunta interativamente com git config como hint default"
    - "_persist_user_name salva config.toml preservando outras chaves"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-26-05

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
