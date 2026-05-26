# SPRINT 247 — UX-COCKPIT-RESPONSIVE-FIT-01

## 0. SPEC

```yaml
sprint:
  id: UX-COCKPIT-RESPONSIVE-FIT-01
  title: "Terminal cockpit ajusta tamanho ao Chrome maximizado (fullscreen real)"
  onda: 31
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [UX-COCKPIT-FULLSCREEN-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/terminal.html
      reason: "Sprint 245 aplicou CSS 100vw/100vh + fitTerminal mas terminal ainda renderiza em ~640x500 de 1280x800; falta forçar resize após DOMContentLoaded + flex layout"
  creates: []
  removes: []

  forbidden:
    - "Adicionar dependência externa (xterm.js fit-addon não é vendored)"
    - "Quebrar handover de PTY (sprint 246)"
    - "Adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true

  acceptance_criteria:
    - "Chrome maximizado 1920x1080: terminal preenche 100% da viewport descontando 32px de header"
    - "Usuário NÃO precisa rolar barra lateral para ver área de input"
    - "Resize do Chrome em runtime: terminal ajusta cols/rows automaticamente (debounced 80ms)"
    - "Layout funciona em 1280x800, 1366x768, 1920x1080, 2560x1440"
```

---

# Sprint 247 — UX-COCKPIT-RESPONSIVE-FIT-01

**Status:** PENDENTE
**Data criação:** 2026-05-25

## Contexto

Usuário reportou após sprint 245: "altura e largura deve ser a mesma no navegador maximizado, eu tenho que descer na lateral pra poder ver a area de input user". Captura confirma: terminal ocupa ~50% da viewport esquerda; lado direito vazio; scroll lateral aparece.

Sprint 245 aplicou:
- `body, html { width: 100vw; height: 100vh; overflow: hidden }`
- `#terminal { position: fixed; top:32px; left:0; right:0; bottom:0 }`
- `measureCell()` + `fitTerminal()` + debounced resize

Mas terminal renderiza em ~640x500 visualmente, não 100% viewport.

## Hipóteses de causa-raiz

1. **measureCell() retorna tamanho errado** porque chama antes da fonte web carregar (FontFace race).
2. **xterm.js inicializa com cols/rows hardcoded** (80x24) e não recalcula até `term.resize()`.
3. **Container parent `#terminal` não tem flex/display block** que herda dimensões; xterm.js usa `clientWidth` interno que pode ser 0 ou cached.
4. **CSS `.xterm-viewport` ou `.xterm-screen` não está se ajustando** porque xterm.js sobrescreve width/height inline.

## Solução

Fase 1 — diagnóstico empírico via DevTools Chrome:
```bash
./run.sh --web &
sleep 18
google-chrome --new-window --window-size=1920,1080 http://127.0.0.1:11437/static/terminal.html &
sleep 5
# Console JS:
#   document.getElementById('terminal').clientWidth
#   document.querySelector('.xterm-screen').clientWidth
#   term.cols, term.rows
# Comparar com window.innerWidth.
```

Fase 2 — fix:
- `document.fonts.ready.then(() => fitTerminal())` antes do `term.open()`.
- `term.open(div)` → `fitTerminal()` IMEDIATO + dentro `requestAnimationFrame` aninhado para garantir layout (browser paint).
- CSS adicional: `.xterm { display: block; width: 100%; height: 100%; }` (sem !important onde já há).
- ResizeObserver no `#terminal` (não só window.resize) para reagir a layout changes do header.

## Acceptance

- [ ] Chrome 1920x1080 maximizado: terminal preenche ~1900x1000px (margem header).
- [ ] Sem scroll lateral visível.
- [ ] Resize do Chrome ajusta cols/rows em <200ms.
- [ ] Smoke + invariantes preservados.

## Proof-of-work

Captura visual antes/depois via `import -window` da janela maximizada. SHA distinto entre ANTES (640x500 efetivo) e DEPOIS (1900x1000 efetivo).
