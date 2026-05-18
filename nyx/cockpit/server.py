"""FastAPI server do Cockpit (COCKPIT-01, +02 PTY/xterm.js).

Bind APENAS em 127.0.0.1 (ADR-001 Local First). Rotas:
- GET /health
- GET /api/features (lê REGISTRY.yaml)
- GET /static/{path:path} (substituto manual de StaticFiles -- ver COCKPIT-02-FIX-WS-403)
- GET / (index.html)
- WS /stream (broadcast simples; legacy)
- WS /repl (PTY bridge para REPL Nyx embedded) -- COCKPIT-02

NOTA: declarações no module-level (sem create_app function) porque
combinação `create_app function + uvicorn.run(app)` em Starlette 1.0
quebrava handshake WS retornando 403 sem chamar o handler. Workaround
investigado em COCKPIT-02-FIX-WS-403.

Uso direto:
    ./venv/bin/python -m nyx.cockpit.server
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse

from nyx.agent.services.logging_service import get_logger
from nyx.cockpit.pty_bridge import PtyBridge
from nyx.config.defaults import COCKPIT_HOST, COCKPIT_PORT

logger = get_logger("nyx.cockpit")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "dev-journey" / "04-features" / "REGISTRY.yaml"
STATIC_DIR = Path(__file__).resolve().parent / "static"
RUN_SH = REPO_ROOT / "run.sh"
COCKPIT_VERSION = "0.2.0"

_pty_lock = asyncio.Lock()
_active_pty: PtyBridge | None = None
_ws_clients: set[WebSocket] = set()


def _load_registry() -> dict[str, Any]:
    try:
        import yaml
    except ImportError:
        return {"features": [], "total": 0, "error": "pyyaml ausente"}
    if not REGISTRY_PATH.is_file():
        return {"features": [], "total": 0}
    try:
        return yaml.safe_load(REGISTRY_PATH.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 -- yaml malformado nao deve crashar
        logger.warning("registry inválido: %s", exc)
        return {"features": [], "total": 0, "error": str(exc)}


app = FastAPI(title="Nyx Cockpit", version=COCKPIT_VERSION)


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok", "cockpit_version": COCKPIT_VERSION}


@app.get("/api/features")
async def features() -> dict[str, Any]:
    data = _load_registry()
    return {
        "total": data.get("total", 0),
        "features": data.get("features", []),
    }


# Substituto manual de StaticFiles. Bug isolado em COCKPIT-02-FIX-WS-403:
# app.mount("/static", StaticFiles(...)) em Starlette 1.0 derruba WS handshakes.
@app.get("/static/{path:path}")
async def static_files(path: str):
    target = (STATIC_DIR / path).resolve()
    if not str(target).startswith(str(STATIC_DIR.resolve())):
        raise HTTPException(status_code=403, detail="path traversal bloqueado")
    if not target.is_file():
        raise HTTPException(status_code=404)
    return FileResponse(str(target))


@app.get("/", response_class=HTMLResponse)
async def root() -> str:
    idx = STATIC_DIR / "index.html"
    if idx.is_file():
        return idx.read_text(encoding="utf-8")
    return "<h1>Nyx Cockpit</h1>"


@app.websocket("/stream")
async def stream(ws: WebSocket):
    await ws.accept()
    _ws_clients.add(ws)
    try:
        await ws.send_text(json.dumps({"type": "hello", "version": COCKPIT_VERSION}))
        while True:
            msg = await ws.receive_text()
            await ws.send_text(json.dumps({"type": "echo", "data": msg}))
    except WebSocketDisconnect:
        logger.debug("WS /stream desconectado")
    finally:
        _ws_clients.discard(ws)


@app.websocket("/repl")
async def repl(ws: WebSocket):
    """COCKPIT-02: bridge PTY <-> WS para REPL Nyx no browser.

    Apenas 1 sessão PTY por cockpit (segunda conexão recebe 'busy').
    Protocolo: bytes brutos do PTY -> WS frames binários, e vice-versa.
    Mensagens texto JSON são reservadas para metadados (ex: resize).
    """
    global _active_pty
    await ws.accept()
    if _pty_lock.locked():
        await ws.send_text(json.dumps({"type": "busy", "reason": "PTY já alocado"}))
        await ws.close(code=1013)
        return

    async with _pty_lock:
        bridge = PtyBridge([str(RUN_SH)], cwd=str(REPO_ROOT))
        _active_pty = bridge
        try:
            bridge.start()
        except Exception as exc:  # noqa: BLE001 -- spawn falhou
            logger.error("Falha ao spawnar PTY: %s", exc)
            await ws.send_text(json.dumps({"type": "error", "message": str(exc)}))
            await ws.close(code=1011)
            _active_pty = None
            return

        async def _pty_to_ws() -> None:
            try:
                async for data in bridge.read():
                    await ws.send_bytes(data)
            except Exception as exc:  # noqa: BLE001 -- ws fechou ou pty morto
                logger.debug("PTY->WS encerrou: %s", exc)

        reader_task = asyncio.create_task(_pty_to_ws())
        try:
            while True:
                msg = await ws.receive()
                if msg["type"] == "websocket.disconnect":
                    break
                if "bytes" in msg and msg["bytes"] is not None:
                    bridge.write(msg["bytes"])
                elif "text" in msg and msg["text"] is not None:
                    try:
                        meta = json.loads(msg["text"])
                        if meta.get("type") == "resize":
                            bridge.resize(int(meta["rows"]), int(meta["cols"]))
                    except (json.JSONDecodeError, KeyError, ValueError) as exc:
                        logger.debug("WS text inválido (ignorado): %s", exc)
        except WebSocketDisconnect:
            logger.debug("WS /repl desconectado")
        finally:
            reader_task.cancel()
            bridge.close()
            _active_pty = None


def main() -> None:
    import uvicorn

    uvicorn.run(app, host=COCKPIT_HOST, port=COCKPIT_PORT, log_level="info")


if __name__ == "__main__":
    main()
