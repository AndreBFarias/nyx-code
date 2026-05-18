# SPRINT VISUAL-LAYOUT-03 — Theme engine no terminal (CSS-like vars no Rich)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISUAL-LAYOUT-03
  title: "Theme engine no terminal — Rich consome paleta via design_tokens_extended"
  onda: 24
  bloco: 24.2 Visual Layout
  prioridade: MÉDIA
  tipo: Refactor
  dependencias: [VISUAL-LAYOUT-01]
  desbloqueia: [VISUAL-LAYOUT-05, VISUAL-LAYOUT-08]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/theme_manager.py
      reason: "Adicionar resolve_palette() que consome design_tokens_extended.get_active()"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Cores via theme_manager.resolve_palette() em vez de import direto de design_tokens"
  creates: []
  removes: []

  forbidden:
    - "Hardcode de hex fora de design_tokens*"
    - "Quebrar invariante #14 (glifos canônicos)"
    - "Quebrar modo default (paleta D continua igual)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "NYX_AESTHETIC=arcano NYX_ENTITY=luna ./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "theme_manager.resolve_palette() lê NYX_AESTHETIC + NYX_ENTITY"
    - "output.py consome paleta via theme_manager"
    - "Default behavior idêntico (paleta D)"
    - "Smoke ok"
```

---

# Sprint VISUAL-LAYOUT-03 — Theme engine

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

VISUAL-LAYOUT-01 cria as estruturas estáticas. VISUAL-LAYOUT-03 conecta o consumo: `output.py` (Rich render layer) precisa pegar cores via theme_manager em vez de import direto. Permite alternância em runtime.

---

## Solução

Adicionar `resolve_palette(aesthetic=None, entity=None)` no `theme_manager.py` que:
- Se nada passado: lê env vars
- Cacheia última paleta por (aesthetic, entity)
- Retorna estrutura compatível com o que `output.py` espera (hex strings)

`output.py` substitui `from nyx.themes.design_tokens import NYX_PRIMARY` por `palette = theme_manager.resolve_palette(); accent = palette["palette"]["accent"]`.

---

## Critério binário de aceite

- [ ] `theme_manager.resolve_palette()` existe e cacheia
- [ ] `output.py` consome via theme_manager
- [ ] `NYX_AESTHETIC=arcano ./run.sh` muda cores
- [ ] Default permanece paleta D
- [ ] Smoke ok
- [ ] Invariantes 14/14
- [ ] Sprint movida → `concluidos/`
- [ ] Commit `refactor(VISUAL-LAYOUT-03): theme engine no terminal via theme_manager`

---

## Riscos

| Risco | Mitigação |
|---|---|
| Performance: cada chamada chama compose() | Cache via lru_cache |
| Quebrar UX-LAYOUT-01A/01B (banner) | Banner usa o mesmo theme_manager, preserva ADR-029 |

---

*"A identidade adapta; o gosto pelo glifo permanece." — VISUAL-LAYOUT-03*
