# SPRINT VISUAL-LAYOUT-05 — Estético arcano (showcase MVP)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: VISUAL-LAYOUT-05
  title: "Aplicar estético arcano end-to-end como showcase MVP"
  onda: 24
  bloco: 24.2 Visual Layout
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [VISUAL-LAYOUT-01, VISUAL-LAYOUT-03]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/SHOWCASE_AESTHETIC_ARCANO.md
      reason: "Documentar comparativo visual default vs arcano com screenshots"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/SHOWCASE_AESTHETIC_ARCANO.md
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/assets/aesthetics/arcano_boot.png
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/assets/aesthetics/arcano_conversa.png
  removes: []

  forbidden:
    - "Quebrar default (paleta D continua igual)"
    - "Tocar invariante #14 (○ ◐ ●)"

  tests:
    - cmd: "NYX_AESTHETIC=arcano ./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"

  acceptance_criteria:
    - "NYX_AESTHETIC=arcano produz tela com fundo escuro azul-violeta (#0E0820) + accent roxo (#9D4EDD)"
    - "Glifos ╭╮╰╯ mantidos (compatível com arcano)"
    - "○ ◐ ● na toolbar funcionam em arcano"
    - "2 screenshots em assets/aesthetics/"
    - "SHOWCASE_AESTHETIC_ARCANO.md compara default e arcano lado-a-lado"
    - "Smoke ok"
```

---

# Sprint VISUAL-LAYOUT-05 — Arcano showcase

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

VISUAL-LAYOUT-01 cria as estruturas. VISUAL-LAYOUT-03 conecta consumo. VISUAL-LAYOUT-05 prova end-to-end: alternar aesthetic muda a experiência visual real do REPL, e o arcano (roxo profundo) serve como showcase do design system extendido.

---

## Solução

1. Validar manualmente que `NYX_AESTHETIC=arcano ./run.sh` produz tela com palette arcana.
2. Capturar screenshots (scrot/import via xdotool).
3. Documentar showcase em markdown com comparativo default vs arcano.

---

## Comandos de verificação

```bash
# Default
./run.sh &
sleep 4 && scrot -u /tmp/default_boot.png
pkill -f "nyx.cli"
sleep 1

# Arcano
NYX_AESTHETIC=arcano ./run.sh &
sleep 4 && scrot -u /tmp/arcano_boot.png
pkill -f "nyx.cli"

# Copiar pros assets
mkdir -p assets/aesthetics
cp /tmp/arcano_boot.png assets/aesthetics/
```

---

## Critério binário de aceite

- [ ] 2 screenshots em `assets/aesthetics/`
- [ ] SHOWCASE_AESTHETIC_ARCANO.md descreve aesthetic
- [ ] Smoke ok com NYX_AESTHETIC=arcano
- [ ] Default preservado
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `feat(VISUAL-LAYOUT-05): estetico arcano como showcase + screenshots`

---

*"O grimório que pensa em código." — VISUAL-LAYOUT-05*
