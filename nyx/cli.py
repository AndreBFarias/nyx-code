#!/usr/bin/env python3
"""Nyx CLI -- Code Agent interativo local.

REPL integrado com:
- Rich output (cores Nyx, syntax highlight)
- Streaming (tokens em tempo real)
- Commands (/explain, /plan, /test, /compact, /help, /quit, /clear, /status)
- Permissões (confirmação para run_command/write)
- Persistência (salva sessão ao sair)
- Context bar (uso de budget)

Uso:
    ./run.sh                           # Inicia tudo (Ollama + Proxy + CLI)
    ./run.sh --no-stream               # Sem streaming
    ./venv/bin/python nyx/cli.py       # Se Ollama + Proxy já estão rodando
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import signal
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from nyx.agent.services.logging_service import InternalLogging

InternalLogging()
logger = logging.getLogger("nyx.cli")

from nyx.__version__ import __version__ as NYX_VERSION

# ── Cores Nyx (fallback ANSI) ─────────────────────────────────────

ACCENT = "\033[38;2;0;212;170m"
PRIMARY = "\033[38;2;232;232;232m"
DIM = "\033[2m"
BOLD = "\033[1m"
NC = "\033[0m"


def _build_banner(model: str, tools_count: int, project: str) -> str:
    title = f"Nyx -- Code Agent Local v{NYX_VERSION}"
    tools_info = f"{tools_count}        100% offline"
    lines = [
        "",
        f"  {ACCENT}{BOLD}╭──────────────────────────────────────────╮{NC}",
        f"  {ACCENT}{BOLD}│{NC}  {BOLD}{title:<40s}{NC}{ACCENT}{BOLD}│{NC}",
        f"  {ACCENT}{BOLD}│{NC}  modelo   {model:<31s}{ACCENT}{BOLD}│{NC}",
        f"  {ACCENT}{BOLD}│{NC}  projeto  {project:<31s}{ACCENT}{BOLD}│{NC}",
        f"  {ACCENT}{BOLD}│{NC}  tools    {tools_info:<31s}{ACCENT}{BOLD}│{NC}",
        f"  {ACCENT}{BOLD}╰──────────────────────────────────────────╯{NC}",
        "",
        f"  {DIM}/help para comandos. Ctrl+D para sair.{NC}",
        "",
    ]
    return "\n".join(lines)


def _ask_permission(level: str, tool_name: str, args: dict) -> bool:
    """Pede confirmação ao usuário para execução de tool."""
    args_preview = str(args)[:80]
    level_label = {"confirm_once": "uma vez", "always_confirm": "sempre"}.get(level, level)
    try:
        resp = input(
            f"  {ACCENT}[permissão: {level_label}]{NC} Executar {BOLD}{tool_name}{NC}({args_preview})? [S/n] "
        ).strip().lower()
        return resp in ("", "s", "sim", "y", "yes")
    except (EOFError, KeyboardInterrupt):
        return False


async def run_repl(streaming: bool = True) -> int:
    from nyx.agent.commands import handle_command
    from nyx.agent.context import render_context_bar
    from nyx.agent.loop import AgentLoop
    from nyx.agent.persistence import cleanup_old_sessions, save_session
    from nyx.agent.services.analytics import Analytics

    cleanup_old_sessions()
    analytics = Analytics()

    try:
        from nyx.agent.output import RichOutput
        output = RichOutput()
        use_rich = output.available
    except ImportError:
        output = None
        use_rich = False

    project_root = str(PROJECT_ROOT)

    prompt_session = None
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.formatted_text import ANSI
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.shortcuts import CompleteStyle
        from nyx.agent.completer import create_completer

        history_path = Path.home() / ".nyx" / "history"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        completer = create_completer(project_root)

        kb = KeyBindings()

        @kb.add("enter")
        def _submit(event: object) -> None:
            event.current_buffer.validate_and_handle()  # type: ignore[attr-defined]

        @kb.add("c-j")
        def _newline(event: object) -> None:
            event.current_buffer.insert_text("\n")  # type: ignore[attr-defined]

        prompt_session = PromptSession(
            history=FileHistory(str(history_path)),
            completer=completer,
            multiline=True,
            key_bindings=kb,
            complete_while_typing=True,
            complete_style=CompleteStyle.MULTI_COLUMN,
        )
        logger.info("prompt-toolkit ativo (histórico: %s)", history_path)
    except ImportError:
        logger.info("prompt-toolkit indisponível, usando input() nativo")
    proxy_url = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:11436/v1")
    proxy_url = proxy_url.replace("/v1", "").rstrip("/")
    if not proxy_url.startswith("http"):
        proxy_url = "http://127.0.0.1:11436"
    model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", "qwen3:4b"))

    from nyx.agent.output import (
        render_tool_call,
        render_tool_result,
        render_user_input,
        render_assistant_start,
        render_assistant_end,
        nyx_spinner,
    )

    spinner_state: dict[str, object | None] = {"active": None}

    def _stop_spinner() -> None:
        sp = spinner_state.get("active")
        if sp is not None:
            sp.stop()  # type: ignore[union-attr]
            spinner_state["active"] = None

    def on_token(token: str) -> None:
        _stop_spinner()
        sys.stdout.write(token)
        sys.stdout.flush()

    def on_tool(name: str, args: dict) -> None:
        _stop_spinner()
        render_tool_call(name, args, project_root=project_root)

    def on_tool_result(name: str, result: str) -> None:
        render_tool_result(result)

    agent = AgentLoop(
        project_root=project_root,
        proxy_url=proxy_url,
        model=model,
        on_token=on_token if streaming else None,
        on_tool=on_tool,
        on_tool_result=on_tool_result,
        on_permission=_ask_permission,
        streaming=streaming,
    )

    print(_build_banner(model, agent.tools_count, PROJECT_ROOT.name))

    session_start = time.time()
    total_iterations = 0

    from nyx.agent.output import render_footer

    while True:
        try:
            ctx_info = agent.get_context_info()
            render_footer(
                pct=int(ctx_info.get("pct", 0) * 100),
                model=model,
                iteration=agent.session.iteration,
                reads=agent.session.files_read_count,
                mods=agent.session.files_modified_count,
            )
            prompt_str = f"{ACCENT}{BOLD}nyx>{NC} "
            if prompt_session:
                user_input = (await prompt_session.prompt_async(ANSI(prompt_str))).strip()
            else:
                user_input = input(prompt_str).strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue

        if not user_input:
            continue

        if not user_input.startswith("/"):
            render_user_input(user_input)

        if user_input.startswith("/"):
            result = handle_command(user_input, project_root)
            if result is None:
                continue

            if result == "__quit__":
                break

            if result == "__clear__":
                agent.reset()
                if use_rich and output:
                    output("ok", "Sessão limpa.")
                else:
                    print(f"  {DIM}Sessão limpa.{NC}")
                continue

            if result == "__status__":
                s = agent.session
                stats = agent.parser_stats
                ctx = agent.get_context_info()
                status_msg = (
                    f"Iterações: {s.iteration} | "
                    f"Lidos: {s.files_read_count} | "
                    f"Modificados: {s.files_modified_count} | "
                    f"Parser: {stats['success_rate']:.0%} | "
                    f"Tools: {agent.tools_count} | "
                    f"Contexto: {ctx.get('pct', 0):.0%}"
                )
                if use_rich and output:
                    output("sessao", status_msg)
                else:
                    print(f"  {ACCENT}[sessão]{NC} {status_msg}")
                continue

            if result == "__context__":
                ctx = agent.get_context_info()
                bar = render_context_bar(ctx)
                ctx_msg = (
                    f"{bar}\n"
                    f"  System: {ctx.get('system_tokens', 0)} tok | "
                    f"User: {ctx.get('user_tokens', 0)} tok | "
                    f"Total: {ctx.get('total_tokens', 0)}/{ctx.get('max_tokens', 0)} tok"
                )
                print(f"  {ctx_msg}")
                continue

            if result == "__session_save__":
                saved = save_session(agent.session, PROJECT_ROOT.name)
                if saved:
                    print(f"  {ACCENT}[ok]{NC} Sessão salva: {saved.name}")
                else:
                    print(f"  {DIM}Falha ao salvar sessão.{NC}")
                continue

            if result == "__session_load__":
                from nyx.agent.persistence import load_latest_session
                loaded = load_latest_session(PROJECT_ROOT.name)
                if loaded:
                    agent._session = loaded
                    print(f"  {ACCENT}[ok]{NC} Sessão restaurada ({len(loaded.history)} entradas)")
                else:
                    print(f"  {DIM}Nenhuma sessão para restaurar.{NC}")
                continue

            if isinstance(result, str) and result.startswith("__model__"):
                new_model = result.replace("__model__", "")
                agent._model = new_model
                print(f"  {ACCENT}[ok]{NC} Modelo trocado para: {new_model}")
                continue

            if isinstance(result, str) and result.startswith("__rewind__"):
                n = int(result.replace("__rewind__", "") or "1")
                removed = min(n, len(agent.session.history))
                for _ in range(removed):
                    if agent.session.history:
                        agent.session.history.pop()
                print(f"  {ACCENT}[ok]{NC} Desfeitas {removed} entradas do histórico.")
                continue

            if result == "__stats__":
                s = agent.session
                stats = agent.parser_stats
                status_msg = (
                    f"  Iterações: {s.iteration}\n"
                    f"  Arquivos lidos: {s.files_read_count}\n"
                    f"  Arquivos modificados: {s.files_modified_count}\n"
                    f"  Entradas no histórico: {len(s.history)}\n"
                    f"  Parser taxa sucesso: {stats['success_rate']:.0%}\n"
                    f"  Tools: {agent.tools_count}"
                )
                print(status_msg)
                continue

            if result == "__usage__":
                ctx = agent.get_context_info()
                usage_msg = (
                    f"  Contexto: {ctx.get('pct', 0):.0%} usado\n"
                    f"  Tokens sistema: {ctx.get('system_tokens', 0)}\n"
                    f"  Tokens usuário: {ctx.get('user_tokens', 0)}\n"
                    f"  Total: {ctx.get('total_tokens', 0)}/{ctx.get('max_tokens', 0)}"
                )
                print(usage_msg)
                continue

            if result == "__files__":
                ctx = agent.session.get_files_context()
                print(f"  {ctx}" if ctx else "  Nenhum arquivo no contexto.")
                continue

            if result == "__trace__":
                entries = [e for e in agent.session.history if e.tool_name]
                if not entries:
                    print(f"  {DIM}Nenhuma tool call na sessão.{NC}")
                else:
                    print(f"  Últimas tool calls:")
                    for e in entries[-10:]:
                        args_short = str(e.tool_args)[:50]
                        print(f"    {ACCENT}{e.tool_name}{NC}({args_short})")
                continue

            if isinstance(result, str) and result.startswith("__btw__"):
                note = result[7:]
                agent.session.add_user(f"[nota lateral] {note}")
                print(f"  {DIM}Nota registrada: {note[:60]}{NC}")
                continue

            if isinstance(result, str) and result.startswith("__export__"):
                fmt = result.replace("__export__", "") or "md"
                from nyx.agent.persistence import SESSIONS_DIR
                export_dir = Path.home() / ".nyx" / "exports"
                export_dir.mkdir(parents=True, exist_ok=True)
                ts = time.strftime("%Y%m%d_%H%M%S")
                export_path = export_dir / f"session_{ts}.{fmt}"
                lines = []
                for entry in agent.session.history:
                    if entry.tool_name:
                        lines.append(f"[{entry.tool_name}] {str(entry.tool_args)[:80]}")
                    else:
                        lines.append(f"[{entry.role}] {entry.content[:200]}")
                export_path.write_text("\n".join(lines), encoding="utf-8")
                print(f"  {ACCENT}[ok]{NC} Sessão exportada: {export_path}")
                continue

            if result == "__copy__":
                import subprocess as _sp
                last_content = ""
                for entry in reversed(agent.session.history):
                    if entry.role == "assistant" or entry.tool_result:
                        last_content = entry.content or entry.tool_result
                        break
                if last_content:
                    try:
                        _sp.run(["xclip", "-selection", "clipboard"],
                                input=last_content.encode(), timeout=5)
                        print(f"  {ACCENT}[ok]{NC} Copiado para clipboard ({len(last_content)} chars)")
                    except FileNotFoundError:
                        tmp = Path.home() / ".nyx" / "clipboard.txt"
                        tmp.write_text(last_content, encoding="utf-8")
                        print(f"  {DIM}xclip indisponível. Salvo em {tmp}{NC}")
                else:
                    print(f"  {DIM}Nenhum output para copiar.{NC}")
                continue

            if result.startswith("  Comando desconhecido"):
                print(result)
                continue

            if "read_file" in result or "list_files" in result or "done(" in result:
                user_input = result
            else:
                if use_rich and output:
                    output("nyx", result)
                else:
                    print(result)
                continue

        try:
            spinner = nyx_spinner("pensando...")
            spinner.__enter__()
            spinner_state["active"] = spinner
            render_assistant_start()
            try:
                status = await agent.run(user_input)
            finally:
                _stop_spinner()
            total_iterations += status.iterations

            if status.summary:
                if use_rich and output:
                    output("nyx", status.summary)
                else:
                    print(f"\n{PRIMARY}{status.summary}{NC}\n")

            state_label = status.state.value
            if status.state != status.state.DONE:
                print(f"  {DIM}[{state_label}]{NC}")

            render_assistant_end()

        except KeyboardInterrupt:
            _stop_spinner()
            print(f"\n  {ACCENT}[cancelado]{NC}")

    elapsed = time.time() - session_start

    session_summary = (
        f"Iterações: {total_iterations} | "
        f"Lidos: {agent.session.files_read_count} | "
        f"Modificados: {agent.session.files_modified_count} | "
        f"Tempo: {elapsed:.1f}s"
    )
    if use_rich and output:
        output("sessao", session_summary)
    else:
        print(f"\n  {ACCENT}[sessão]{NC} {session_summary}\n")

    analytics.end_session()

    project_name = PROJECT_ROOT.name
    saved = save_session(agent.session, project_name)
    if saved:
        print(f"  {DIM}Sessão salva: {saved.name}{NC}")

    await agent.close()
    return 0


async def run_headless() -> int:
    """Modo headless: lê JSON de stdin, responde JSON em stdout.

    Protocolo:
      Input:  {"type": "request", "content": "..."}
      Output: {"type": "response", "state": "done", "summary": "...", "iterations": N}
      Output: {"type": "tool_use", "tool": "...", "args": {...}}
      Output: {"type": "error", "message": "..."}
    """
    import json as _json

    from nyx.agent.loop import AgentLoop
    from nyx.agent.persistence import save_session

    project_root = str(PROJECT_ROOT)
    proxy_url = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:11436/v1")
    proxy_url = proxy_url.replace("/v1", "").rstrip("/")
    if not proxy_url.startswith("http"):
        proxy_url = "http://127.0.0.1:11436"
    model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", "qwen3:4b"))

    def on_tool(name: str, args: dict) -> None:
        msg = _json.dumps({"type": "tool_use", "tool": name, "args": args}, ensure_ascii=False)
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()

    agent = AgentLoop(
        project_root=project_root,
        proxy_url=proxy_url,
        model=model,
        on_tool=on_tool,
        streaming=False,
    )

    shutdown_requested = False

    def _headless_shutdown(signum: int, frame: object) -> None:
        nonlocal shutdown_requested
        if shutdown_requested:
            return
        shutdown_requested = True
        saved = save_session(agent.session, PROJECT_ROOT.name)
        msg = _json.dumps({
            "type": "shutdown",
            "session_saved": saved.name if saved else None,
        }, ensure_ascii=False)
        sys.stdout.write(msg + "\n")
        sys.stdout.flush()

    signal.signal(signal.SIGINT, _headless_shutdown)
    signal.signal(signal.SIGTERM, _headless_shutdown)

    for line in sys.stdin:
        line = line.strip()
        if not line:
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
            resp = _json.dumps({
                "type": "status",
                "tools": agent.tools_count,
                "history": len(agent.session.history),
                "model": model,
                "files_read": agent.session.files_read_count,
                "files_modified": agent.session.files_modified_count,
                "iteration": agent.session.iteration,
            }, ensure_ascii=False)
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
            continue

        if msg_type == "tools":
            tool_names = [t["function"]["name"] for t in agent._tools.tool_defs]
            resp = _json.dumps({
                "type": "tools",
                "list": sorted(tool_names),
                "count": len(tool_names),
            }, ensure_ascii=False)
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
            continue

        if msg_type == "session":
            resp = _json.dumps({
                "type": "session",
                "files_read": agent.session.files_read_count,
                "files_modified": agent.session.files_modified_count,
                "iterations": agent.session.iteration,
                "history_entries": len(agent.session.history),
                "context": agent.session.get_files_context(),
            }, ensure_ascii=False)
            sys.stdout.write(resp + "\n")
            sys.stdout.flush()
            continue

        if msg_type == "request" and content:
            try:
                status = await agent.run(content)
                resp = _json.dumps({
                    "type": "response",
                    "state": status.state.value,
                    "summary": status.summary,
                    "iterations": status.iterations,
                    "files_read": agent.session.files_read_count,
                    "files_modified": agent.session.files_modified_count,
                }, ensure_ascii=False)
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


def main() -> None:
    signal.signal(signal.SIGINT, lambda *_: None)

    parser = argparse.ArgumentParser(description="Nyx CLI -- Code Agent local")
    parser.add_argument("--no-stream", action="store_true", help="Desativa streaming de tokens")
    parser.add_argument("--headless", action="store_true", help="Modo headless: stdin/stdout JSON")
    args = parser.parse_args()

    if args.headless:
        sys.exit(asyncio.run(run_headless()))
    else:
        sys.exit(asyncio.run(run_repl(streaming=not args.no_stream)))


if __name__ == "__main__":
    main()


# "O terminal é o lar do programador." -- Ken Thompson
