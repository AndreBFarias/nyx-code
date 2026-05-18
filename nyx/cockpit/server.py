"""FastAPI server do Cockpit (COCKPIT-01).

Bind APENAS em 127.0.0.1 (ADR-001 Local First). Rota /health, GET /api/features
(lê REGISTRY.yaml) e WS /stream (broadcast simples).

Uso direto:
    ./venv/bin/python -m nyx.cockpit.server
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import COCKPIT_HOST, COCKPIT_PORT

logger = get_logger("nyx.cockpit")

REGISTRY_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "dev-journey" / "04-features" / "REGISTRY.yaml"
)
STATIC_DIR = Path(__file__).resolve().parent / "static"
COCKPIT_VERSION = "0.1.0"


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


def create_app():
    from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
    from fastapi.responses import HTMLResponse
    from fastapi.staticfiles import StaticFiles

    app = FastAPI(title="Nyx Cockpit", version=COCKPIT_VERSION)
    clients: set[WebSocket] = set()

    @app.middleware("http")
    async def loopback_only(request: Request, call_next):
        client_host = request.client.host if request.client else None
        if client_host not in ("127.0.0.1", "::1", "localhost"):
            raise HTTPException(status_code=403, detail="loopback only (ADR-001)")
        return await call_next(request)

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

    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

        @app.get("/", response_class=HTMLResponse)
        async def root() -> str:
            idx = STATIC_DIR / "index.html"
            if idx.is_file():
                return idx.read_text(encoding="utf-8")
            return "<h1>Nyx Cockpit</h1>"
    else:
        @app.get("/", response_class=HTMLResponse)
        async def root_fallback() -> str:
            return "<h1>Nyx Cockpit</h1>"

    @app.websocket("/stream")
    async def stream(ws: WebSocket):
        await ws.accept()
        clients.add(ws)
        try:
            await ws.send_text(json.dumps({"type": "hello", "version": COCKPIT_VERSION}))
            while True:
                msg = await ws.receive_text()
                # eco simples como MVP
                await ws.send_text(json.dumps({"type": "echo", "data": msg}))
        except WebSocketDisconnect:
            logger.debug("WS /stream desconectado")
        finally:
            clients.discard(ws)

    return app


def main() -> None:
    import uvicorn

    uvicorn.run(create_app(), host=COCKPIT_HOST, port=COCKPIT_PORT, log_level="warning")


if __name__ == "__main__":
    main()
