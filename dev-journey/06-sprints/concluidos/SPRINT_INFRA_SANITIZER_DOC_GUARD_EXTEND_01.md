# SPRINT INFRA-SANITIZER-DOC-GUARD-EXTEND-01 — guard anti-sanitizer cobre docs + U+26A1

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-DOC-GUARD-EXTEND-01
  title: "O guard pre-commit anti-sanitizer passa a cobrir dev-journey/**/*.md e o glifo U+26A1, fechando a brecha que deixou o strip de docs passar silencioso"
  onda: 40
  bloco: "40 -- higiene (achado da auditoria que abriu a onda)"
  prioridade: MEDIA
  tipo: Infra / Defesa anti-débito
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/check_sanitizer_attack.py
      reason: "PROTECTED só listava 7 arquivos de código e CANONICAL_GLYPHS só U+25xx; o sanitizer stripou U+26A1 de 7 docs de dev-journey e passou pelos dois gates (emoji-check passa porque não-emoji != bloqueio; este guard não cobria docs/U+26A1)."
      linhas_alvo: "PROTECTED->PROTECTED_CODE, DOC_GLYPHS novo, glyphs_for(), is_sanitizer_attack/_strip_glyphs parametrizados por glyphs, main()"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Bloquear de-emojificação legítima (glifo -> texto): o guard só pega a assinatura de remoção PURA (+linha == -linha sem glifo)"
    - "Tocar no emoji-check do pre-commit (escopo separado: bloqueia ADIÇÃO de emoji; este guard bloqueia REMOÇÃO de glifo)"
    - "Adicionar emoji literal, menção a IA"

  tests:
    - cmd: "probe TDD com diffs sintéticos (/tmp/guard_probe.py)"
      timeout: 30
      esperado: "doc_strip_zap BLOQUEIA(1); doc_legit_replace PASSA(0); code_strip_diamond BLOQUEIA(1); doc_normal_edit PASSA(0)"
    - cmd: "teste real: strip de 1 U+26A1 em doc rastreado + git add + rodar o guard"
      timeout: 30
      esperado: "exit 1 (bloqueia); git checkout restaura limpo"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"

  acceptance_criteria:
    - "Staged diff que só remove U+26A1 (ou U+25xx) de dev-journey/**/*.md é bloqueado no commit"
    - "Os 7 arquivos de código e glifos U+25xx continuam protegidos (sem regressão)"
    - "De-emojificação legítima e edições normais de doc passam livres"
    - "ruff All checks passed, acento rc=0, invariantes 14/14"
```

---

**Status:** CONCLUIDA (ver SPRINT_ORDER_MASTER ONDA-40, sprint 345)
**Data criação:** 2026-06-02
**Origem:** durante o fechamento da ONDA-40, o sanitizer (adversário histórico do projeto -- ver INFRA-SANITIZER-WORKING-TREE-GUARD-01) stripou 24 ocorrências de U+26A1 em 7 docs de `dev-journey/` (working-tree-only, restauradas via `git checkout`). O guard `check_sanitizer_attack.py` existia mas só cobria 7 arquivos de código e glifos U+25xx -- a corrupção de docs passava silenciosa por ele e pelo emoji-check (não-emoji não é bloqueio). Débito levantado no Checkpoint e materializado a pedido do dono.
**Modelo obrigatório:** claude-opus (sem subagentes)

## 1. Causa-raiz

`PROTECTED` = 7 arquivos `.py`/`.sh`; `CANONICAL_GLYPHS` = U+25xx. O `main()` ignorava qualquer path fora de `PROTECTED`. Docs de dev-journey citam glifos (ex.: o relatório de auditoria mostra o glifo de bypass U+26A1 que foi removido do `cli.py`) para documentar a própria remoção -- mas estavam fora de escopo. Um `git add -A && git commit` cego sobre a working tree corrompida pelo sanitizer entraria no histórico sem bloqueio.

## 2. Fix

`PROTECTED` -> `PROTECTED_CODE` (U+25xx). Novo `DOC_GLYPHS = CANONICAL_GLYPHS | {U+26A1}`. `glyphs_for(path)` devolve o conjunto certo (código U+25xx; `dev-journey/**/*.md` -> DOC_GLYPHS) ou None (fora de escopo). `is_sanitizer_attack`/`_strip_glyphs` ganham parâmetro `glyphs`. A assinatura de detecção (remoção pura: `+linha == -linha sem glifo`, nada mais muda) é reusada -- por isso de-emojificação legítima (glifo -> `U+26A1` texto) passa livre.

## 3. Proof-of-work

- **Probe TDD** (diffs sintéticos, sem tocar git): RED mostrou `doc_strip_zap` passando (0, a brecha); GREEN pós-fix os 4 casos corretos (`doc_strip_zap` 1, `doc_legit_replace` 0, `code_strip_diamond` 1, `doc_normal_edit` 0).
- **Teste real (fluxo git):** strip de 1 U+26A1 em `SPRINT_UX_DESIGN_01.md` + `git add` -> guard exit **1** com mensagem; `git checkout` restaura (16 glifos de volta, diff limpo).
- **Estático:** AST OK, ruff `All checks passed!`, acento rc=0.
- **Invariantes:** 14/14 PASS (inclui #13 smoke boot ok).

## 4. Escopo / notas

- O guard atua em **staged diff** (camada pre-commit): pega o `git add` cego da working tree corrompida. Um watcher de working tree em tempo real seria outra camada (outra sprint, se desejado).
- **Tensão pré-existente (não resolvida aqui, não introduzida aqui):** o emoji-check do pre-commit (`\x{2600}-\x{26FF}` inclui U+26A1, sem exceção de path) bloquearia recommitar um doc que contém o glifo literal. Os docs em HEAD foram grandfathered. Resolver isso (noqa-emoji para docs que citam glifos, ou converter as citações para `U+26A1` texto) é decisão de filosofia anti-emoji -- candidato a sprint própria se o dono quiser.
