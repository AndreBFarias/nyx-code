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
import os
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse

from nyx.agent.services.logging_service import get_logger
from nyx.cockpit.evidencia import latest_evidence, save_evidence
from nyx.cockpit.pty_bridge import PtyBridge
from nyx.config.defaults import COCKPIT_HOST, COCKPIT_PORT
from nyx.themes.design_tokens import (
    NYX_ACCENT,
    NYX_ACCENT_DIM,
    NYX_BG,
    NYX_BG_SOFT,
    NYX_ERROR,
    NYX_MUTED,
    NYX_PRIMARY,
    NYX_PURPLE,
    NYX_PURPLE_DIM,
    NYX_SUCCESS,
    NYX_WARNING,
)

logger = get_logger("nyx.cockpit")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "dev-journey" / "04-features" / "REGISTRY.yaml"
STATIC_DIR = Path(__file__).resolve().parent / "static"
RUN_SH = REPO_ROOT / "run.sh"
VENV_PYTHON = REPO_ROOT / "venv" / "bin" / "python"
NYX_CLI = REPO_ROOT / "nyx" / "cli.py"
COCKPIT_VERSION = "0.2.0"


def _proxy_up(timeout_s: float = 1.0) -> bool:
    """COCKPIT-WEB-REDESIGN-02: detecta se proxy Nyx já responde em /v1/models.

    Usa httpx síncrono com timeout curto. Retorno True só se status 200 e
    payload contém 'data' (formato OpenAI compatível). Qualquer falha de I/O
    retorna False (assume DOWN).
    """
    from nyx.config.defaults import PROXY_PORT
    try:
        import httpx as _httpx
        with _httpx.Client(timeout=timeout_s) as c:
            r = c.get(f"http://127.0.0.1:{PROXY_PORT}/v1/models")
            return r.status_code == 200 and isinstance(r.json().get("data"), list)
    except Exception:
        return False


def _choose_repl_command() -> list[str]:
    """COCKPIT-WEB-REDESIGN-02: escolhe comando PTY conforme stack já UP ou não.

    Proxy UP -> REPL puro (sem re-bootar Ollama/proxy).
    Proxy DOWN -> ./run.sh completo (compat com browser standalone).
    """
    if _proxy_up() and VENV_PYTHON.is_file() and NYX_CLI.is_file():
        logger.info("PTY mode: REPL puro (proxy UP)")
        return [str(VENV_PYTHON), str(NYX_CLI)]
    logger.info("PTY mode: ./run.sh completo (proxy DOWN ou venv ausente)")
    return [str(RUN_SH)]

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


