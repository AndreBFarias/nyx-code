# Cockpit Control API -- uso por Claude via Chrome MCP / curl

Bind: `127.0.0.1:11437` (ADR-001 Local First, loopback-only via bind).

Spec base: COCKPIT-01..05 + UX-COCKPIT-EXPERIENCE-01.

---

## Endpoints HTTP

### GET /health

```bash
curl -s http://127.0.0.1:11437/health
# => {"status":"ok","cockpit_version":"0.2.0"}
```

### GET /api/features

Lista todas as 62 features do REGISTRY.yaml.

```bash
curl -s http://127.0.0.1:11437/api/features | jq '.total'
# => 62
```

### GET /api/tokens (COCKPIT-03)

Paleta D (turquesa + roxo + neutros + erro) para o frontend hidratar CSS vars.

```bash
curl -s http://127.0.0.1:11437/api/tokens | jq '.accent'
# => "#00D4AA"
```

### POST /api/features/{feature_id}/run (COCKPIT-03)

Dispara gauntlet para a fase associada à categoria da feature.

```bash
curl -s -X POST http://127.0.0.1:11437/api/features/I-01/run
# => {"job_id": "uuid-...", "feature_id": "I-01", "status": "running"}
```

404 se `feature_id` desconhecido.

### GET /api/features/{feature_id}/status/{job_id} (COCKPIT-03)

Poll de progresso. Status: `running | ok | fail | timeout | error`.

```bash
curl -s http://127.0.0.1:11437/api/features/I-01/status/<job_id>
# => {"id": "...", "status": "ok", "duration": 5.2, "rc": 0, "output_tail": "..."}
```

### POST /api/screenshot (COCKPIT-04)

Recebe PNG do canvas xterm (form-data: `feature_id`, `img`). Hard cap 1MB.

```bash
curl -s -X POST http://127.0.0.1:11437/api/screenshot \
  -F feature_id=I-01 \
  -F img=@/tmp/canvas.png
# => {"path": "dev-journey/07-reports/evidencia/I-01/<ts>.png", "size_bytes": 12345}
```

Rotação: até 5 PNGs por feature; mais antigos deletados. REGISTRY.yaml atualizado com `evidencia_path` da última.

### GET /api/evidencia (COCKPIT-04)

Lista evidências (agregado ou por feature).

```bash
curl -s http://127.0.0.1:11437/api/evidencia
# => {"total": 7, "por_feature": {"I-01": 3, "P-02": 4}}

curl -s "http://127.0.0.1:11437/api/evidencia?feature_id=I-01"
# => {"feature_id": "I-01", "evidencias": [{"path": "...", "size_bytes": ...}, ...]}
```

---

## Control API (COCKPIT-05)

Endpoints `/control/*` expostos para automação Claude/MCP.

### POST /control/gauntlet/run

Dispara `./run.sh --gauntlet` (todas as fases). Hard cap 600s.

```bash
curl -s -X POST http://127.0.0.1:11437/control/gauntlet/run
# => {"job_id": "uuid-...", "state": "iniciado"}
```

### GET /control/gauntlet/status/{job_id}

Estado de qualquer job (gauntlet completo ou feature-single).

```bash
curl -s http://127.0.0.1:11437/control/gauntlet/status/<job_id>
# => {"job_id": "...", "state": "running"|"ok"|"fail"|"timeout"|"error",
#     "duration": 12.3, "rc": null|0|1, "log_tail": "..."}
```

### POST /control/feature/{id}/run

Alias semântico de `POST /api/features/{id}/run`.

### POST /control/repl/send

Envia bytes para o PTY ativo (sessão WebSocket /repl aberta).

```bash
curl -s -X POST http://127.0.0.1:11437/control/repl/send \
  -H 'Content-Type: application/json' \
  -d '{"text": "/help\n"}'
# => {"sent_bytes": 6, "ok": true}
```

409 se nenhuma sessão PTY ativa.

### GET /control/repl/snapshot

Últimas N linhas do REPL. Buffer ainda não implementado (anti-débito COCKPIT-05-SNAPSHOT-BUFFER-01).

```bash
curl -s "http://127.0.0.1:11437/control/repl/snapshot?lines=20"
# => {"active": true|false, "lines": [], "note": "..."}
```

### GET /control/registry

REGISTRY.yaml completo para introspecção.

```bash
curl -s http://127.0.0.1:11437/control/registry | jq '.features[0]'
```

---

## WebSocket /repl (COCKPIT-02)

Bridge bidirecional PTY <-> WS. Apenas 1 sessão por cockpit (segunda recebe `{type:"busy"}`).

Protocolo:
- Server -> Client: bytes brutos do PTY (xterm renderiza).
- Client -> Server (bytes): input do usuário (xterm.onData).
- Client -> Server (text JSON): metadados, ex.: `{"type":"resize","rows":24,"cols":80}`.

Exemplo Python:
```python
import asyncio, websockets
async def main():
    async with websockets.connect("ws://127.0.0.1:11437/repl") as ws:
        data = await ws.recv()
        print(data)  # bytes do banner Nyx
        await ws.send(b"/help\n")
asyncio.run(main())
```

---

## WebSocket /stream (legacy, COCKPIT-01)

Eco simples para teste de conectividade. Não usado em produção.

---

## Fluxo de automação típico (Claude/Chrome MCP)

```
1. mcp__claude-in-chrome__navigate http://127.0.0.1:11437
2. mcp__claude-in-chrome__read_page  # ver dashboard com 62 cards
3. POST /control/feature/I-01/run -> job_id
4. GET /control/gauntlet/status/<job_id> (poll até state=ok)
5. mcp__claude-in-chrome__computer screenshot -> arquivo local
6. POST /api/screenshot {feature_id: "I-01", img: <PNG>}
7. GET /api/evidencia?feature_id=I-01 -> confirmar path salvo
```

Para validação completa de release v1.0 (VALIDATE-FINAL-01):

```
for feature in REGISTRY.yaml:
    POST /control/feature/{feature.id}/run
    poll status
    POST /api/screenshot
```

---

*"API é a linguagem em que dois agentes se reconhecem." -- COCKPIT-05*
