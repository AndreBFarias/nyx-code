# SPRINT 231 — INFRA-SANITIZER-VENDOR-RESTORE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-VENDOR-RESTORE-01
  title: "Restaurar glifo U+25C6 em xterm.js vendored (achado colateral sprint 230)"
  onda: 31
  prioridade: BAIXA
  tipo: Bugfix
  dependencias: [INFRA-SANITIZER-RECIDIVA-08]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/vendor/xterm.js
      reason: "Glifo ◆ U+25C6 zerado pelo vetor sanitizer histórico (CHARSETS[0] DEC graphics)"
  creates: []
  removes: []

  forbidden:
    - "Tocar em código vendored manualmente (apenas git checkout)"
    - "Tocar em outros arquivos do cockpit"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "nyx/cockpit/static/vendor/xterm.js tem U+25C6 c6=1 (restaurado)"
    - "Smoke boot ok"
    - "Invariantes 14/14 PASS preservado da sprint 230"
    - "Gauntlet --only rapido APROVADO"
```

---

# Sprint 231 — INFRA-SANITIZER-VENDOR-RESTORE-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

Achado colateral catalogado pelo validador da sprint 230 (INFRA-SANITIZER-RECIDIVA-08): arquivo vendored `nyx/cockpit/static/vendor/xterm.js` também sofreu corrupção do vetor sanitizer histórico — glifo `◆` U+25C6 em `CHARSETS[0]["\`"]` (DEC graphics legacy) removido.

Impacto funcional: nulo (DEC charset legacy raramente usado em terminais modernos).
Importância estratégica: prova que o vetor NÃO se limita aos 7 arquivos do invariante #14 — qualquer arquivo com glifo U+25xx é vulnerável.

## Fix aplicado

Fix trivial via `git checkout`. Arquivo é vendored (commit e9707fc COCKPIT-02 introduziu via download, zero modificação humana subsequente).

```bash
git checkout e9707fc -- nyx/cockpit/static/vendor/xterm.js
# verificação:
python3 -c "from pathlib import Path; t = Path('nyx/cockpit/static/vendor/xterm.js').read_text(); print(t.count(chr(0x25C6)))"
# → 1 (restaurado, era 0)
```

## Proof-of-work

```
ANTES: c6=0 (recidiva confirmada)
DEPOIS: c6=1 (commit e9707fc original restaurado)
Smoke: boot ok exit 0
Invariantes: PASS=14/14 FAIL=0 (preserva sprint 230)
```

## Próximo passo recomendado (deferido)

Sprint futura `INFRA-SANITIZER-VENDOR-AUDIT-01`: scan amplo de todos os arquivos do repo (não só 7 protegidos) para detectar corrupção residual em vendor/. Foge ao escopo desta sprint trivial.

---

*"Achado catalogado vira sprint. Fix em uma linha vira commit. Débito não existe." — protocolo*
