"""Modo headless do Nyx CLI.

Extraído de nyx/cli.py em INFRA-CLI-SPLIT-03. Protocolo:
  Input  (linha): {"type": "request", "content": "..."}
                  ou /slash command (conveniência para scripts)
  Output (linha): JSON com tipo (response/tool_use/error/pong/status/...).

A função opera apenas com nyx.agent.* + nyx.config.*. Não importa nyx.cli
(evita ciclos) e mantém sandbox singletons globais (módulo base).
"""

from __future__ import annotations

import json as _json
import os
import signal
import sys
from logging import Logger
from pathlib import Path


async def run_headless(project_root: Path, logger: Logger) -> int:
    """Loop principal do modo headless. Retorna exit code.

    Args:
        project_root: raiz do projeto (geralmente PROJECT_ROOT de cli.py).
        logger: logger já configurado pelo caller (get_logger("nyx.cli")).
    """
    from nyx.agent.loop import AgentLoop
    from nyx.agent.persistence import save_session
    from nyx.config.settings import load_settings

    settings = load_settings()
    project_root_str = str(project_root)
    proxy_url = os.environ.get("OPENAI_BASE_URL", settings.proxy_v1_url)
    proxy_url = proxy_url.replace("/v1", "").rstrip("/")
    if not proxy_url.startswith("http"):
        proxy_url = settings.proxy_url
    model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", settings.model))

    # PROJECT-ROOTS-MULTI-01: mesma inicialização do REPL para sandbox.
    try:
        from nyx.agent.tools.base import add_extra_root, set_active_project_root

        set_active_project_root(project_root_str)
        for raw in settings.extra_roots:
            try:
                cand = Path(raw).expanduser()
                if cand.exists() and cand.is_dir():
                    add_extra_root(cand)
            except Exception as _exc:  # noqa: BLE001
                logger.warning("headless extra root %s falhou: %s", raw, _exc)
    except Exception as _exc:  # noqa: BLE001
        logger.warning("headless boot de sandbox roots falhou: %s", _exc)

    # NYX-AUTO-APPROVE-01: em headless via cockpit/CI o prompt CONFIRM_ONCE
    # deadlocka sem TTY. Log de aviso visível em stderr para auditoria.
    if os.environ.get("NYX_AUTO_APPROVE") == "1":
        logger.warning(
            "NYX_AUTO_APPROVE=1 ativo (headless): CONFIRM_ONCE auto-aprovado. "
            "Use somente em automação confiável."
        )

    def on_tool(name: str, args: dict) -> None:
        msg = _json.dumps({"type": "tool_use", "tool": name, "args": args}, ensure_ascii=False)
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()

    agent = AgentLoop(
        project_root=project_root_str,
        proxy_url=proxy_url,
        model=model,
        on_tool=on_tool,
        streaming=False,
        settings=settings,
    )

    shutdown_requested = False

    def _headless_shutdown(signum: int, frame: object) -> None:
        nonlocal shutdown_requested
        if shutdown_requested:
            return
        shutdown_requested = True
        saved = save_session(agent.session, project_root.name)
        msg = _json.dumps(
            {
                "type": "shutdown",
                "session_saved": saved.name if saved else None,
            },
            ensure_ascii=False,
        )
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()

    signal.signal(signal.SIGINT, _headless_shutdown)
    signal.signal(signal.SIGTERM, _headless_shutdown)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        # PROJECT-ROOTS-MULTI-01: aceita slash command direto em headless.
        # Conveniência para scripts/testes (ex.: smoke do spec) que enviam
        # "/sandbox list" sem encapsular em JSON. Resposta sai como linha
        # de output cru (mesma semântica do REPL).
        if line.startswith("/"):
            from nyx.agent.commands import handle_command

            cmd_result = handle_command(line, project_root_str)
            if cmd_result is None:
                continue
            if cmd_result == "__sandbox_list__":
                from nyx.agent.tools.base import (
                    get_active_project_root,
                    list_extra_roots,
                )
                active = get_active_project_root() or project_root
                extras = list_extra_roots()
                lines_out = ["Roots autorizados:", f"  [ativo] {active}"]
                if extras:
                    for r in extras:
                        lines_out.append(f"  [extra] {r}")
                else:
                    lines_out.append(
                        "  (nenhum extra; use /sandbox add <path>)"
                    )
                sys.stdout.write("\n".join(lines_out) + "\n")
                sys.stdout.flush()
                continue
            if isinstance(cmd_result, str) and cmd_result.startswith("__sandbox_add__"):
                from nyx.agent.tools.base import add_extra_root

                raw_path = cmd_result[len("__sandbox_add__"):]
                cand = Path(raw_path).expanduser()
                if not cand.exists() or not cand.is_dir():
                    sys.stdout.write(
                        f"erro: '{raw_path}' não é diretório válido\n"
                    )
                else:
                    added = add_extra_root(cand)
                    sys.stdout.write(f"ok: root autorizado {added}\n")
                sys.stdout.flush()
                continue
            if isinstance(cmd_result, str) and cmd_result.startswith("__sandbox_remove__"):
                from nyx.agent.tools.base import (
                    get_active_project_root,
                    remove_extra_root,
                )
                raw_path = cmd_result[len("__sandbox_remove__"):]
                cand = Path(raw_path).expanduser().resolve()
                active = get_active_project_root() or project_root
                if cand == Path(active).resolve():
                    sys.stdout.write(
                        f"erro: project_root ativo {active} não pode ser removido\n"
                    )
                elif remove_extra_root(cand):
                    sys.stdout.write(f"ok: root removido {cand}\n")
                else:
                    sys.stdout.write(f"erro: root {cand} não estava na lista\n")
                sys.stdout.flush()
                continue
            if isinstance(cmd_result, str) and cmd_result.startswith("__cd__"):
                from nyx.agent.tools.base import (
                    add_extra_root,
                    get_active_project_root,
                    set_active_project_root,
                )
                raw_path = cmd_result[len("__cd__"):]
                cand = Path(raw_path).expanduser()
                if not cand.exists() or not cand.is_dir():
                    sys.stdout.write(f"erro: '{raw_path}' inválido para /cd\n")
                else:
                    old_root = get_active_project_root() or project_root
                    new_root = set_active_project_root(cand)
                    add_extra_root(old_root)
                    project_root_str = str(new_root)
                    # Reconstrói o system prompt junto (TUI-CD-CONTEXT-REBUILD-01):
                    # sem isso o modelo gera caminhos no root antigo.
                    agent.set_project_root(project_root_str)
                    sys.stdout.write(f"ok: project_root agora {new_root}\n")
                sys.stdout.flush()
                continue
            if isinstance(cmd_result, str) and cmd_result.startswith("__error__"):
                payload = cmd_result[len("__error__"):]
                msg_err = payload.split("||")[0]
                sys.stdout.write(f"erro: {msg_err}\n")
                sys.stdout.flush()
                continue
            # Comandos não suportados em headless ainda assim retornam algo.
            sys.stdout.write(str(cmd_result) + "\n")
            sys.stdout.flush()
            continue

        try:
            msg = _json.loads(line)
        except _json.JSONDecodeError:
            err = _json.dumps({"type": "error", "message": "JSON inválido"}, ensure_ascii=False)
            sys.stdout.write(err + "\n")
            sys.stdout.flush()
            continue

        msg_type = msg.get("type", "")
        content = msg.get("content", "")

        if msg_type == "ping":
            resp = _json.dumps({"type": "pong", "tools": agent.tools_count}, ensure_ascii=False)
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
            continue

        if msg_type == "status":
            resp = _json.dumps(
                {
                    "type": "status",
                    "tools": agent.tools_count,
                    "history": len(agent.session.history),
                    "model": model,
                    "files_read": agent.session.files_read_count,
                    "files_modified": agent.session.files_modified_count,
                    "iteration": agent.session.iteration,
                },
                ensure_ascii=False,
            )
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
            continue

        if msg_type == "tools":
            tool_names = [t["function"]["name"] for t in agent._tools.tool_defs]
            resp = _json.dumps(
                {
                    "type": "tools",
                    "list": sorted(tool_names),
                    "count": len(tool_names),
                },
                ensure_ascii=False,
            )
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
            continue

        if msg_type == "session":
            resp = _json.dumps(
                {
                    "type": "session",
                    "files_read": agent.session.files_read_count,
                    "files_modified": agent.session.files_modified_count,
                    "iterations": agent.session.iteration,
                    "history_entries": len(agent.session.history),
                    "context": agent.session.get_files_context(),
                },
                ensure_ascii=False,
            )
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
            continue

        if msg_type == "request" and content:
            try:
                status = await agent.run(content)
                resp = _json.dumps(
                    {
                        "type": "response",
                        "state": status.state.value,
                        "summary": status.summary,
                        "iterations": status.iterations,
                        "files_read": agent.session.files_read_count,
                        "files_modified": agent.session.files_modified_count,
                    },
                    ensure_ascii=False,
                )
            except Exception as e:
                resp = _json.dumps({"type": "error", "message": str(e)}, ensure_ascii=False)
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
            continue

        if msg_type == "reset":
            agent.reset()
            resp = _json.dumps({"type": "ok", "message": "Sessão resetada"}, ensure_ascii=False)
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
            continue

        err = _json.dumps(
            {"type": "error", "message": f"Tipo desconhecido: {msg_type}"},
            ensure_ascii=False,
        )
        sys.stdout.write(err + "\n")
        sys.stdout.flush()

    await agent.close()
    return 0


# "Pipes are simple, pipes are universal." -- Doug McIlroy
