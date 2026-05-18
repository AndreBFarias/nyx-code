# SPRINT TUI-REDESIGN-25-07 — Remoção do eco do prompt (bubble única)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-07
  title: "Após Enter, mostra UMA bubble user com [Nome] -- remove eco redundante"
  onda: 25
  bloco: 25.3 Diálogo
  prioridade: ALTA
  tipo: UX+Refactor
  dependencias: [TUI-REDESIGN-25-03, TUI-REDESIGN-25-04]
  desbloqueia: [TUI-REDESIGN-25-08]
  origem: "Auditoria audit.jsx -- problema P02 (Duplicação do prompt do usuário)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Keybinding enter (linha 173): após submit, limpar tela do prompt antes de chamar render_user_input"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_user_input usa schema soft-box default (já tokenizado em 25-03)"

  forbidden:
    - "Remover o prompt 'nyx> ' (precisa continuar para tab completion / history)"
    - "Quebrar Ctrl+O (expandir paste longa)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Após Enter, tela mostra: 1 bubble user em [Nome] + resposta Nyx"
    - "Sem linha 'nyx> X' duplicada acima da bubble"
    - "Tab completion + Ctrl+R + Ctrl+O continuam funcionando"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-07

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P02: hoje a tela mostra:
```
nyx> Olá, tudo bem?
┌─ você ─┐
│ Olá, tudo bem? │
└────────┘
```

A linha `nyx> X` é ruído visual (eco do prompt do prompt_toolkit) — a bubble abaixo já mostra o conteúdo.

## Solução proposta

1. Em `cli.py` keybinding enter: após `buf.validate_and_handle()`, emitir `\033[1A\033[2K` (move-up + clear-line) para remover a linha do prompt antes de imprimir a bubble.
2. Alternativa mais limpa: configurar `PromptSession` com `rprompt=None` e suprimir echo via callback `pre_run`.
3. Garantir que Ctrl+R (history search) e Ctrl+O (expand) ainda funcionem.

## Critério binário

- [ ] Eco redundante removido
- [ ] Bubble user única visível
- [ ] Tab completion preservado
- [ ] Ctrl+R, Ctrl+O preservados
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-07): remove eco do prompt usuario`

## Invariantes

#14.

## Anti-débito

- Animação de transição (fade) fora de escopo: terminal não suporta.
- Suporte a paste longo (>N linhas) já existe em cli_helpers.

## Verificação

```bash
./run.sh
# digitar "oi" + Enter
# avaliar: apenas a bubble [Nome] visível, sem nyx> oi acima
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Uma fala = uma bubble." -- TUI-REDESIGN-25-07*
