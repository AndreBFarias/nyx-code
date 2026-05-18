# SPRINT TUI-REDESIGN-25-03 — Tokens de bubble (user/Nyx) em design_tokens_extended.py

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-03
  title: "Tokens de bubble (user soft-box + Nyx side-rule) em design_tokens_extended.py"
  onda: 25
  bloco: 25.1 Fundamentos visuais
  prioridade: ALTA
  tipo: UX
  dependencias: [TUI-REDESIGN-25-02]
  desbloqueia: [TUI-REDESIGN-25-07, TUI-REDESIGN-25-08]
  origem: "Auditoria audit.jsx -- problemas P02 (Duplicação prompt usuário) e P03 (Rótulo 'você' impessoal)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens_extended.py
      reason: "Adicionar bloco BUBBLE_STYLES com kind (soft-box, side-rule, bracket-label, ornament-box) por schema"

  creates: []
  removes: []

  forbidden:
    - "Hardcode de hex fora de design_tokens*"
    - "Quebrar default backward-compat (paleta D continua igual)"

  tests:
    - cmd: "./venv/bin/python -c 'from nyx.themes.design_tokens_extended import BUBBLE_STYLES; assert len(BUBBLE_STYLES) >= 4'"
      timeout: 5
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "BUBBLE_STYLES dict com 4 kinds: soft-box, side-rule, bracket-label, ornament-box"
    - "Cada kind tem: glyphs (chars), padding, color tokens"
    - "Default = soft-box cyan (user) + side-rule purple (Nyx)"
    - "Smoke + invariantes 14/14"
    - "Backward-compat: import existente nao quebra"
```

---

# Sprint TUI-REDESIGN-25-03

**Status:** CONCLUIDA
**Data criacao:** 2026-05-18
**Data conclusao:** 2026-05-18
**Modelo obrigatorio:** claude-opus-4-7

## Contexto

P02 + P03: bubble user e caixa ASCII redundante (eco do prompt ja mostrou o texto) e o rotulo "voce" e impessoal. Esta sprint estabelece o vocabulario de bubbles em tokens -- implementacao visual fica para 25-07 e 25-08.

## Solucao proposta

`design_tokens_extended.py` ganha:

```python
BUBBLE_STYLES = {
    "soft-box":     {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|", "color_token": "accent2"},
    "side-rule":    {"side": "|", "color_token": "accent",  "padding_left": 2},
    "bracket-label":{"open": "[", "close": "]", "color_token": "ink", "uppercase": True},
    "ornament-box": {"tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|", "color_token": "accent"},
}

DEFAULT_USER_BUBBLE = "soft-box"
DEFAULT_NYX_BUBBLE = "side-rule"
```

NOTA: glifos finais (corners arredondados, ornamentos) vivem em design_tokens com nomes (BOX_CHARS, ROUND_CHARS, ORNAMENT_CHARS) -- esta sprint apenas referencia keys. A implementacao concreta usa caracteres Unicode geometricos (nao-emoji) como U+256D, U+25C6, etc.

## Criterio binario

- [ ] BUBBLE_STYLES presente
- [ ] 4 kinds (soft-box, side-rule, bracket-label, ornament-box)
- [ ] Default = soft-box (user) + side-rule (Nyx)
- [ ] Smoke + invariantes 14/14
- [ ] Sprint movida
- [ ] Commit `feat(TUI-REDESIGN-25-03): tokens de bubble em design_tokens_extended`

## Invariantes a preservar

#6, #14.

## Anti-debito

- Render de cada bubble fica para 25-07 (user) e 25-08 (Nyx).
- Aplicacao por schema fica para 25-15.

## Verificacao

```bash
./venv/bin/python -c "from nyx.themes.design_tokens_extended import BUBBLE_STYLES; print(list(BUBBLE_STYLES))"
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Cada bubble fala uma estrutura; o token define o vocabulario." -- TUI-REDESIGN-25-03*
