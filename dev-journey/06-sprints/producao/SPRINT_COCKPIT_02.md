# SPRINT COCKPIT-02 — REPL embedded via PTY + xterm.js no browser

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: COCKPIT-02
  title: "REPL Nyx no browser via PTY + xterm.js (bridge PTY ↔ WS)"
  onda: 23
  bloco: 23.3 Cockpit
  prioridade: ALTA
  tipo: Feature
  dependencias: [COCKPIT-01]
  desbloqueia: [COCKPIT-03]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "Adiciona WS /repl que faz bridge PTY <-> WebSocket"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/index.html
      reason: "Adiciona xterm.js (CDN local) + canvas terminal"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/pty_bridge.py
      reason: "Helper assíncrono que controla subprocess PTY e converte bytes <-> WS frames"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/xterm.js
      reason: "xterm.js standalone (vendored, ADR-001 Local First — zero CDN externo)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/xterm.css
      reason: "Estilos xterm vendored"

  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Carregar xterm.js de CDN remoto (ADR-001)"
    - "Spawn subprocess sem timeout"
    - "PTY com tty inheritance que possa vazar entrada do shell pai"
    - "Permitir múltiplas sessões PTY em paralelo (1 sessão por cockpit por enquanto)"
    - "Adicionar emoji"

  tests:
    - cmd: "./run.sh --cockpit"
      timeout: 60
      deve_passar: true
    - cmd: "websocat ws://127.0.0.1:11437/repl < /dev/null && echo ok"
      timeout: 15
      deve_passar: true
      nota: "Aceita conexão; PTY spawnado"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "Rota WS /repl spawna PTY com ./run.sh"
    - "Bytes do PTY são enviados como frames WS para o browser"
    - "Input do browser é gravado no PTY via WS"
    - "xterm.js renderiza terminal funcional (cores ANSI 24-bit funcionam)"
    - "Claude (Chrome MCP) consegue acessar http://127.0.0.1:11437 e ver REPL ativo"
    - "Cleanup: ao fechar tab/desconectar WS, PTY é morto (sem órfão)"
    - "Apenas 1 sessão PTY por cockpit (concurrent rejeitado com 'busy')"
    - "Acentuação PT-BR; PT-BR no terminal embedded"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint COCKPIT-02

## Solução

### `nyx/cockpit/pty_bridge.py`

```python
import asyncio, os, pty, signal, subprocess
from typing import AsyncIterator

class PtyBridge:
    def __init__(self, cmd: list[str]):
        self.cmd = cmd
        self.proc: subprocess.Popen | None = None
        self.master_fd: int | None = None

    def start(self):
        self.master_fd, slave_fd = pty.openpty()
        self.proc = subprocess.Popen(
            self.cmd, stdin=slave_fd, stdout=slave_fd, stderr=slave_fd,
            start_new_session=True,
        )
        os.close(slave_fd)

    async def read(self) -> AsyncIterator[bytes]:
        loop = asyncio.get_event_loop()
        while True:
            data = await loop.run_in_executor(None, os.read, self.master_fd, 4096)
            if not data:
                break
            yield data

    def write(self, data: bytes):
        os.write(self.master_fd, data)

    def close(self):
        if self.proc:
            self.proc.send_signal(signal.SIGTERM)
            self.proc.wait(timeout=5)
        if self.master_fd:
            os.close(self.master_fd)
```

### Adição em `nyx/cockpit/server.py`

```python
@app.websocket("/repl")
async def repl(ws: WebSocket):
    await ws.accept()
    bridge = PtyBridge(["./run.sh"])
    bridge.start()
    async def reader():
        async for data in bridge.read():
            await ws.send_bytes(data)
    asyncio.create_task(reader())
    try:
        async for msg in ws.iter_bytes():
            bridge.write(msg)
    finally:
        bridge.close()
```

### `index.html` minimal

```html
<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Nyx Cockpit</title>
  <link rel="stylesheet" href="/xterm.css">
  <script src="/xterm.js"></script>
</head>
<body>
  <div id="terminal"></div>
  <script>
    const term = new Terminal({theme: {background: '#0E1116', foreground: '#E8E8E8'}});
    term.open(document.getElementById('terminal'));
    const ws = new WebSocket('ws://' + location.host + '/repl');
    ws.binaryType = 'arraybuffer';
    ws.onmessage = (e) => term.write(new Uint8Array(e.data));
    term.onData((d) => ws.send(new TextEncoder().encode(d)));
  </script>
</body>
</html>
```

## Verificação

```bash
./run.sh --cockpit
# abrir http://127.0.0.1:11437 no Chrome — ver REPL Nyx ativo
# Claude via Chrome MCP: tabs_context_mcp + read_page para validar
```

---

*"O terminal no browser é o REPL onde Claude e humano se encontram." -- anônimo*
