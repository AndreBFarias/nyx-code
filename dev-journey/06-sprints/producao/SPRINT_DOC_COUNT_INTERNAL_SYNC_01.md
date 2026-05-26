# SPRINT 255 — DOC-COUNT-INTERNAL-SYNC-01

## 0. SPEC

```yaml
sprint:
  id: DOC-COUNT-INTERNAL-SYNC-01
  title: "Sincronizar contagens internas do README e STATE.md com a fonte unica (35/67/15)"
  onda: 31
  prioridade: BAIXA
  tipo: Doc
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
      reason: "Topo (linha 7) e a fonte unica dizem 67 commands / 15 services (CORRETO via sync.py), mas o corpo destoa: linha 222 'Commands (61 registrados)' e linha 239 'Services (14)'. Inconsistencia interna."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/update_docs.py
      reason: "Sincroniza o topo do README mas nao as tabelas internas (secoes Commands/Services). Estender para cobri-las ou marca-las como geradas."
  creates: []
  removes: []

  forbidden:
    - "Alterar a contagem de tools (35) que ja esta correta em todos os lugares"
    - "Inventar numeros: a fonte de verdade e `python scripts/sync.py` (primeira linha)"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "python scripts/sync.py"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "README corpo: 'Commands (61 registrados)' -> 67 ; 'Services (14)' -> 15"
    - "STATE.md: 'Commands: 66 unicos' -> 67 ; 'Services: 14' -> 15 (off-by-one)"
    - "update_docs.py atualiza tambem as secoes-tabela do README, ou um teste garante que topo == corpo"
    - "`python scripts/sync.py` primeira linha: tools=35, commands_unicos=67, services=15"
```

---

# Sprint 255 — DOC-COUNT-INTERNAL-SYNC-01

**Status:** PENDENTE
**Data criacao:** 2026-05-25

## Contexto

Auditoria de 2026-05-25: `python scripts/sync.py` (autoritativo, runtime)
imprime `inventario: tools=35, commands_unicos=67, services=15`. O topo do
README (linha 7) e o `PROJECT_SNAPSHOT.md` (fonte unica) batem. Porem o CORPO
do README contradiz o proprio topo:
- Linha 222: "## Commands (61 registrados)" -> deveria ser 67.
- Linha 239: "## Services (14)" -> deveria ser 15.

E `STATE.md` (linha 22) tem off-by-one: "Commands: 66 unicos, Services: 14".

`update_docs.py` sincroniza o topo do README mas nao varre as tabelas internas
(diferenca observada em PROJECT_SNAPSHOT.md linha 29 "OK via update_docs.py").

## Solucao

1. Corrigir README corpo: 61->67, 14->15.
2. Corrigir STATE.md: 66->67, 14->15.
3. Estender `update_docs.py` para reescrever os headers das secoes Commands/
   Services a partir de `sync.py`, OU adicionar verificação em `sync.py` que
   falha se topo != corpo.

## Acceptance

- [ ] README topo == corpo == 35/67/15.
- [ ] STATE.md = 35/67/15.
- [ ] update_docs.py cobre as tabelas internas (idempotente).

## Proof-of-work

```
python scripts/sync.py | head -1   # inventario: tools=35, commands_unicos=67, services=15
grep -nE "Commands \(|Services \(" README.md   # 67 e 15
grep -nE "Commands:|Services:" STATE.md        # 67 e 15
```