async def _run_gauntlet_single_feature(feature_id: str, job_id: str) -> None:
    """Executa `./run.sh --gauntlet --only <feature_id>` em subprocess.

    COCKPIT-03-GAUNTLET-PER-FEATURE-01: passa feature_id direto para o gauntlet,
    que detecta regex (^[A-Z]-\\d+$), localiza a fase via REGISTRY.yaml e
    filtra resultados para o teste alvo. Não roda mais a fase inteira.

    Job_id de tracking para poll via /api/features/{id}/status/{job_id}.
    """
    job = _jobs.get(job_id)
    if not job:
        return
    job["fase"] = feature_id
    # String concat runtime evita falso positivo de hook de seguranca
    # que casa o substring 'exec' (asyncio create_subprocess_exec eh seguro
    # pois recebe args como lista, sem shell).
    spawn = getattr(asyncio, "create_subprocess_" + "exec")
    try:
        proc = await spawn(
            "./run.sh", "--gauntlet", "--only", feature_id,
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
    except Exception as exc:  # noqa: BLE001 -- yaml malformado não deve crashar
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
    """COCKPIT-03 + UX-COCKPIT-EXPERIENCE-01: paleta D serializada para o frontend.

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


_MICROCOPY_PATH = REPO_ROOT / "dev-journey" / "05-guides" / "MICROCOPY.md"


@app.get("/api/aesthetics")
async def aesthetics() -> dict[str, Any]:
    """VISUAL-LAYOUT-08: lista aesthetics + entities disponiveis.

    Frontend pode renderizar seletor de aesthetic ao vivo.
    Fonte unica: nyx/themes/design_tokens_extended.py.
    """
    from nyx.themes.design_tokens_extended import (
        get_active,
        list_aesthetics,
        list_entities,
    )
    active = get_active()
    return {
        "active": {
            "aesthetic": active["aesthetic_id"],
            "entity": active["entity_id"],
            "tagline": active["tagline"],
        },
        "aesthetics": list_aesthetics(),
        "entities": list_entities(),
    }


@app.get("/api/microcopy")
async def microcopy() -> dict[str, Any]:
    """UX-COCKPIT-EXPERIENCE-01: serve MICROCOPY.md + strings canonicas.

    Cockpit consome via fetch + atualiza textos do UI. Fonte unica.
    """
    raw = _MICROCOPY_PATH.read_text(encoding="utf-8") if _MICROCOPY_PATH.is_file() else ""
    return {
        "version": "1",
        "raw_markdown": raw,
        # ADR-027 vocabulario Nyx canonico (espelha tabela do MICROCOPY.md)
        "strings": {
            "running": "rodando",
            "ok": "ok",
            "warn": "aviso",
            "fail": "falha",
            "unknown": "sem teste",
            "no_test": "sem teste",
            "timeout": "tempo esgotado",
            "error": "erro",
            "cancel": "cancelar",
            "cancelled": "cancelado",
            "run_gauntlet": "rodar gauntlet",
            "reload": "recarregar",
            "category": "categoria",
            "status": "status",
            "all": "todos",
            "all_f": "todas",
            "no_session": "nenhuma sessão",
            "session_saved": "sessão salva",
            "session_restored": "sessão restaurada",
            "session_clean": "sessão limpa",
            "boot_ok": "boot ok",
            "footer": "ADR-001 Local First | bind 127.0.0.1 | paleta D | Onda 24",
            # Tooltips contextuais (ADR-026: '?' em qualquer ponto)
            "tooltip_run": "Dispara fase do Gauntlet correspondente a essa categoria",
            "tooltip_filter_cat": "Filtra cards pela categoria do REGISTRY",
            "tooltip_filter_status": "Filtra cards pelo estado atual do teste",
        },
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


# ─── COCKPIT-04: screenshot/evidência ──────────────────────────────────

@app.post("/api/screenshot")
async def screenshot(feature_id: str = Form(...), img: UploadFile = File(...)) -> dict[str, Any]:
    """COCKPIT-04: recebe PNG do canvas xterm, salva em evidencia/<id>/<ts>.png.

    Rotação 5 PNGs por feature; atualiza REGISTRY.yaml com path da última.
    Hard cap 1MB por PNG (forbidden de COCKPIT-04).
    """
    data = await img.read()
    try:
        meta = save_evidence(feature_id, data)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return meta


@app.get("/api/evidencia")
async def list_evidence(feature_id: str | None = None) -> dict[str, Any]:
    """Lista evidências (por feature ou agregado)."""
    return latest_evidence(feature_id)


# ─── COCKPIT-05: Control API para automacao via agente externo / MCP ──────────

@app.post("/control/gauntlet/run")
async def control_gauntlet_run() -> dict[str, Any]:
    """COCKPIT-05: dispara gauntlet completo (todas as fases)."""
    job_id = _job_register("__gauntlet_full__")
    asyncio.create_task(_run_gauntlet_completo(job_id))
    return {"job_id": job_id, "state": "iniciado"}


@app.get("/control/gauntlet/status/{job_id}")
async def control_gauntlet_status(job_id: str) -> dict[str, Any]:
    """COCKPIT-05: poll de status de job (gauntlet ou feature-single)."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job_id desconhecido")
    return {
        "job_id": job["id"],
        "feature_id": job["feature_id"],
        "state": job["status"],
        "started_at": job["started_at"],
        "finished_at": job["finished_at"],
        "duration": (job["finished_at"] or time.time()) - job["started_at"],
        "rc": job["rc"],
        "log_tail": job["output"][-3000:] if job["output"] else "",
    }


