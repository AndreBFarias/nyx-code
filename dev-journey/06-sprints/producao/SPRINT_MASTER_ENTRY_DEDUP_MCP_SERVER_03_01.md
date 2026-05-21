# SPRINT MASTER-ENTRY-DEDUP-MCP-SERVER-03-01 — Remoção de entry duplicada de MCP-SERVER-03

## 0. SPEC

```yaml
sprint:
  id: MASTER-ENTRY-DEDUP-MCP-SERVER-03-01
  title: "Remover entry duplicada de MCP-SERVER-03 no MASTER (128b vs 206)"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: ALTA
  tipo: Refactor doc
  dependencias: [MASTER-IDS-DEDUP-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Remover 1 entry redundante. Linha 381 (ID 128b) e linha 399 (ID 206) descrevem a MESMA sprint MCP-SERVER-03 com textos divergentes."

  forbidden:
    - "Criar terceira entry"
    - "Alterar descrição de outras sprints"
    - "Tocar entries vizinhas"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths dev-journey/06-sprints/SPRINT_ORDER_MASTER.md"
      assert: "rc=0"

  acceptance_criteria:
    - "grep -cE '\\| (128b|206) \\| \\*\\*MCP-SERVER-03\\*\\*' dev-journey/06-sprints/SPRINT_ORDER_MASTER.md retorna 1 (não 2)"
    - "Awk uniq -d sobre coluna ID permanece 0 (não regrede 125qq)"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

1. Identificar qual texto preservar: linha 381 (ID 128b) tem hash de commit canônico `5e1927e` + lista de achados colaterais reais (125ll/mm/nn) — mais provável de ser canônica.
2. Remover linha 399 (ID 206) que cita "ADR-030 fechado" sem hash de commit.
3. Preservar quaisquer referências cruzadas em CHANGELOG/PORT_STATUS (não tocar esses arquivos — só MASTER).
4. Validar: `grep -cE '\| (128b|206) \| \*\*MCP-SERVER-03\*\*'` retorna 1.

## Critério binário

- [ ] Apenas 1 entry de MCP-SERVER-03 no MASTER (não 2)
- [ ] Awk uniq -d sobre IDs permanece 0
- [ ] Smoke + invariantes 14/14
- [ ] Acentuação rc=0
