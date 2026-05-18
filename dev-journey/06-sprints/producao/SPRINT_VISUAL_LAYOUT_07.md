# SPRINT VISUAL-LAYOUT-07 — Spinner Braille + meter inline

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISUAL-LAYOUT-07
  title: "Spinner Braille + meter inline com paleta aesthetic-aware"
  onda: 24
  bloco: 24.2 Visual Layout
  prioridade: BAIXA
  tipo: Feature
  dependencias: [VISUAL-LAYOUT-01, VISUAL-LAYOUT-03]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Spinner Braille + meter consomem palette atual via theme_manager"
  creates: []
  removes: []

  forbidden:
    - "Substituir ○ ◐ ● por Braille (esses são canônicos #14)"
    - "Spinner que blocking thread principal"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"

  acceptance_criteria:
    - "Spinner Braille ⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏ animado em operações async"
    - "Meter inline (ex: progresso de download) usa ▰▱▰▱ ou similar"
    - "Cores via theme_manager (não hardcoded)"
    - "○ ◐ ● preservados na toolbar"
    - "Smoke ok"
    - "Invariantes 14/14"
```

---

# Sprint VISUAL-LAYOUT-07 — Spinner Braille + meter

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

novo_layout/src/sections-features.jsx mostra spinner Braille (⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏) com cores aesthetic-aware. Hoje o spinner Nyx é genérico.

---

## Solução

Atualizar spinners existentes em `output.py` para usar Braille pattern. Meter inline para downloads (ex: `apt-get`, `ollama pull`).

---

## Critério binário de aceite

- [ ] Spinner Braille animado em operações async
- [ ] Meter inline para progresso longo
- [ ] Cores via theme_manager
- [ ] ○ ◐ ● na toolbar preservados
- [ ] Smoke ok
- [ ] Invariantes 14/14
- [ ] Commit `feat(VISUAL-LAYOUT-07): spinner Braille + meter inline aesthetic-aware`

---

*"O pulso visual da máquina." — VISUAL-LAYOUT-07*
