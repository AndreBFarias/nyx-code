"""Boot pieces e shutdown do REPL.

Extraído de nyx/cli.py em INFRA-CLI-SPLIT-03. Helpers puros (sem state global)
chamados uma vez no boot, a cada turno do REPL, ou no shutdown ordenado.
"""

from __future__ import annotations

import asyncio
import os
import time
from logging import Logger
from pathlib import Path
from typing import Any


def init_sandbox_roots(settings: Any, project_root: Path, logger: Logger) -> None:
    """PROJECT-ROOTS-MULTI-01: inicializa sandbox roots no módulo base.

    _ACTIVE_ROOT recebe o project_root atual; extras do env/toml entram
    via add_extra_root() (idempotente). Paths inexistentes são logados
    e ignorados -- sandbox preserva strictness (não autoriza fantasmas).
    """
    try:
        from nyx.agent.tools.base import add_extra_root, set_active_project_root

        set_active_project_root(str(project_root))
        for raw in settings.extra_roots:
            try:
                cand = Path(raw).expanduser()
                if cand.exists() and cand.is_dir():
                    add_extra_root(cand)
                else:
                    logger.warning(
                        "NYX_EXTRA_ROOTS ignorou caminho inválido: %s", cand
                    )
            except Exception as _exc:  # noqa: BLE001 -- boot best-effort
                logger.warning("extra root %s falhou: %s", raw, _exc)
    except Exception as _exc:  # noqa: BLE001 -- boot best-effort
        logger.warning("inicialização de sandbox roots falhou: %s", _exc)


def compute_prompt_str(
    app_state: dict,
    accent: str,
    bold: str,
    nc: str,
) -> str:
    """TUI-REDESIGN-27-02: prompt customizado com nome + template opcional.

    Default: "  > {nome} " (mockup-faithful). NYX_PROMPT_TEMPLATE aceita
    placeholders {user_name}/{schema}/{model}; rejeita template com escape
    ANSI inline (anti-injection).
    """
    from nyx.config.defaults import DEFAULT_MODEL

    _u_name = str(app_state.get("user_display_name") or "visitante")
    _schema_now = os.environ.get("NYX_SCHEMA", "hybrid")
    _model_now = os.environ.get("NYX_MODEL", DEFAULT_MODEL)
    _tpl = os.environ.get("NYX_PROMPT_TEMPLATE", "").strip()
    if _tpl and "\033" not in _tpl and "\\033" not in _tpl:
        try:
            _body = _tpl.format(
                user_name=_u_name, schema=_schema_now, model=_model_now,
            )
        except (KeyError, IndexError, ValueError):
            _body = f"> {_u_name} "
    else:
        _body = f"> {_u_name} "
    return f"  {accent}{bold}{_body}{nc} "


def render_quit_card(
    agent: Any,
    app_state: dict,
    project_root: Path,
) -> None:
    """TUI-REDESIGN-25-14: card de stats da sessão antes do shutdown."""
    from nyx.agent.output import render_session_stats_card

    _sess = agent.session
    _started = app_state.get("session_started_monotonic")
    _duration = (
        time.monotonic() - float(_started)
        if isinstance(_started, (int, float))
        else 0.0
    )
    _sess_id = (
        getattr(_sess, "id", None)
        or getattr(_sess, "session_id", None)
    )
    _saved = (
        getattr(_sess, "path", None)
        or getattr(_sess, "save_path", None)
    )
    _tokens_raw = app_state.get("total_tokens") or 0
    _tokens = int(_tokens_raw) if int(_tokens_raw) > 0 else None
    render_session_stats_card(
        iterations=int(getattr(_sess, "iteration", 0) or 0),
        files_read=int(getattr(_sess, "files_read_count", 0) or 0),
        files_modified=int(
            getattr(_sess, "files_modified_count", 0) or 0
        ),
        duration_s=_duration,
        tokens=_tokens,
        session_id=str(_sess_id) if _sess_id else None,
        saved_path=str(_saved) if _saved else None,
        project_root=str(project_root),
    )


async def run_quit_shutdown(
    proxy_url: str,
    logger: Logger,
) -> None:
    """SUDO-MODE-01 + UX-LIFECYCLE-01: wipe + admin/shutdown best-effort."""
    try:
        from nyx.agent.tools import sudo_session as _sudo_quit
        _sudo_quit.wipe()
    except Exception as _exc:  # noqa: BLE001 -- shutdown best-effort
        logger.debug("sudo wipe best-effort falhou: %s", _exc)
    try:
        import httpx as _httpx_quit

        async with _httpx_quit.AsyncClient(timeout=2.0) as _qs:
            await _qs.post(f"{proxy_url}/admin/shutdown")
    except Exception as _exc:  # noqa: BLE001 -- shutdown best-effort
        logger.debug("admin/shutdown best-effort falhou: %s", _exc)


async def shutdown_repl(
    agent: Any,
    analytics_ref: list,
    project_root: Path,
    logger: Logger,
) -> Any:
    """UX-BUG-03: shutdown ordenado do REPL após o loop.

    1) Wipe da sudo cache (idempotente).
    2) Cancela tasks pendentes (warmup, summarize, etc.) com timeout 2s.
    3) end_session do Analytics se foi criado.
    4) Salva sessão; retorna o Path salvo (ou None).
    """
    try:
        from nyx.agent.tools import sudo_session as _sudo_final
        _sudo_final.wipe()
    except Exception as _exc:  # noqa: BLE001 -- shutdown best-effort
        logger.debug("sudo wipe final falhou: %s", _exc)

    pending = [
        t for t in asyncio.all_tasks()
        if t is not asyncio.current_task() and not t.done()
    ]
    for task in pending:
        task.cancel()
    if pending:
        try:
            await asyncio.wait_for(
                asyncio.gather(*pending, return_exceptions=True),
                timeout=2.0,
            )
        except asyncio.TimeoutError:
            logger.warning("shutdown: %d task(s) ignoraram cancel em 2s", len(pending))

    analytics = analytics_ref[0]
    if analytics is not None:
        try:
            analytics.end_session()
        except Exception as exc:  # noqa: BLE001 -- shutdown best-effort
            logger.warning("Analytics.end_session falhou: %s", exc)

    # TUI-CTRL-Q-OLLAMA-STOP-04: parar TODOS os modelos Ollama rodando no
    # shutdown para liberar VRAM. Decisão de design: TUI Nyx-Code é cliente
    # único do Ollama na máquina-padrão. Best-effort: timeout curto, warning
    # se ollama CLI ausente ou parsing falhar; nunca bloqueia shutdown.
    try:
        import subprocess
        result = subprocess.run(
            ["ollama", "ps"], capture_output=True, text=True, timeout=3,
        )
        lines = result.stdout.splitlines()
        # Primeira linha é header (NAME, ID, SIZE, ...); restante são modelos.
        for line in lines[1:]:
            parts = line.split()
            if not parts:
                continue
            model = parts[0]
            try:
                subprocess.run(
                    ["ollama", "stop", model], timeout=5, check=False,
                )
            except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
                logger.warning("ollama stop %s falhou: %s", model, exc)
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError) as exc:
        logger.warning("ollama ps falhou (modelos não parados): %s", exc)

    from nyx.agent.persistence import save_session as _save_session

    project_name = project_root.name
    saved = _save_session(agent.session, project_name)
    await agent.close()
    return saved


# "Boot is the loneliest moment of any program." -- anônimo
