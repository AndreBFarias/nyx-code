# SPRINT 298 — TUI-BANNER-SCROLLABLE-01

## 0. SPEC

```yaml
sprint:
  id: TUI-BANNER-SCROLLABLE-01
  title: "Tornar o banner rolável: remover dock:top e torná-lo o 1º filho do #chat, de modo que role junto com a conversa (a scrollbar do #chat passa a cobrir banner+chat); só Input/Toolbar (dock:bottom) ficam fora do scroll"
  onda: 34
  prioridade: MEDIA
  tipo: Feature
  dependencias: [TUI-CHAT-LABELS-COLORS-01]
  desbloqueia: []

  origem: "Matriz de auditoria ONDA-34 (plano redesign, linhas 36/52/78): banner FIXO (dock:top) — usuário quer rolável; 'remover dock:top; banner vira primeiro filho do #chat (rola junto)'."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/app.py
      reason: "compose(): banner deixa de ser yielded como sibling docked e passa a ser yielded DENTRO de `with VerticalScroll(id='chat'):` como 1º filho."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/banner.py
      reason: "Remover `dock: top;` do DEFAULT_CSS do BannerWidget (era o que pinava o banner mesmo dentro do #chat) — bloco CSS puro, zero glifo tocado."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/styles/nyx.tcss
      reason: "Remover `dock: top;` do bloco BannerWidget (app stylesheet) + atualizar comentário."
  creates: []
  removes: []

  forbidden:
    - "Tocar nyx/agent/banner.py (o banner CLI legado — ESSE é o #14-protegido; o widget Textual nyx/agent/tui/widgets/banner.py NÃO está no check #14)"
    - "Tocar os glifos/render do BannerWidget (só o bloco DEFAULT_CSS)"
    - "Quebrar a ordem dock:bottom de Input/Toolbar"
    - "Mexer no recreate-Terminal do 282 (a rolagem é interna ao Textual, transparente ao PTY/xterm.js)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 15
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "banner é o 1º filho do #chat (não mais sibling docked)"
    - "ao rolar o #chat, o banner sai do viewport (region.y < topo do #chat)"
    - "Input/Toolbar continuam dock:bottom (fora do scroll)"
    - "invariantes 14/14 (inclui #14 sobre nyx/agent/banner.py — intocado)"
```

## 1. PROOF-OF-WORK (CONCLUIDA — 2026-05-30)

**Implementação (3 arquivos):**
- `app.py` compose(): `with VerticalScroll(id="chat"): yield banner` (banner vira 1º filho do
  #chat; os ChatMessages são `mount`-ados depois, abaixo dele). Antes: `yield banner` + `yield VerticalScroll(id="chat")` vazio.
- `banner.py` (widget Textual): `DEFAULT_CSS` perde `dock: top;`.
- `nyx.tcss`: bloco `BannerWidget` perde `dock: top;` + comentário atualizado.

**Causa-raiz de um falso "não-rola" (debug):** remover o dock só do `nyx.tcss` NÃO bastou — o
banner continuava pinado (`region.y=1` mesmo com `scroll_y=25`). O `dock: top;` vivia TAMBÉM no
`DEFAULT_CSS` do próprio `BannerWidget` (banner.py), que o app-stylesheet não sobrescreve quando
não declara `dock`. Fix completo exigiu remover de AMBOS.

**Correção de premissa da auditoria:** o "CUIDADO banner.py #14" confundiu dois arquivos —
o `#14` checa `nyx/agent/banner.py` (banner CLI legado), enquanto a feature toca
`nyx/agent/tui/widgets/banner.py` (widget Textual), que NÃO está no check #14. Edit seguro.

**Validação:**
- Pilot programático (definitivo): ANTES scroll `banner.region.y=1`; DEPOIS `scroll_end`
  `banner.region.y=-24` (banner ACIMA do viewport = True), `chat.scroll_y=25`. O banner é o
  1º filho do #chat.
- **Visual (Pilot SVG→PNG):** `/tmp/banner_top.png` mostra o banner no topo do #chat com a
  scrollbar cobrindo banner+chat; `/tmp/banner_scrolled_fixed.png` mostra o banner FORA de cena
  após rolar (mensagens 5-11 preenchem a tela).
- `py_compile` OK; `validar-acentuacao` (banner.py) rc 0; #14 banner.py legado CF count inalterado.
- `./run.sh --smoke` (invariantes #13): boot OK com a nova árvore.
- `bash scripts/sprint_invariants.sh`: 14/14 (FAIL=0).
- `./run.sh --gauntlet --only rapido`: APROVADO.
- recreate-Terminal (282): interação NULA por construção — a rolagem é interna ao #chat do
  Textual; o byte-stream para o xterm.js é o mesmo full-frame, o sizing do recreate independe
  de banner docked vs scrollado.
