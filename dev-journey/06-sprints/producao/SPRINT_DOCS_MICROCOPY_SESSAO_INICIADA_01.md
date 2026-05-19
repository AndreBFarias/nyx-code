# SPRINT DOCS-MICROCOPY-SESSAO-INICIADA-01 — Capitalizar referência em MICROCOPY.md

## 0. SPEC

```yaml
sprint:
  id: DOCS-MICROCOPY-SESSAO-INICIADA-01
  title: "Atualizar dev-journey/05-guides/MICROCOPY.md:109 de 'sessão iniciada' para 'Sessão Iniciada' (paridade com TUI-REDESIGN-28-01)"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code (anti-débito)
  prioridade: BAIXA
  tipo: Docs
  dependencias: [TUI-REDESIGN-28-01]
  desbloqueia: []
  origem: "Achado colateral durante execução de TUI-REDESIGN-28-01 pelo executor-sprint: doc cita literal minúsculo enquanto código já foi capitalizado. Materialização anti-débito conforme memória feedback_nenhum_debito.md."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/MICROCOPY.md
      reason: "linha 109: 'sessão iniciada' → 'Sessão Iniciada' (paridade com nyx/themes/design_tokens.py e run.sh)"

  forbidden:
    - "Alterar outras entries do MICROCOPY.md fora da linha 109"
    - "Mudar lógica de microcopy_audit.py (só MD)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "./venv/bin/python scripts/microcopy_audit.py --check"
      timeout: 30
      deve_passar: "zero violações"
    - cmd: "grep -n 'Sessão Iniciada' dev-journey/05-guides/MICROCOPY.md"
      timeout: 5
      deve_passar: ">= 1 match"

  acceptance_criteria:
    - "MICROCOPY.md cita 'Sessão Iniciada' (capitalizado) em linha 109"
    - "microcopy_audit --check zero violações"
    - "Smoke ok"

  proof_of_work:
    - "git diff dev-journey/05-guides/MICROCOPY.md mostra única mudança: 'sessão iniciada' → 'Sessão Iniciada' na linha 109"
```

---

# Sprint DOCS-MICROCOPY-SESSAO-INICIADA-01

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Rollback

`git reset --hard HEAD~1`
