# SPRINT 256 — DOC-STATE-REFRESH-ONDA31-01

## 0. SPEC

```yaml
sprint:
  id: DOC-STATE-REFRESH-ONDA31-01
  title: "Atualizar metadados de estado (MASTER header/inventario/projecao, STATE, README Status) para ONDA-31"
  onda: 31
  prioridade: BAIXA
  tipo: Doc
  dependencias: [DOC-COUNT-INTERNAL-SYNC-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Header v5.4.0 datado 2026-05-21; secao Inventario de 2026-04-21 (52 commands/9 services); Projecao de testes parada na Onda 22 (340 testes). Trabalho real esta na ONDA-31 (sprints 222-259)."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/README.md
      reason: "Secao 'Status atual (2026-05-21, v1.3.0-rc2)' defasada vs Onda 31 / 2026-05-25."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/STATE.md
      reason: "Linha de retomada datada 2026-05-21 (gitignored; atualizar local)."
  creates: []
  removes: []

  forbidden:
    - "Reescrever historico das ondas anteriores (apendar, nao apagar)"
    - "Commitar STATE.md / VALIDATOR_BRIEF.md (sao gitignored por design)"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true

  acceptance_criteria:
    - "MASTER: secao Inventario aponta 35/67/15 (ou refere sync.py como fonte viva) e nota da ONDA-31"
    - "MASTER: Projecao de testes estendida ate a onda atual OU marcada como historica ate Onda 22"
    - "README 'Status atual' reflete 2026-05-25 / ONDA-31"
    - "STATE.md linha de retomada = sessao atual"
```

---

# Sprint 256 — DOC-STATE-REFRESH-ONDA31-01

**Status:** CONCLUIDA (2026-05-26)
**Data criacao:** 2026-05-25

## Contexto

Auditoria de 2026-05-25: os metadados de estado nao acompanharam as ondas 23-31.
- `SPRINT_ORDER_MASTER.md`: header v5.4.0 / 2026-05-21; "Inventario" de
  2026-04-21 ("35 tools / 52 commands / 9 services"); "Projecao de testes"
  termina na Onda 22 (340 testes). Os blocos MANUAL_OVERRIDE existem ate ONDA-31,
  mas as secoes de cabecalho/projecao nao.
- README "Status atual (2026-05-21, v1.3.0-rc2)".
- STATE.md "Sessao 2026-05-21".

Sintoma esperado do alto custo de meta-trabalho: a maquina de processo produz
mais rapido do que se auto-atualiza.

## Solucao

Atualizar os 3 documentos para o estado real (ONDA-31, 2026-05-25, contagens
35/67/15). Preferir apontar para fontes vivas (`sync.py`) em vez de numeros
congelados, reduzindo recidiva de defasagem. STATE.md e gitignored: atualizar
local sem commit.

## Acceptance

- [ ] MASTER header/inventario/projecao = estado ONDA-31.
- [ ] README "Status atual" = 2026-05-25.
- [ ] STATE.md linha de retomada atual.
- [ ] Smoke preservado.

## Proof-of-work (REAL, 2026-05-26)

Atualizado (append-style, sem apagar histórico):
- MASTER header: Versão v5.4.0 -> v5.5.0; Data ganha entrada 2026-05-26 ONDA-31
  (lista CONCLUIDAS/PENDENTE da onda) antes da entrada 2026-05-21.
- MASTER Inventário: apêndice 2026-05-26 (ONDA-31) com 35/67/15/32 ADRs/320 testes
  apontando `sync.py` como fonte viva (números congelados = só marco histórico).
- MASTER Projeção de testes: nota de que é histórica até Onda 22; estado real em
  `sync.py` + `--gauntlet`.
- README "Status atual": (2026-05-21, v1.3.0-rc2) -> (2026-05-26, v1.3.0 ONDA-31).
- STATE.md (gitignored, local): linha de retomada -> sessão 2026-05-26 ONDA-31.

```
grep -n "v5.5.0\|ONDA-31" dev-journey/06-sprints/SPRINT_ORDER_MASTER.md | head   # presente
grep -n "Status atual" README.md   # 2026-05-26, v1.3.0 ONDA-31
./run.sh --smoke                    # boot ok
bash scripts/sprint_invariants.sh   # PASS 14 / FAIL 0
```

STATE.md e VALIDATOR_BRIEF.md NAO commitados (gitignored por design, conforme
forbidden do spec).
