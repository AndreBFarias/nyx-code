# SPRINT TUI-REDESIGN-25-05 — Wizard --menu em 5 passos com contador + summary

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-05
  title: "Wizard --menu vira 5 passos numerados (01/05) com hint contextual + summary card final"
  onda: 25
  bloco: 25.2 Onboarding & Banner
  prioridade: ALTA
  tipo: UX+Refactor
  dependencias: [TUI-REDESIGN-25-04]
  desbloqueia: [TUI-REDESIGN-25-06]
  origem: "Auditoria audit.jsx -- problema P04 (Sem onboarding real)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/menu_wizard.py
      reason: "Reformatar saída: passo X/Y, título destaque, hint contextual, summary card final"

  forbidden:
    - "Persistir senha sudo no config.toml"
    - "Quebrar Enter como aceitar default"
    - "Adicionar etapas que não estavam no wizard atual (mesmas 5)"

  tests:
    - cmd: "printf '\\n\\n\\n\\n\\nS\\n' | NYX_MENU_EMIT=1 ./venv/bin/python scripts/menu_wizard.py 2>&1 | grep -c '0[0-9]/05'"
      timeout: 10
      deve_passar: ">= 5 (cada passo emite contador)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Cada passo mostra contador '01/05', '02/05', ..."
    - "Cada passo tem hint 1-linha abaixo do título"
    - "Summary card final mostra tabela de escolhas antes de salvar"
    - "Enter aceita default destacado (com '↵ Enter' visível)"
    - "stdout reservado para exports (separação preservada)"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-05

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P04: o wizard atual é lista numerada sem step counter e sem contexto. O redesenho inspira-se em onboardings lineares: cada passo respira, tem hint, e o usuário vê quantos passos faltam.

## Solução proposta

Reformatar `scripts/menu_wizard.py::ask()`:
- Cabeçalho: `01/05 · Aesthetic visual` em destaque accent.
- Hint: 1 linha curta abaixo (ex: "Estrutura geral do layout: cor, glifos, divisores.")
- Choices numeradas (atual ok)
- Footer: `↵ Enter aceita 'default'`
- Após 5 passos: summary card com tabela `aesthetic = X / entity = Y / banner = Z / model = W / auto_approve = bool` antes de salvar.

## Critério binário

- [ ] Contador 01/05..05/05 em cada passo
- [ ] Hint contextual de 1 linha
- [ ] Summary card antes de salvar
- [ ] Defaults aceitos com Enter
- [ ] stdout/stderr separados preservados
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-05): wizard 5 passos com contador e summary`

## Invariantes

#6, #14.

## Anti-débito

- Persistência em ~/.nyx/config.toml já existe — escopo aqui é só UX.
- Validação de input (números fora do range) já existe — manter.

## Verificação

```bash
./run.sh --menu  # avalia interativo
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Onboarding bom é respiração orquestrada." -- TUI-REDESIGN-25-05*
