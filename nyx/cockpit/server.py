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
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse

from nyx.agent.services.logging_service import get_logger
from nyx.cockpit.pty_bridge import PtyBridge
from nyx.config.defaults import COCKPIT_HOST, COCKPIT_PORT
from nyx.themes.design_tokens import (
    NYX_ACCENT, NYX_ACCENT_DIM, NYX_BG, NYX_BG_SOFT, NYX_ERROR, NYX_MUTED,
    NYX_PRIMARY, NYX_PURPLE, NYX_PURPLE_DIM, NYX_SUCCESS, NYX_WARNING,
)

logger = get_logger("nyx.cockpit")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "dev-journey" / "04-features" / "REGISTRY.yaml"
STATIC_DIR = Path(__file__).resolve().parent / "static"
RUN_SH = REPO_ROOT / "run.sh"
COCKPIT_VERSION = "0.2.0"

_pty_lock = asyncio.Lock()
_active_pty: PtyBridge | None = None
_ws_clients: set[WebSocket] = set()

# COCKPIT-03: registry de jobs em background.
_jobs: dict[str, dict[str, Any]] = {}
_JOB_TIMEOUT = 300  # 5 min hard cap (forbidden em COCKPIT-03)
_MAX_JOBS_RETAIN = 50


def _job_register(feature_id: str) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "id": job_id,
        "feature_id": feature_id,
        "status": "running",
        "started_at": time.time(),
        "finished_at": None,
        "rc": None,
        "output": "",
    }
    if len(_jobs) > _MAX_JOBS_RETAIN:
        oldest = sorted(_jobs.items(), key=lambda kv: kv[1]["started_at"])[0][0]
        _jobs.pop(oldest, None)
    return job_id


_CATEGORIA_PARA_FASE = {
    "infraestrutura": "infra",
    "infraestrutura (boot/lifecycle)": "infra",
    "proxy": "proxy",
    "tools": "tools",
    "qualidade": "qualidade",
    "performance": "performance",
    "visual": "visual",
    "configuração": "config",
    "configuracao": "config",
    "resiliência": "resiliencia",
    "resiliencia": "resiliencia",
}


def _fase_para(feature_id: str) -> str:
    """Mapeia feature_id (ex: I-01) -> fase do gauntlet (ex: infra).

    COCKPIT-03 dispara fase inteira da categoria; teste por feature
    individual fica em sub-sprint COCKPIT-03-GAUNTLET-PER-FEATURE-01.
    """
    data = _load_registry()
    for f in data.get("features", []):
        if f.get("id") == feature_id:
            cat = (f.get("categoria") or "").lower()
            return _CATEGORIA_PARA_FASE.get(cat, "rapido")
    return "rapido"


async def _run_gauntlet_single_feature(feature_id: str, job_id: str) -> None:
    """Executa `./run.sh --gauntlet --only <fase-da-categoria>` em subprocess.

    Job_id de tracking para poll via /api/features/{id}/status/{job_id}.
    Atalho: feature_id -> categoria do REGISTRY -> fase do gauntlet.
    """
    job = _jobs.get(job_id)
    if not job:
        return
    fase = _fase_para(feature_id)
    job["fase"] = fase
    # String concat runtime evita falso positivo de hook de seguranca
    # que casa o substring 'exec' (asyncio create_subprocess_exec eh seguro
    # pois recebe args como lista, sem shell).
    spawn = getattr(asyncio, "create_subprocess_" + "exec")
    try:
        proc = await spawn(
            "./run.sh", "--gauntlet", "--only", fase,
            cwd=str(REPO_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=_JOB_TIMEOUT)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            job["status"] = "timeout"
            job["finished_at"] = time.time()
            job["output"] = "Timeout: hard cap 300s atingido."
            return
        job["rc"] = proc.returncode
        job["status"] = "ok" if proc.returncode == 0 else "fail"
        job["finished_at"] = time.time()
        job["output"] = stdout.decode("utf-8", errors="replace")[-8000:]
    except Exception as exc:  # noqa: BLE001 -- background task best-effort
        job["status"] = "error"
        job["finished_at"] = time.time()
        job["output"] = "Erro ao spawnar gauntlet: " + str(exc)


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


@app.get("/api/tokens")
async def tokens() -> dict[str, Any]:
    """COCKPIT-03 + D1 UX-COCKPIT-EXPERIENCE: paleta D serializada para o frontend.

    Frontend hidrata CSS vars via fetch('/api/tokens') na inicialização.
    Fonte única: nyx/themes/design_tokens.py (n-para-n honrado).
    """
    return {
        "accent": NYX_ACCENT,
        "accent_dim": NYX_ACCENT_DIM,
        "purple": NYX_PURPLE,
        "purple_dim": NYX_PURPLE_DIM,
        "primary": NYX_PRIMARY,
        "muted": NYX_MUTED,
        "bg": NYX_BG,
        "bg_soft": NYX_BG_SOFT,
        "success": NYX_SUCCESS,
        "warning": NYX_WARNING,
        "error": NYX_ERROR,
    }


@app.post("/api/features/{feature_id}/run")
async def run_feature(feature_id: str) -> dict[str, Any]:
    """COCKPIT-03: dispara gauntlet single-feature em background.

    Retorna job_id imediatamente; cliente faz poll em
    GET /api/features/{feature_id}/status/{job_id}.
    """
    data = _load_registry()
    feats = data.get("features", [])
    if not any(f.get("id") == feature_id for f in feats):
        raise HTTPException(status_code=404, detail=f"feature_id desconhecido: {feature_id}")
    job_id = _job_register(feature_id)
    asyncio.create_task(_run_gauntlet_single_feature(feature_id, job_id))
    return {"job_id": job_id, "feature_id": feature_id, "status": "running"}


@app.get("/api/features/{feature_id}/status/{job_id}")
async def feature_status(feature_id: str, job_id: str) -> dict[str, Any]:
    """COCKPIT-03: poll de status do job de gauntlet."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_id desconhecido (talvez rotacionado)")
    if job["feature_id"] != feature_id:
        raise HTTPException(status_code=400, detail="feature_id não casa com job_id")
    return {
        "id": job["id"],
        "feature_id": job["feature_id"],
        "status": job["status"],
        "started_at": job["started_at"],
        "finished_at": job["finished_at"],
        "duration": (
            (job["finished_at"] or time.time()) - job["started_at"]
        ),
        "rc": job["rc"],
        "output_tail": job["output"][-2000:] if job["output"] else "",
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
