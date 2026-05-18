# COCKPIT_WEB_GUIDE -- Validação Playwright do TUI no browser

Guia operacional para validar a Nyx TUI no browser usando Playwright
(externo) ou Chrome MCP. Reflexo da Onda 26 que reformulou `--web`
(sprint **COCKPIT-WEB-REDESIGN-01..03**).

## Quando usar

- Validar mudanças visuais no TUI sem precisar interagir manualmente
  no terminal local (capturar screenshot, comparar com mockups em
  `novo_layout/v2_referencias/nyx-session-render.jsx`).
- Testar fluxos REPL completos em CI (ex: gauntlet validar resposta
  visual de erros, /quit card etc.).
- Acompanhar a Nyx executando algo em background enquanto o REPL TUI
  local está ocupado com outra coisa.

## Pré-requisitos

- `./run.sh --web` rodando (cockpit em `127.0.0.1:11437` + Ollama +
  proxy bootados).
- Playwright disponível (via MCP em editor externo, ou `pip install
  playwright` + binários Chromium).
- Sem `--gauntlet` ou `--headless` ativos no mesmo run (eles desabilitam
  o REPL interativo).

## Seção 1 -- Iniciar

```bash
# Terminal A: sobe o stack completo + abre browser local.
./run.sh --web
# Quando ver "[nyx] browser aberto em http://127.0.0.1:11437/",
# o cockpit está pronto.
```

A rota `/` agora serve o **terminal Nyx** (xterm.js + PTY). A rota
`/dashboard` continua servindo o painel de gauntlet (legacy). Sprint
**COCKPIT-WEB-REDESIGN-01** fez essa troca.

Quando o browser conecta no WS `/repl`, o cockpit detecta se o proxy
em `:11436` está UP. Se sim, spawna apenas `./venv/bin/python nyx/cli.py`
(REPL puro reusando Ollama/proxy já bootados). Se não, fallback para
`./run.sh` completo. Sprint **COCKPIT-WEB-REDESIGN-02** fez essa
detecção.

## Seção 2 -- Navegar (Playwright)

```javascript
// Exemplo via Playwright API (Node)
await page.goto('http://127.0.0.1:11437/');
// title esperado: "Nyx Cockpit -- REPL"
const title = await page.title();
console.log(title);
```

Equivalente via MCP em editor externo:
```
mcp__plugin_playwright_playwright__browser_navigate
  url: http://127.0.0.1:11437/

mcp__plugin_playwright_playwright__browser_take_screenshot
  type: png
  filename: nyx_tui_now.png
  fullPage: true
```

## Seção 3 -- Interagir (control API)

Enviar input para o REPL ativo (atalho para digitar no xterm.js sem
precisar de keyboard automation):

```bash
# Envia "oi" + Enter como se o usuário tivesse digitado.
curl -X POST http://127.0.0.1:11437/control/repl/send \
  -H "Content-Type: application/json" \
  -d '{"text":"oi\n"}'
# Resposta esperada: {"sent_bytes": 3, "ok": true}
```

Ações comuns:

```bash
# Pedir /help (3 colunas categorizadas, sprint 25-13)
curl -X POST http://127.0.0.1:11437/control/repl/send \
  -d '{"text":"/help\n"}'

# Pedir /schema list (4 schemas, sprint 25-16)
curl -X POST http://127.0.0.1:11437/control/repl/send \
  -d '{"text":"/schema list\n"}'

# Encerrar com card de stats (sprint 25-14)
curl -X POST http://127.0.0.1:11437/control/repl/send \
  -d '{"text":"/quit\n"}'
```

## Seção 4 -- Validar (screenshot + compare)

```javascript
// Após enviar input, espera renderização do xterm.js
await page.waitForTimeout(2000);
await page.screenshot({
  path: 'nyx_apos_oi.png',
  fullPage: true,
});
```

Compare visualmente com mockup de referência:

```bash
diff -q \
  novo_layout/v2_referencias/nyx-session-render.jsx \
  /tmp/nyx_apos_oi.png  # diff de bytes não-trivial; comparação visual manual
```

## Seção 5 -- Encerrar

```bash
# 1. Encerra REPL com /quit (renderiza card de stats da sessão)
curl -X POST http://127.0.0.1:11437/control/repl/send \
  -d '{"text":"/quit\n"}'

# 2. Encerra o cockpit + Ollama + proxy
pkill -f "nyx.cockpit.server"
pkill -f "ollama serve"
pkill -f "nyx/proxy.py"

# Ou simplesmente Ctrl+C no terminal A (./run.sh --web) -- o trap EXIT
# já limpa Ollama + proxy + lock file.
```

## Smoke test completo

```bash
# Sobe stack + valida tudo via curl + Playwright via MCP
./run.sh --web > /tmp/cockpit.log 2>&1 &
sleep 8
curl -s http://127.0.0.1:11437/health
curl -s http://127.0.0.1:11437/ | grep -o "<title>.*</title>"
# esperado: <title>Nyx Cockpit -- REPL</title>

curl -s http://127.0.0.1:11437/dashboard | grep -o "<title>.*</title>"
# esperado: <title>Nyx Cockpit -- Dashboard</title>

# Após navegar via Playwright para abrir WS /repl:
curl -X POST http://127.0.0.1:11437/control/repl/send \
  -H "Content-Type: application/json" \
  -d '{"text":"oi\n"}'
# esperado: {"sent_bytes": 3, "ok": true}
```

## Endpoints Control API (COCKPIT-05)

- `POST /control/repl/send` -- escreve texto no PTY ativo
- `GET /control/repl/snapshot?lines=N` -- (buffer ainda não implementado;
  retorna placeholder)
- `POST /control/gauntlet/run` -- dispara gauntlet completo
- `GET /control/gauntlet/status/{job_id}` -- poll do job
- `POST /control/feature/{id}/run` -- dispara feature single
- `GET /control/registry` -- REGISTRY.yaml completo

## Limitações conhecidas

- **Sem buffer de snapshot**: `/control/repl/snapshot` não retorna
  histórico de output. Use Playwright `browser_take_screenshot` para
  capturar o que está visível.
- **Uma sessão PTY por vez**: segunda conexão WS `/repl` recebe `busy`.
  Feche a primeira aba antes de abrir outra.
- **Sem TLS**: cockpit roda em HTTP local (`127.0.0.1:11437`). ADR-001
  Local First.

## Próximos passos (já materializados como sprints)

- **STREAMING-SIDE-RULE-01** -- faixa lateral `│` em cada linha
  streamada (M2).
- **TUI-REDESIGN-25-09-PARTE-2** -- captura real do thinking + Tab
  keybinding (M3).
- **TUI-REDESIGN-26-01..04** -- bubble soft-box, header inline-leading,
  tool chip glyph-per-tool, card encerramento grid 3x2.
- **TUI-REDESIGN-26-05** -- onboarding pede nome + persiste em
  `~/.nyx/config.toml`.
