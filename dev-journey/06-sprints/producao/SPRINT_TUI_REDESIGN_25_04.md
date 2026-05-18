# SPRINT TUI-REDESIGN-25-04 — Boas-vindas com nome do usuário

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-04
  title: "Boas-vindas lê git config user.name; bubble user usa [Nome] em vez de 'você'"
  onda: 25
  bloco: 25.2 Onboarding & Banner
  prioridade: MÉDIA
  tipo: UX
  dependencias: [TUI-REDESIGN-25-01]
  desbloqueia: [TUI-REDESIGN-25-05, TUI-REDESIGN-25-07]
  origem: "Auditoria audit.jsx -- problemas P03 (Rótulo 'você') e P04 (Sem onboarding real)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/onboarding.py
      reason: "Primeira tela do tutorial menciona o nome (subprocess git config --get user.name); fallback 'visitante'"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_user_input usa app_state['user_display_name'] para Panel title"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Resolve user_display_name no boot e armazena em app_state"

  forbidden:
    - "Persistir nome em arquivo do repo (lido em runtime via git config)"
    - "Pedir input interativo no boot só pra capturar nome (silencioso/automático)"
    - "Quebrar fluxo se git config user.name vazio (fallback 'visitante')"

  tests:
    - cmd: "git config --get user.name"
      timeout: 5
      deve_passar: "qualquer string ou vazio (não falha)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "boot resolve user_display_name = git config user.name | fallback 'visitante'"
    - "Bubble user usa [Nome] como title (não 'você')"
    - "Onboarding primeira tela: 'Bem-vindo, <Nome>!'"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-04

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P03 + P04: "você" é impessoal. Claude Code lê git config para personalizar. Esta sprint adota o mesmo padrão (silencioso, sem prompt).

## Solução proposta

1. `cli.py` no boot: `subprocess.run(["git", "config", "--get", "user.name"], capture_output=True)`. Strip + fallback `visitante`. Armazena em `app_state["user_display_name"]`.
2. `render_user_input` (output.py) lê `app_state` via param ou closure; Panel title vira `[Nome]`.
3. `onboarding.py` primeira tela: `f"Bem-vindo, {user_name}!"`.

## Critério binário

- [ ] git config lido no boot (sem prompt)
- [ ] Fallback 'visitante' funciona quando git config vazio
- [ ] Bubble user usa [Nome]
- [ ] Onboarding personalizado
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-04): boas-vindas com nome do usuario via git config`

## Invariantes

#2, #14.

## Anti-débito

- Persistência do nome em ~/.nyx/config.toml (caso git config indisponível) fica para sprint nova se demandado.
- Internacionalização (Welcome / Bienvenido) fica fora; PT-BR fixo.

## Verificação

```bash
git config --get user.name
./run.sh --smoke
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Nome é a primeira affordance de presença." -- TUI-REDESIGN-25-04*
