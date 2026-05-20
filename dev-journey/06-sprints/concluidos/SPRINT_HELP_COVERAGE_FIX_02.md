# SPRINT HELP-COVERAGE-FIX-02 — `/aesthetic` excede limite de 3 exemplos

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: HELP-COVERAGE-FIX-02
  title: "Comando /aesthetic deve ter no máximo 3 exemplos (audit_help_coverage)"
  onda: 24
  bloco: 24.4 Higiene de orquestração
  prioridade: BAIXA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/aesthetic.py
      reason: "Reduzir lista de examples de 4 para 3 (máximo permitido)"
  creates: []
  removes: []

  forbidden:
    - "Remover funcionalidade real do /aesthetic"
    - "Mexer no audit_help_coverage.py para flexibilizar limite"

  tests:
    - cmd: "./venv/bin/python scripts/audit_help_coverage.py | tail -1"
      timeout: 10
      deve_passar: "61/61 OK"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "/aesthetic tem exatamente 3 exemplos (mantendo cobertura semântica)"
    - "audit_help_coverage retorna 61/61 OK"
    - "Smoke ok"
    - "Invariantes 14/14"
```

---

# Sprint HELP-COVERAGE-FIX-02 — `/aesthetic` exemplos

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7
**Origem:** achado colateral durante execução de HELP-COVERAGE-FIX-01

---

## Contexto

Durante execução de HELP-COVERAGE-FIX-01 detectou-se que `audit_help_coverage.py` reportava `59/61 OK`, e não `59/60` como o spec original supunha. Existem DUAS falhas:

1. `/?` com 1 exemplo (corrigido pela sprint 01).
2. `/aesthetic` com 4 exemplos (este achado).

`audit_help_coverage.py` aceita 2 a 3 exemplos. `/aesthetic` está acima do limite. Protocolo anti-débito materializa esta sprint formalmente, sem fix inline na sprint 01.

---

## Estado atual (evidência)

```
nyx/agent/commands/aesthetic.py:20-25
    examples=[
        "/aesthetic list",
        "/aesthetic get",
        "/aesthetic set arcano",
        "/aesthetic set cyberpunk:luna",
    ],
```

---

## Solução proposta

Reduzir para 3 exemplos preservando os casos canônicos. Sugestão:

```python
examples=[
    "/aesthetic list",
    "/aesthetic set arcano",
    "/aesthetic set cyberpunk:luna",
],
```

Justificativa: `/aesthetic get` é menos importante que `list` (que cobre exploração) e `set` (que cobre as duas formas, simples e composta `aesthetic:entity`).

Alternativa: manter `get` e juntar `list` com a forma curta sem argumentos. Decidir durante implementação.

---

## Critério binário de aceite

- [ ] `/aesthetic` tem ≤3 exemplos
- [ ] `audit_help_coverage.py` reporta 61/61 OK
- [ ] Smoke ok
- [ ] Invariantes 14/14
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `fix(HELP-COVERAGE-FIX-02): /aesthetic 4->3 exemplos (61/61 OK)`

---

*"Excesso é falta com outro nome." — HELP-COVERAGE-FIX-02*
