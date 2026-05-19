# SPRINT VISUAL-LAYOUT-09 — Banner consome glyphs e accent puros do aesthetic (RASCUNHO)

**Origem:** Achado colateral durante SPRINT_VISUAL_LAYOUT_06 (2026-05-19).
**Status:** RASCUNHO — aguarda /planejar-sprint para formalizar spec yaml.
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto empírico

Durante VISUAL-LAYOUT-06, capturas via `build_banner` produziram PNGs visualmente idênticos para cyberpunk/brutalist/mecha/editorial. Investigação revelou que `nyx/agent/banner.py`:

1. Linha 39: usa `_ANSI = current_ansi()` em import-time, e `current_ansi()` consome `compose(aesthetic, entity)` onde **entity sobrescreve accent**. Com `NYX_ENTITY=nyx` (default), accent é sempre `#00D4AA` (teal Nyx) — não importa o aesthetic.
2. Linhas 21-28: importa `BOX_CHARS` de `design_tokens.py` (constante hardcoded `╭ ╮ ╰ ╯ ─ │`), não `current_glyphs()` de `theme_manager`. Glifos `┏ ┓` (cyberpunk), `+ |` (brutalist), `( )` (editorial) nunca aparecem no banner.

## Evidência

- PNG correto via script auxiliar: `dev-journey/07-reports/proofs/VISUAL_LAYOUT_06/banner_cyberpunk.png` (mostra `┏ ┓` + cyan `#00F5FF`).
- Output literal de `NYX_AESTHETIC=cyberpunk ./venv/bin/python -c 'from nyx.agent.banner import build_banner; print(build_banner("qwen2.5-coder:3b", 35, "Nyx-Code"))'` mostra ANSI `38;2;0;212;170` (teal) + `╭╮╰╯`.

## Decisão pendente

ADR-029 dita "entity sobrescreve accent" como design intencional. Três opções:

- (a) Banner usa aesthetic puro (decoupla de entity).
- (b) Slot separado: entity glow vs aesthetic structure.
- (c) Duas camadas: cantos/linhas vêm do aesthetic, accent textual da entity.

Decidir antes de implementar.

## Touches estimados

- `nyx/agent/banner.py`

## Acceptance esperado

- `NYX_AESTHETIC=cyberpunk ./venv/bin/python -c 'from nyx.agent.banner import build_banner; print(build_banner("qwen2.5-coder:3b", 35, "Nyx-Code"))'` produz banner com glifos `┏ ┓` e cyan cyberpunk `#00F5FF` visível.
- Smoke + invariantes 14/14.

## Prioridade

BAIXA — showcase concluído via `scripts/visual/render_aesthetic_showcase.py`. Bug é qualidade de DX, não funcional. Onda 24.2 Visual Layout.

---

*Rascunho aberto pelo executor-sprint da VISUAL-LAYOUT-06. Promover via /planejar-sprint.*
