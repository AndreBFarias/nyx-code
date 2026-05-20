# SPRINT COCKPIT-01 — Servidor FastAPI base + WebSocket + rotas mínimas

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: COCKPIT-01
  title: "Servidor FastAPI em 127.0.0.1:11437 com WS /stream e GET /api/features"
  onda: 23
  bloco: 23.3 Cockpit
  prioridade: ALTA
  tipo: Feature+Infra
  dependencias: [BOOT-VRAM-GUARD-01, SBOM-REGISTRY-02]
  desbloqueia: [COCKPIT-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Adicionar fase de boot do Cockpit (opt-in via --cockpit flag)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/__init__.py
      reason: "Pacote cockpit"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "FastAPI bind 127.0.0.1:11437 com WS /stream, GET /, GET /api/features, GET /health"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/index.html
      reason: "Página HTML mínima — apenas placeholder; UI vem em COCKPIT-03"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "Adicionar COCKPIT_PORT = 11437 (fonte única)"

  removes: []

  n_to_n_pairs:
    - descricao: "COCKPIT_PORT = 11437 só em config/defaults.py — todas as referências importam dele"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh

  forbidden:
    - "Bind em 0.0.0.0 ou IP público (ADR-001 Local First — só 127.0.0.1)"
    - "Aceitar conexões não-loopback (verificar request.client.host)"
    - "Bloquear o REPL Nyx ao subir Cockpit (devem coexistir)"
    - "Importar dependência pesada (FastAPI ok, mas evitar SQLAlchemy/Celery)"
    - "Hardcoded de porta — usar config/defaults.COCKPIT_PORT"
    - "Adicionar emoji; menção a IA"

  tests:
    - cmd: "./run.sh --cockpit --smoke"
      timeout: 60
      deve_passar: true
      nota: "Boot inclui Cockpit; ./run.sh sem --cockpit não inicia (opt-in)"
    - cmd: "curl -sf http://127.0.0.1:11437/health"
      timeout: 10
      deve_passar: true
      nota: "Retorna {'status':'ok', 'cockpit_version':'0.1.0'}"
    - cmd: "curl -sf http://127.0.0.1:11437/api/features | jq '.features | length'"
      timeout: 10
      deve_passar: true
      nota: "Retorna 62 (lê REGISTRY.yaml)"
    - cmd: "curl --resolve test.com:11437:1.2.3.4 -sf http://test.com:11437/health"
      timeout: 5
      deve_passar: false
      nota: "Rejeita conexão não-loopback (status 403)"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "nyx/cockpit/server.py existe e bind 127.0.0.1:11437"
    - "Rota GET /health retorna {status, cockpit_version}"
    - "Rota GET /api/features lê REGISTRY.yaml e retorna JSON com 62 features"
    - "Rota WS /stream aceita conexão e envia heartbeat a cada 5s"
    - "Rejeita conexões não-loopback (403)"
    - "run.sh --cockpit inicia Cockpit em background com PID rastreado para cleanup"
    - "Cockpit não bloqueia REPL Nyx existente (coexistem)"
    - "Cleanup em SIGTERM/SIGINT mata Cockpit corretamente"
    - "Acentuação PT-BR"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint COCKPIT-01

## Solução resumida

```python
# nyx/cockpit/server.py
from fastapi import FastAPI, WebSocket, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import yaml, asyncio
from nyx.config.defaults import COCKPIT_PORT

COCKPIT_VERSION = "0.1.0"
ROOT = Path(__file__).resolve().parent.parent.parent
STATIC = Path(__file__).parent / "static"
REGISTRY = ROOT / "dev-journey/04-features/REGISTRY.yaml"

app = FastAPI(title="Nyx Cockpit", version=COCKPIT_VERSION)

def _require_loopback(request: Request):
    if request.client.host not in ("127.0.0.1", "::1"):
        raise HTTPException(403, "Acesso restrito a loopback")

@app.get("/health")
async def health(request: Request):
    _require_loopback(request)
    return {"status": "ok", "cockpit_version": COCKPIT_VERSION}

@app.get("/api/features")
async def features(request: Request):
    _require_loopback(request)
    if not REGISTRY.exists():
        return {"features": []}
    data = yaml.safe_load(REGISTRY.read_text())
    return {"features": data.get("features", [])}

@app.websocket("/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            await ws.send_json({"type": "heartbeat", "ts": time.time()})
            await asyncio.sleep(5)
    except Exception:
        pass

app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
```

```bash
# run.sh adição
if [ "$COCKPIT" -eq 1 ]; then
    log_boot "Subindo Cockpit na porta $NYX_COCKPIT_PORT..."
    "$SCRIPT_DIR/venv/bin/python" -m uvicorn nyx.cockpit.server:app \
        --host 127.0.0.1 --port $NYX_COCKPIT_PORT \
        >> "$SCRIPT_DIR/logs/cockpit.log" 2>&1 &
    COCKPIT_PID=$!
    disown $COCKPIT_PID 2>/dev/null || true
fi
```

## Verificação

```bash
./run.sh --cockpit --smoke
curl -sf http://127.0.0.1:11437/health | jq .
curl -sf http://127.0.0.1:11437/api/features | jq '.features | length'
```

---

*"Uma porta loopback é uma promessa: o agente nunca sai de casa." -- anônimo*
