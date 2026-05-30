# SPRINT 306 — TUI-INPUT-HEIGHT-5-SCROLL-01 (encarnação Textual)

> Nota de ID: a 226 (concluída) usou o mesmo ID no `repl_app.py`/prompt_toolkit, removido na ONDA-32.
> Esta é a re-implementação no Textual; arquivo nomeado com o número 306 para não colidir com
> `SPRINT_TUI_INPUT_HEIGHT_5_SCROLL_01.md` (a 226).

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-INPUT-HEIGHT-5-SCROLL-01
  title: "Input com 5 linhas fixas + scrollbar interna (Ctrl+J), sem corte da borda pela toolbar"
  onda: 35
  prioridade: ALTA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "compose: input + toolbar agrupados em Vertical#bottombar (dock:bottom unico)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "InputWidget height fixo 7 (5+borda), #bottombar dock:bottom, remover dock dos filhos"
  creates: []
  removes: []

  forbidden:
    - "Tocar no autofoco (307) ou no scroll da conversa (309)"
    - "Adicionar emoji / mencao a IA / except silencioso / print fora de cli-output"
    - "Hex fora de design_tokens.py"

  acceptance_criteria:
    - "Input mostra 5 linhas de conteudo com borda completa (topo+base), sem corte pela toolbar"
    - "Conteudo alem de 5 linhas (Ctrl+J) rola DENTRO do input com scrollbar interna"
    - "Toolbar permanece visivel e intacta abaixo do input"
    - "Smoke + invariantes 14/14 + gauntlet rapido APROVADO"
```

---

**Status:** CONCLUIDA
**Data criação:** 2026-05-30
**Data conclusão:** 2026-05-30
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Problema

A área de input aparecia **cortada** (borda inferior comida pela toolbar — no `--web` o box ficava com ~2 linhas) e o usuário pediu **5 linhas fixas** com **scrollbar interna** quando o Ctrl+J passa de 5 linhas. Confirmado visualmente no `--web`.

## Causa-raiz (mais profunda que "altura")

O `InputWidget` no `nyx.tcss` tinha `height: auto; min-height: 3; max-height: 10`. Mas o problema central **não era só a altura**: `InputWidget` e `Toolbar` eram **dois widgets `dock: bottom` soltos** no mesmo container. O Textual não reservava o espaço somado — o `#chat` (1fr) descontava apenas o input e a **toolbar caía sobre a borda inferior do input** (sobreposição de 1 linha). Diagnóstico via Pilot (viewport 100x30): `#chat` h=23, `#input` y=23..29 (h=7) e `#toolbar` y=29 → colisão na linha 29. Com a altura elástica pequena (vazio) o sintoma ficava mascarado; com 5 linhas, a soma estourava e cortava.

## Fix

1. `app.py compose()`: agrupar input + toolbar em `with Vertical(id="bottombar")` (import `Vertical`). Um único `dock: bottom` reserva `input(7) + toolbar(1) = 8` e o `#chat` (1fr) fica com o resto.
2. `nyx.tcss`: `InputWidget { height: 7; ... }` fixo (5 linhas de conteúdo + 2 da borda round; box-model do Textual inclui a borda em `height`) + `scrollbar-size-vertical: 1` e cores de scrollbar; remover `dock: bottom` do InputWidget e da Toolbar; novo bloco `#bottombar { dock: bottom; height: auto; }`. Scroll interno é nativo do TextArea quando o conteúdo excede 5 linhas.

## Proof-of-work

```
FAIL_BEFORE=0 -> FAIL_AFTER=0 (14/14)
ruff app.py: All checks passed!   acentuacao app.py+nyx.tcss: rc=0
gauntlet --only rapido: 19/19 (100%) APROVADO
```

**Pilot (`/tmp/val_306_input.py`, viewport 100x30):**
```
vazio: content.height=5 outer.height=7
8 linhas: content.height=5 outer.height=7 max_scroll_y=3   (scroll interno OK)
input outer y=22..29 | toolbar y=29 h=1                    (toolbar intacta, sem corte)
layout: #chat 0..21 | #input 22..28 | #toolbar 29          (soma 30 = viewport)
```

**--web real (playwright, digitando 7 linhas com Ctrl+J, lendo o buffer `.xterm-rows`):**
```
51: ╭─────────────...─────────────╮   (borda topo completa)
52: │ 3                          │
53: │ 4                        ▅ │     (scrollbar interna -- thumb)
54: │ 5                          │
55: │ 6                          │
56: │ 7                          │
57: ╰─────────────...─────────────╯   (borda base -- NAO cortada)
58:  Ctx 0% | qwen2.5-coder:3b | ... | shift+tab: ...   (toolbar intacta abaixo)
```
Digitadas 7 linhas → mostra as últimas 5 (3–7) com scrollbar; borda topo+base completa; toolbar na linha 58 sem corte. (Nota: o screenshot do canvas xterm.js não pinta em headless; o buffer DOM `.xterm-rows` é a evidência fiel — e mais precisa que pixels.)

## Critério de aceite

- [x] 5 linhas de conteúdo com borda completa, sem corte.
- [x] Scroll interno (scrollbar) com mais de 5 linhas via Ctrl+J.
- [x] Toolbar intacta abaixo.
- [x] Smoke + invariantes 14/14 + gauntlet rápido 19/19 APROVADO; ruff e acentuação limpos.

---

*"Cinco linhas bastam para um pensamento; o resto rola e espera." -- anônimo*
