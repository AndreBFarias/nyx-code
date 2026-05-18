# SPRINT HELP-COVERAGE-FIX-01 — `/?` ganha 2o exemplo de uso

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: HELP-COVERAGE-FIX-01
  title: "Comando /? deve ter pelo menos 2 exemplos (mín. exigido por audit_help_coverage)"
  onda: 24
  bloco: 24.4 Higiene de orquestração
  prioridade: BAIXA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/help.py
      reason: "Adicionar exemplo extra ao /? (atualmente tem só 1)"
  creates: []
  removes: []

  forbidden:
    - "Reescrever toda a documentação do /?"
    - "Adicionar exemplo que não é executável literal"

  tests:
    - cmd: "./venv/bin/python scripts/audit_help_coverage.py | tail -1"
      timeout: 10
      deve_passar: "60/60 OK"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "/? tem pelo menos 2 exemplos no docstring/help do command"
    - "audit_help_coverage retorna 60/60 OK (era 59/60)"
    - "Smoke ok"
    - "Invariantes 14/14"
```

---

# Sprint HELP-COVERAGE-FIX-01 — `/?` exemplos

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Achado colateral A1 da sessão 2026-05-18: `audit_help_coverage.py` reporta `59/60 OK` porque `/?` tem apenas 1 exemplo (mínimo exigido = 2). Resto está OK. Anti-débito imediato: materializa sprint, resolve.

---

## Solução proposta

Localizar registro de `/?` em `nyx/agent/commands/` (provavelmente `help.py` ou `agency.py`). Adicionar 1-2 exemplos de uso (string com prompt + breve descrição do efeito esperado).

Exemplo:
```python
examples=[
    "/? — contextualiza a próxima ação possível dada o estado atual",
    "/? plano — pergunta o que fazer dado um arquivo de plano aberto",
]
```

---

## Critério binário de aceite

- [ ] `/?` tem ≥2 exemplos
- [ ] `audit_help_coverage.py` reporta 60/60 OK
- [ ] Smoke ok
- [ ] Invariantes 14/14
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `fix(HELP-COVERAGE-FIX-01): /? ganha 2o exemplo (60/60 OK)`

---

*"Cobertura é cuidado." — HELP-COVERAGE-FIX-01*