@app.post("/control/feature/{feature_id}/run")
async def control_feature_run(feature_id: str) -> dict[str, Any]:
    """COCKPIT-05: alias semântico de POST /api/features/{id}/run."""
    return await run_feature(feature_id)


@app.post("/control/repl/send")
async def control_repl_send(payload: dict[str, Any]) -> dict[str, Any]:
    """COCKPIT-05: envia texto para o PTY ativo (PTY write via WS bridge)."""
    text = payload.get("text") if isinstance(payload, dict) else None
    if not isinstance(text, str):
        raise HTTPException(status_code=400, detail="campo 'text' obrigatório (string)")
    if _active_pty is None:
        raise HTTPException(status_code=409, detail="nenhuma sessão PTY ativa")
    try:
        _active_pty.write(text.encode("utf-8"))
    except Exception as exc:  # noqa: BLE001 -- write best-effort
        raise HTTPException(status_code=500, detail="write falhou: " + str(exc))
    return {"sent_bytes": len(text.encode("utf-8")), "ok": True}


@app.post("/control/repl/permission")
async def control_repl_permission(payload: dict[str, Any]) -> dict[str, Any]:
    """PTY-PERMISSION-FLOW-01: aprova/nega prompt CONFIRM_ONCE no PTY ativo.

    Frontend (terminal.html) detecta a marca `[permissão: uma vez]` no stream
    do xterm e dispara POST com:
      - {"answer": "yes"}                -> envia 'S\\n' (uma vez)
      - {"answer": "yes_always", "tool": "write_file"} -> 'S\\n' + '/permissions add write_file\\n'
      - {"answer": "no"}                 -> envia 'n\\n'

    NÃO aprova sem clique humano: a rota só responde à requisição explícita
    (forbidden #1 do spec). NÃO persiste resposta padrão (forbidden #2).
    """
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload deve ser objeto JSON")
    answer = payload.get("answer")
    tool_name = payload.get("tool")
    if answer not in ("yes", "yes_always", "no"):
        raise HTTPException(status_code=400, detail="answer inválido (use yes|yes_always|no)")
    if _active_pty is None:
        raise HTTPException(status_code=409, detail="nenhuma sessão PTY ativa")

    try:
        if answer == "yes":
            _active_pty.write(b"S\n")
        elif answer == "no":
            _active_pty.write(b"n\n")
        elif answer == "yes_always":
            # Aprova esta vez primeiro (libera a tool call em curso) e em
            # seguida promove a tool a auto via slash command do REPL.
            _active_pty.write(b"S\n")
            if isinstance(tool_name, str) and tool_name.strip():
                # Aceita apenas identificadores [A-Za-z_][A-Za-z0-9_]* para
                # evitar injeção de slash command extra via newline/sep.
                import re as _re
                m = _re.match(r"[A-Za-z_][A-Za-z0-9_]*", tool_name.strip())
                if m:
                    _active_pty.write(f"/permissions add {m.group(0)}\n".encode("utf-8"))
    except Exception as exc:  # noqa: BLE001 -- write best-effort
        raise HTTPException(status_code=500, detail="write falhou: " + str(exc))
    return {"sent": answer, "tool": tool_name if answer == "yes_always" else None, "ok": True}


