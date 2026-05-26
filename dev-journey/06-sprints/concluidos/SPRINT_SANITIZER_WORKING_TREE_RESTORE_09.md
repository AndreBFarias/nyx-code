# SPRINT 253 — SANITIZER-WORKING-TREE-RESTORE-09

## 0. SPEC

```yaml
sprint:
  id: SANITIZER-WORKING-TREE-RESTORE-09
  title: "Restaurar 65 arquivos + xterm.js com glifos da allowlist estripados (dano residual pre-allowlist)"
  onda: 31
  prioridade: ALTA
  tipo: Hygiene
  dependencias: []
  desbloqueia: []

  touches:
    - path: "(65 arquivos via `git diff --name-only`)"
      reason: "Glifos da allowlist (U+25CB circulo vazio, U+25D0 meio, U+25CF cheio, U+25C6 losango, U+25B6 triangulo, U+25BC) estripados deixando espaco orfao; inclui MICROCOPY.md (o arquivo que DEFINE os glifos) e nyx/cockpit/static/vendor/xterm.js (U+25C6 removido da tabela CHARSETS do VT100)"
  creates: []
  removes: []

  forbidden:
    - "Commitar o dano (glifos estripados) ao historico"
    - "Tocar os 3 sanitizers (universal-sanitizer.py, emoji_guardian.py, guardian.py): ja corrigidos hoje via allowlist centralizada glyphs_canonicos.py (SPRINTs 232/233/234)"
    - "Descartar mudanca legitima: auditoria confirmou que as 65 sao dano puro de glifo (HEAD esta limpo e correto)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 120
      deve_passar: true

  acceptance_criteria:
    - "git diff --name-only retorna vazio (working tree limpa) apos checkout"
    - "MICROCOPY.md volta a conter os 3 glifos canonicos U+25CB U+25D0 U+25CF na secao de glifos"
    - "nyx/cockpit/static/vendor/xterm.js volta a ter U+25C6 na tabela CHARSETS[0] (1 ocorrencia)"
    - "Smoke boot ok + invariantes 14/14 PASS preservados"
```

---

# Sprint 253 — SANITIZER-WORKING-TREE-RESTORE-09

**Status:** CONCLUIDA (2026-05-25)
**Data criacao:** 2026-05-25

## Contexto

Auditoria de 2026-05-25 detectou 65 arquivos NAO-commitados na working tree
com glifos da allowlist canonica estripados (substituidos por espaco vazio).
Causa-raiz confirmada empiricamente: o range `-◿` do
`emoji_guardian.py` (em `~/Controle de Bordo/.sistema/scripts/`) capturava
todos os glifos geometricos (U+25CB, U+25D0, U+25CF, U+25C6, U+25B6, U+25BC,
U+25FB, U+25FC) ANTES da allowlist centralizada criada hoje (20:48, commit
4df7d0d, via SPRINTs 232/233/234).

Os 3 sanitizers ja estao corrigidos (testado: preservam os glifos, removem so
emoji real como U+26A1). O dano e RESIDUAL — nunca foi revertido na working
tree. Inclui:
- `MICROCOPY.md`: o arquivo que DEFINE os glifos teve `(U+25CB U+25D0 U+25CF)`
  apagado para `(  )` (espaco vazio).
- `nyx/cockpit/static/vendor/xterm.js`: U+25C6 removido de `CHARSETS[0]` (mapa
  DEC do VT100). O `emoji_guardian.py` nao exclui `/vendor/` (ver sprint 257).

HEAD (e0f49bd) esta limpo e correto: `xterm.js` no HEAD tem 1 ocorrencia de
U+25C6; working tree tem 0. Decisao do usuario (2026-05-25): `git checkout`.

## Solucao

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
# Capturar lista antes (auditoria/proof)
git diff --name-only > /tmp/restore09_files.txt
wc -l /tmp/restore09_files.txt   # esperado: 65
# Restaurar ao HEAD limpo
git checkout -- $(git diff --name-only)
# Verificar
git diff --name-only           # esperado: vazio
grep -c "$(printf '\xe2\x97\x86')" nyx/cockpit/static/vendor/xterm.js  # esperado: 1
```

Os untracked (2 baselines JSON) e o `D` (PTY_HANDOVER ja movido) ficam fora do
checkout — sao estado legitimo, nao dano.

## Acceptance

- [ ] working tree limpa (`git diff --name-only` vazio para os 65 tracked).
- [ ] MICROCOPY.md com os 3 glifos restaurados.
- [ ] xterm.js com U+25C6 restaurado (count 1).
- [ ] Smoke + invariantes preservados.

## Proof-of-work (REAL, 2026-05-25)

Classificacao rigorosa dos 65 (strip-non-ASCII de HEAD vs working):
- **61 arquivos = dano puro de glifo/acento** -> revertidos via `git checkout`.
- **4 arquivos = conteudo ASCII legitimo, ZERO perda de glifo** -> PRESERVADOS:
  - `gauntlet/checkpoint.json` (resultado gauntlet 2026-05-25, timestamp+phases)
  - `gauntlet/baselines/baseline_2026-05-21.json` (dados gauntlet)
  - `PROJECT_SNAPSHOT.md` (Sprints concluidas 387->434; glifos 10==10 intactos)
  - `SPRINT_TEMPLATE_V2.md` (cli.py ~790->980 linhas; sem glifo)

Verificação da reversão:
```
xterm.js U+25C6:  ANTES 0 -> DEPOIS 1   (CHARSETS[0] DEC restaurado)
MICROCOPY glifos: ANTES 0 -> DEPOIS 17  (secao de glifos canonicos restaurada)
./run.sh --smoke               # boot ok
bash scripts/sprint_invariants.sh  # PASS: 14  FAIL: 0
```

Nota: o criterio original "git diff vazio" foi ajustado para "zero dano de
glifo" — os 4 arquivos legitimos + MASTER (registro das sprints 253-259) + 7
specs novas permanecem como mudanca intencional a commitar.

Achado colateral (ja materializado): a recidiva do xterm.js (sprint 231 ja o
havia restaurado) prova que falta excluir /vendor/ no emoji_guardian ->
sprint 257 SANITIZER-VENDOR-EXCLUDE-HARDEN-01.
