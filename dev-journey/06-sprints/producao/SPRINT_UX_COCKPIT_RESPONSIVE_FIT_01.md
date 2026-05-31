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

## Investigação 2026-05-26 (NÃO reproduz no Playwright -- MANTÉM PENDENTE)

Tentativa de repro no Chromium do Playwright + medição DOM:
- Viewport limpa 1920x1080: `innerW=1920 termW=1920 vpW=1897 domRows=80` -> preenche.
- Resize runtime 1366x768: `termW=1366 vpW=1343 domRows=56` -> re-ajusta (handler
  `window.resize` existente funciona).
- O "640x500" reproduzido foi ARTEFATO do investigador: viewport do Playwright
  travada em 1280 + janela OS esticada a 1920 via `wmctrl` -> faixa preta. Confirmado
  por readout (`screenW=1280 vvScale=1 dpr=1`) e flags do processo
  (`--user-data-dir=.../ms-playwright/mcp-chrome-*`, `--no-sandbox`).

PENDÊNCIA REAL: o bug foi reportado no Chrome DIÁRIO do usuário (perfil default,
janelas "Ouroboros"), não medido aqui (extensão MCP do navegador desconectada). **Sprint
permanece PENDENTE** até repro/medição no Chrome real do usuário. Decisão do usuário
2026-05-26: "deixa em aberto, não classifica como concluída".

## Investigação 2026-05-31 (pós-ONDA-35; re-disparada pelo usuário) — MANTÉM PENDENTE

Re-verificado no playwright (viewport real via `setViewportSize`), já com as mudanças das ondas 32-35 no `terminal.html`:
- **O fit FUNCIONA no testável.** 1920x1080: `innerW=1920 terminalW=1920 screenW=1912 viewportW=1897` → preenche; altura `1048/1040` (desconta o header de 32px). Resize runtime 1366x768: `screenW=1358` → re-ajusta. Sem regressão das ondas de TUI.
- **Causa #1 (FontFace race) NÃO se aplica:** a fonte é `ui-monospace` (nativa do sistema, sem web font); `document.fonts.status == "loaded"`. Não há corrida de carregamento.
- **Fix defensivo TENTADO e REVERTIDO — NÃO re-tentar:** um `ResizeObserver` no `#terminal` reusando o refit-por-recriação (`scheduleRefit`→`recreateTerminal`) causou **tiling (25 input boxes empilhados)** no resize: o `recreateTerminal` altera o layout interno e **re-dispara o ResizeObserver → novo recreate → loop**. `ResizeObserver` + `recreateTerminal` é incompatível. Revertido para `git diff` limpo (terminal.html idêntico ao commitado).
- **Conclusão:** não é resolvível sem o ambiente do usuário. **Para avançar, medição no Chrome real dele** (cockpit maximizado, DevTools console): `document.getElementById('terminal').clientWidth`, `document.querySelector('.xterm-screen').clientWidth`, `window.innerWidth`. Se `screenW << innerW`, reproduz e revela a causa (provável: zoom/devtools/extensão do perfil alterando o layout sem disparar `window.resize`). Aí o fix vira cirúrgico (não especulativo).