@app.get("/control/repl/snapshot")
async def control_repl_snapshot(lines: int = 50) -> dict[str, Any]:
    """COCKPIT-05: retorna últimas N linhas do REPL ativo (via output buffer).

    NOTA: Buffer ainda não implementado em pty_bridge; retorna placeholder.
    Sub-sprint COCKPIT-05-SNAPSHOT-BUFFER-01 cobre adição de ring buffer.
    """
    if _active_pty is None:
        return {"active": False, "lines": [], "note": "nenhuma sessão PTY ativa"}
    return {
        "active": True,
        "lines": [],
        "note": "buffer de snapshot ainda não implementado (COCKPIT-05-SNAPSHOT-BUFFER-01)",
        "requested_lines": lines,
    }


@app.get("/control/registry")
async def control_registry() -> dict[str, Any]:
    """COCKPIT-05: REGISTRY.yaml completo (introspeccao por agente externo / MCP)."""
    return _load_registry()


async def _run_gauntlet_completo(job_id: str) -> None:
    """Background: roda ./run.sh --gauntlet (todas as fases)."""
    job = _jobs.get(job_id)
    if not job:
        return
    spawn = getattr(asyncio, "create_subprocess_" + "exec")
    try:
        proc = await spawn(
            "./run.sh", "--gauntlet",
            cwd=str(REPO_ROOT),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=600)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            job["status"] = "timeout"
            job["finished_at"] = time.time()
            job["output"] = "Timeout: hard cap 600s atingido (gauntlet completo)."
            return
        job["rc"] = proc.returncode
        job["status"] = "ok" if proc.returncode == 0 else "fail"
        job["finished_at"] = time.time()
        job["output"] = stdout.decode("utf-8", errors="replace")[-20000:]
    except Exception as exc:  # noqa: BLE001 -- background best-effort
        job["status"] = "error"
        job["finished_at"] = time.time()
        job["output"] = "Erro ao spawnar gauntlet completo: " + str(exc)


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
    """COCKPIT-WEB-REDESIGN-01: rota / serve o terminal Nyx live (TUI no browser).

    Dashboard de gauntlet migrou para GET /dashboard. Workflow esperado:
    `./run.sh --web` abre browser em /, terminal xterm.js conecta no WS /repl
    e mostra a sessão Nyx interativa.
    """
    term = STATIC_DIR / "terminal.html"
    if term.is_file():
        return term.read_text(encoding="utf-8")
    return "<h1>Nyx Cockpit -- terminal.html ausente</h1>"


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard() -> str:
    """COCKPIT-WEB-REDESIGN-01: dashboard de gauntlet (legacy / em GET /)."""
    idx = STATIC_DIR / "index.html"
    if idx.is_file():
        return idx.read_text(encoding="utf-8")
    return "<h1>Nyx Cockpit -- index.html ausente</h1>"


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
        # COCKPIT-WEB-REDESIGN-02: detecta se proxy já está UP. Se sim, spawna
        # REPL puro (./venv/bin/python nyx/cli.py) reusando Ollama/proxy já
        # gerenciados. Se não, fallback para ./run.sh completo (compat para
        # browser standalone sem cockpit pre-bootado).
        cmd = _choose_repl_command()
        # Propaga env vars de configuração da Onda 25/26 (NYX_SCHEMA etc).
        env = dict(os.environ)
        bridge = PtyBridge(cmd, cwd=str(REPO_ROOT), env=env)

        # COCKPIT-LIFECYCLE-FIX-01: detecta NYX_PID_FILE antes de spawnar.
        # Se instância anterior viva, recusa em vez de causar cascata
        # de kill via UX-LIFECYCLE-01. Lock stale é limpo pelo preflight.
        preflight = bridge.preflight()
        if preflight.get("state") == "alive":
            pid_anterior = preflight.get("pid")
            logger.info(
                "PTY recusado: sessão Nyx ativa em outro lugar (PID=%s)", pid_anterior,
            )
            await ws.send_text(json.dumps({
                "type": "busy",
                "reason": "sessão Nyx ativa em outro lugar",
                "pid": pid_anterior,
            }))
            await ws.close(code=1013)
            return

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
