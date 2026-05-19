# SPRINT INFRA-ACENTO-FIX-01 — Acentuação periférica em scripts/menu_wizard.py

## 0. SPEC

```yaml
sprint:
  id: INFRA-ACENTO-FIX-01
  title: "Corrigir acentuação periférica em scripts/menu_wizard.py (3 violações)"
  onda: 28
  bloco: 28.2 dívida técnica
  prioridade: BAIXA
  tipo: Fix
  dependencias: []
  desbloqueia: []
  origem: "Achado colateral durante execução de TUI-REDESIGN-28-05 (2026-05-18). Validador de acentuação reportou 3 violações pré-existentes; protocolo anti-débito (feedback_nenhum_debito.md) exige sprint nova ao invés de fix inline silencioso."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/menu_wizard.py
      reason: "Trocar 3 ocorrências sem acento por versões corretas"

  forbidden:
    - "Tocar lógica do wizard; só strings"

  tests:
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths scripts/menu_wizard.py"
      timeout: 5
      deve_passar: "0 violação"
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"

  acceptance_criteria:
    - "validar-acentuacao.py retorna 0 violações em scripts/menu_wizard.py"
    - "wizard ainda roda (smoke + standalone --menu)"

  proof_of_work:
    - "Diff mostra apenas substituições: 'nao' -> 'não' (linhas 8 e 119); 'descricao' -> 'descrição' (linha 64)"
    - "validar-acentuacao.py --paths scripts/menu_wizard.py mostra 0 violações"
```

---

# Sprint INFRA-ACENTO-FIX-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`

## Proof-of-work (executor 2026-05-18)

Substituições aplicadas em `scripts/menu_wizard.py` (3 violações pré-existentes):

- Linha 8 (docstring de módulo): `auto-approve (sim | nao)` → `auto-approve (sim | não)`
- Linha 64 (docstring `ask`): `(valor, descricao)` → `(valor, descrição)`
- Linha 119 (rótulo de exibição em `ask_yes_no`): `"sim" if default else "nao"` → `"sim" if default else "não"`

A literal `"nao"` da linha 119 é apenas rótulo (`say(f"...'{default_label}'...")`); a aceitação real continua em `raw in ("s", "sim", "y", "yes")`. Mudança cosmética, sem alterar lógica. Linha 135 (`render_summary`) já usa `"não"`; substituição alinha estética entre prompt e summary.

Validação runtime:

| Check | Antes | Depois |
|---|---|---|
| `validar-acentuacao --paths scripts/menu_wizard.py` | 3 violações | 0 violações |
| `./run.sh --smoke` | boot ok / exit 0 | boot ok / exit 0 |
| `bash scripts/sprint_invariants.sh` | PASS 12 / FAIL 2 (pré-existente, fora escopo) | PASS 14 / FAIL 0 |
| Import sanity (`from scripts.menu_wizard import main`) | -- | ok |

`FAIL_AFTER (0) <= FAIL_BEFORE (2)` — invariante respeitado. Os 2 FAILs da baseline (`print() fora de cli.py/output.py` e `except silencioso`) não estão em `scripts/menu_wizard.py`; possível resolução por agente paralelo.
