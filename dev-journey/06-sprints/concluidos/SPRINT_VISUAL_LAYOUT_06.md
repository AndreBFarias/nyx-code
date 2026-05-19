# SPRINT VISUAL-LAYOUT-06 — Aesthetics restantes (cyberpunk/brutalist/mecha/editorial)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISUAL-LAYOUT-06
  title: "Aplicar cyberpunk, brutalist, mecha e editorial como showcases adicionais"
  onda: 24
  bloco: 24.2 Visual Layout
  prioridade: BAIXA
  tipo: Feature
  dependencias: [VISUAL-LAYOUT-05]
  desbloqueia: []

  touches: []
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/SHOWCASE_AESTHETICS_GALLERY.md
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/assets/aesthetics/cyberpunk_boot.png
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/assets/aesthetics/brutalist_boot.png
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/assets/aesthetics/mecha_boot.png
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/assets/aesthetics/editorial_boot.png
  removes: []

  forbidden:
    - "Quebrar default ou arcano"
    - "Tocar invariante #14"

  tests:
    - cmd: "for a in cyberpunk brutalist mecha editorial; do NYX_AESTHETIC=$a ./run.sh --smoke; done"
      timeout: 120
      deve_passar: "boot ok em todos os 4"

  acceptance_criteria:
    - "4 screenshots em assets/aesthetics/"
    - "Smoke ok em cada aesthetic"
    - "Galeria documenta cada estética com paleta + glifos"
```

---

# Sprint VISUAL-LAYOUT-06 — Aesthetics restantes

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7
**PNGs (paths absolutos):**
- /home/andrefarias/Desenvolvimento/Nyx-Code/assets/aesthetics/cyberpunk_boot.png
- /home/andrefarias/Desenvolvimento/Nyx-Code/assets/aesthetics/brutalist_boot.png
- /home/andrefarias/Desenvolvimento/Nyx-Code/assets/aesthetics/mecha_boot.png
- /home/andrefarias/Desenvolvimento/Nyx-Code/assets/aesthetics/editorial_boot.png

**Galeria:** /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/SHOWCASE_AESTHETICS_GALLERY.md
**Script:** /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/visual/render_aesthetic_showcase.py
**Achado colateral:** Banner ainda consome accent da ENTITY e glifos hardcoded BOX_CHARS; sprint VISUAL-LAYOUT-09 proposta.

---

## Contexto

Após arcano provar a arquitetura, expande para os outros 4 estéticos. Cada um vai como showcase com screenshot e documentação.

---

## Critério binário de aceite

- [ ] 4 screenshots em `assets/aesthetics/`
- [ ] SHOWCASE_AESTHETICS_GALLERY.md com tabela das 5 aesthetics
- [ ] Smoke ok em cada
- [ ] Commit `feat(VISUAL-LAYOUT-06): 4 aesthetics restantes (cyberpunk/brutalist/mecha/editorial) + galeria`

---

*"Cinco linguagens visuais, um agente." — VISUAL-LAYOUT-06*
