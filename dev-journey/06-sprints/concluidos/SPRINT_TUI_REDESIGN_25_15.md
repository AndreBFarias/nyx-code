# SPRINT TUI-REDESIGN-25-15 — 4 schemas de interface (Editorial, Arcano, Brutalist, Hybrid)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-15
  title: "INTERFACE_SCHEMAS dict em design_tokens_extended.py com 4 estruturas completas"
  onda: 25
  bloco: 25.1 Fundamentos visuais
  prioridade: ALTA
  tipo: Feature
  dependencias: [TUI-REDESIGN-25-03]
  desbloqueia: [TUI-REDESIGN-25-16, TUI-REDESIGN-25-06..14]
  origem: "Resposta do usuario em planejamento: construir os 4 schemas como camada de estrutura/layout; reaproveitar aesthetics (cor) e entities (accent)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens_extended.py
      reason: "Adicionar INTERFACE_SCHEMAS com 4 entries: editorial, arcano, brutalist, hybrid (default)"

  creates: []
  removes: []

  forbidden:
    - "Misturar tokens de aesthetic (cor) com schema (estrutura) na mesma chave"
    - "Hardcode de hex fora de design_tokens*"

  tests:
    - cmd: "./venv/bin/python -c 'from nyx.themes.design_tokens_extended import INTERFACE_SCHEMAS; assert set(INTERFACE_SCHEMAS) == {\"editorial\", \"arcano\", \"brutalist\", \"hybrid\"}'"
      timeout: 5
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "INTERFACE_SCHEMAS dict com 4 keys (editorial, arcano, brutalist, hybrid)"
    - "Cada schema contem: prefixes (user, nyx), bubble_style (user, nyx), tool_style, thinking_style, divider_style, banner_style, heading_case"
    - "DEFAULT_SCHEMA = 'hybrid' (decisao usuario)"
    - "Backward-compat: import existente nao quebra"
    - "Smoke + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-15

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criacao:** 2026-05-18
**Modelo obrigatorio:** claude-opus-4-7

## Contexto

Decisao do usuario: separar estrutura (schema) de cor (aesthetic) de accent (entity). Camadas:

- **schema** (4 opcoes: editorial, arcano, brutalist, hybrid) -- estrutura, glifos, prefixes, bubble style
- **aesthetic** (6 opcoes: default + 5 nomeadas) -- paleta de cor (bg, ink, accent base)
- **entity** (7 opcoes) -- override de accent especifico

Esta sprint cria SO a camada de schema. Composicao (compose) e 25-16.

## Solucao proposta

`design_tokens_extended.py` ganha:

```python
INTERFACE_SCHEMAS = {
    "editorial": {
        "user_prefix": ">", "nyx_prefix": "*",
        "user_bubble": "subtle-line", "nyx_bubble": "header-bar",
        "tool_style": "inline", "thinking_style": "row",
        "divider_style": "thin", "banner_style": "type",
        "heading_case": "sentence",
    },
    "arcano": {
        "user_prefix": "+", "nyx_prefix": "+",
        "user_bubble": "ornament-box", "nyx_bubble": "glow-bar",
        "tool_style": "ornament-chip", "thinking_style": "ornament-row",
        "divider_style": "ornament", "banner_style": "ascii-glow",
        "heading_case": "sentence",
    },
    "brutalist": {
        "user_prefix": ">", "nyx_prefix": ">",
        "user_bubble": "bracket-label", "nyx_bubble": "bracket-label",
        "tool_style": "table-row", "thinking_style": "bracket-row",
        "divider_style": "rule", "banner_style": "rule",
        "heading_case": "upper",
    },
    "hybrid": {
        "user_prefix": ">", "nyx_prefix": "*",
        "user_bubble": "soft-box", "nyx_bubble": "side-rule",
        "tool_style": "chip", "thinking_style": "collapsible",
        "divider_style": "thin", "banner_style": "card",
        "heading_case": "sentence",
    },
}

DEFAULT_SCHEMA = "hybrid"
```

NOTA: caracteres `>`, `*`, `+` sao placeholders ASCII na spec. Na implementacao concreta, design_tokens.py mapeia esses keys para glifos Unicode geometricos finais (U+25C6 losango, U+25C7 losango oco, U+2560 fork, etc), preservando invariante #14 (glifos canonicos `o () @`).

## Criterio binario

- [ ] INTERFACE_SCHEMAS com 4 entries
- [ ] DEFAULT_SCHEMA = "hybrid"
- [ ] Backward-compat preservado
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-15): 4 schemas de interface em design_tokens_extended`

## Invariantes

#6, #14.

## Anti-debito

- Composicao runtime (compose + slash /schema) fica para 25-16.
- Render real de cada bubble usa schema mas e trabalhado em sprints especificas (25-07, 25-08, 25-10, 25-13, 25-14).

## Verificacao

```bash
./venv/bin/python -c "from nyx.themes.design_tokens_extended import INTERFACE_SCHEMAS, DEFAULT_SCHEMA; print(DEFAULT_SCHEMA, list(INTERFACE_SCHEMAS))"
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Estrutura define o gesto; cor pinta a alma." -- TUI-REDESIGN-25-15*
