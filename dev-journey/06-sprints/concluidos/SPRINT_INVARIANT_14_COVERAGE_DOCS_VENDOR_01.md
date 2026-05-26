# SPRINT 254 — INVARIANT-14-COVERAGE-DOCS-VENDOR-01

## 0. SPEC

```yaml
sprint:
  id: INVARIANT-14-COVERAGE-DOCS-VENDOR-01
  title: "check #14 (anti-sanitizer) deteccao de glifo-orfao em docs e vendored, nao so runtime canonico"
  onda: 31
  prioridade: MEDIA
  tipo: Infra
  dependencias: [SANITIZER-WORKING-TREE-RESTORE-09]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh
      reason: "Check #14 valida presenca de >=3 de cada glifo canonico em arquivos de RUNTIME (banner.py/output.py), mas passou 14/14 com a working tree corrompida (65 docs + xterm.js com glifos estripados). Gap: nao cobre docs nem vendored."
  creates: []
  removes: []

  forbidden:
    - "Tornar o check #14 lento a ponto de estourar o budget do smoke (manter < 2s)"
    - "Falsos-positivos em arquivos que legitimamente nao tem glifos"
    - "Adicionar emoji ou mencao a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 120
      deve_passar: true

  acceptance_criteria:
    - "Check #14 detecta glifo da allowlist removido deixando padrao-orfao (ex: parenteses/aspas com espaco vazio onde havia U+25CF) em arquivos *.md tracked"
    - "Check #14 verifica que arquivos vendored conhecidos (xterm.js) mantem seus glifos esperados, OU os exclui explicitamente da varredura com comentario"
    - "Reproducao negativa: estripar 1 glifo de teste num .md e confirmar que o check passa a FALHAR (exit != 0)"
    - "Reproducao positiva: working tree limpa -> 14/14 PASS"
```

---

# Sprint 254 — INVARIANT-14-COVERAGE-DOCS-VENDOR-01

**Status:** CONCLUIDA (2026-05-26)
**Data criacao:** 2026-05-25

## Contexto

Durante a auditoria de 2026-05-25, `bash scripts/sprint_invariants.sh` retornou
14/14 PASS **enquanto a working tree tinha 65 arquivos com glifos da allowlist
estripados** (ver sprint 253). O check #14 ("glifos canonicos preservados",
defesa anti-sanitizer) valida apenas a presenca de redundancia (>=3 de cada
U+25CB/U+25D0/U+25CF) nos arquivos canonicos de RUNTIME. Ele NAO cobre:

1. Docs (`dev-journey/**/*.md`, `*.md` raiz) — onde o dano de 65 arquivos
   passou despercebido, incluindo a propria MICROCOPY.md.
2. Vendored (`nyx/cockpit/static/vendor/xterm.js`) — onde U+25C6 foi removido.

A defesa anti-sanitizer e o invariante mais critico do projeto (3 sprints FIX +
3 RECIDIVA). Um check que passa com a tree corrompida e um furo de cobertura.

## Solucao

Ampliar o check #14 com uma sub-verificação de "glifo-orfao":
- Heuristica: procurar em `*.md` tracked padroes que indicam glifo removido,
  ex.: `( )` / `(  )` onde a versao de referencia tinha glifo; ou divergencia
  contra `git show HEAD:<arquivo>` para arquivos de glifo conhecidos.
- Abordagem mais robusta e barata: comparar contagem de glifos da allowlist na
  working tree vs HEAD para um conjunto-sentinela (MICROCOPY.md, xterm.js,
  ADR_027). Se a working tree tem MENOS glifos que o HEAD -> FAIL.
- Manter < 2s (smoke budget): limitar a varredura ao conjunto-sentinela, nao
  ao repo inteiro.

## Acceptance

- [ ] Estripar 1 glifo de teste em MICROCOPY.md -> check #14 FALHA.
- [ ] Restaurar -> check #14 PASSA.
- [ ] Tempo do check < 2s.
- [ ] 14/14 PASS com tree limpa.

## Proof-of-work (REAL, 2026-05-26)

Implementado como sub-check dentro do bloco Python do check #14 em
`sprint_invariants.sh`: para um conjunto-sentinela (`MICROCOPY.md`, vendored
`xterm.js`, `ADR_027`), compara a contagem de codepoints da faixa Geometric
Shapes (U+25A0-U+25FF, range em vez de literais -> imune a sanitizer e cobre
toda a allowlist) na working tree vs `git show HEAD:<arquivo>`. Se working < HEAD
-> FAIL. Custo: 3 `git show` (~150ms).

```
# POSITIVO (tree limpa):
bash scripts/sprint_invariants.sh   # exit 0; PASS 14 / FAIL 0; total 0.69s (< 2s)

# NEGATIVO (estripar 1 glifo ● do MICROCOPY via python replace):
#   ● antes=11 depois=10
bash scripts/sprint_invariants.sh   # exit 1; FAIL no #14:
#   "MICROCOPY.md: glifos Geometric Shapes removidos (working=16 < HEAD=17)
#    -- possivel dano de sanitizer"

# RESTORE (git checkout MICROCOPY):
bash scripts/sprint_invariants.sh   # exit 0; PASS 14 / FAIL 0
```

Cobre o gap exato da auditoria: o check passava 14/14 com 65 docs + xterm.js
estripados. Agora um strip num sentinela (docs OU vendored) -> FAIL antes do commit.
Sem falso-positivo em tree limpa; tempo total 0.69s respeita o budget do smoke.
