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
import os
import signal
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

# Permitir execução como script direto (python nyx/cli.py) além de -m nyx.cli.
# Sem isso, só o diretório nyx/ entra no sys.path e `import nyx.*` falha.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nyx.agent.services.logging_service import (  # noqa: E402
    InternalLogging,
    get_logger,
)

if TYPE_CHECKING:
    pass

InternalLogging()
logger = get_logger("nyx.cli")


# ── Cores e glifos Nyx (design_tokens é fonte única, ADR-023) ─────
from nyx.themes.design_tokens import (  # noqa: E402
    ANSI_ACCENT_FG,
    ANSI_BOLD,
    ANSI_DIM,
    ANSI_PRIMARY_FG,
    ANSI_RESET,
    BULLETS,
    NYX_ACCENT,
    NYX_MUTED,
    NYX_PRIMARY,
    NYX_PURPLE_DIM,
)

ACCENT = ANSI_ACCENT_FG
PRIMARY = ANSI_PRIMARY_FG
DIM = ANSI_DIM
BOLD = ANSI_BOLD
NC = ANSI_RESET


from nyx.agent.banner import build_banner as _build_banner  # noqa: E402
from nyx.agent.output import make_ask_permission as _make_ask_permission  # noqa: E402


async def run_repl(streaming: bool = True) -> int:
    from nyx.agent.commands import handle_command
    from nyx.agent.context import render_context_bar
    from nyx.agent.loop import AgentLoop
    from nyx.agent.persistence import cleanup_old_sessions, save_session
    from nyx.agent.services.analytics import Analytics
    from nyx.config.settings import load_settings

    settings = load_settings()

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
        from prompt_toolkit.formatted_text import ANSI
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.shortcuts import CompleteStyle

        from nyx.agent.completer import create_completer

        history_path = Path.home() / ".nyx" / "history"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        completer = create_completer(project_root)

        kb = KeyBindings()

        @kb.add("enter")
        def _submit(event: object) -> None:
            buf = event.current_buffer  # type: ignore[attr-defined]
            state = buf.complete_state
            if (
                state
                and state.completions
                and buf.document.text_before_cursor.lstrip().startswith("/")
            ):
                buf.apply_completion(state.current_completion or state.completions[0])
            buf.validate_and_handle()

        @kb.add("c-j")
        def _newline(event: object) -> None:
            event.current_buffer.insert_text("\n")  # type: ignore[attr-defined]

        @kb.add("/")
        def _slash(event: object) -> None:
            buf = event.current_buffer  # type: ignore[attr-defined]
            buf.insert_text("/")
            if buf.document.text_before_cursor.lstrip() == "/":
                buf.start_completion(select_first=False)

        @kb.add("s-tab")
        def _toggle_bypass(event: object) -> None:
            app_state["bypass"] = not app_state["bypass"]
            event.app.invalidate()  # type: ignore[attr-defined]

        @kb.add("c-v")
        def _paste(event: object) -> None:
            from prompt_toolkit.application import run_in_terminal

            from nyx.agent.clipboard import capture_image, capture_text

            buf = event.current_buffer  # type: ignore[attr-defined]
            img_path = capture_image()
            if img_path is not None:
                image_counter["n"] += 1
                n = image_counter["n"]
                image_map[n] = str(img_path)
                buf.insert_text(f"[Image #{n}]")
                run_in_terminal(lambda: print(f"  {DIM}⇲ Image #{n} salva em {img_path}{NC}"))
                return
            text = capture_text()
            if text:
                buf.insert_text(text)

        def _bottom_toolbar() -> list:
            """Toolbar inferior do PromptSession.

            Schema de secções (separadas por ' · '):
              [ctx]                     -- ctx X% (Ntok/Mtok) ou ctx X%
              [modelo · iter · lidos · modif]
              [bypass]                  -- ON: fundo roxo; OFF: dica muted
              [<extensões futuras>]     -- UX-BUG-02B adicionará warm/cold aqui

            Contrato: cada secção é um FormattedText fragment. Extensões
            anexam seus fragments ao final de `parts`, sem sobrescrever.
            """
            from prompt_toolkit.formatted_text import FormattedText

            parts: list[tuple[str, str]] = []
            ctx_pct = app_state.get("ctx_pct", 0)
            total_tok = app_state.get("total_tokens", 0)
            max_tok = app_state.get("max_tokens", 0)
            iter_n = app_state.get("iter_n", 0)
            reads = app_state.get("reads", 0)
            mods = app_state.get("mods", 0)

            ctx_label = f"ctx {ctx_pct}%"
            if max_tok:
                ctx_label += f" ({total_tok}/{max_tok}tok)"
            parts.append((f"fg:{NYX_ACCENT}", ctx_label))

            meta = f" · {model} · iter {iter_n} · lidos {reads} · modif {mods}"
            parts.append((f"fg:{NYX_MUTED}", meta))

            if app_state.get("bypass"):
                parts.append(("", "  "))
                parts.append((
                    f"bg:{NYX_PURPLE_DIM} fg:{NYX_PRIMARY} bold",
                    f" {BULLETS['bypass_on']} bypass ON ",
                ))
            else:
                parts.append((f"fg:{NYX_MUTED}", f"   {BULLETS['bypass_off']} shift+tab: bypass"))
            return FormattedText(parts)

        import shutil as _sh

        _term_cols = _sh.get_terminal_size(fallback=(80, 24)).columns
        _style = CompleteStyle.COLUMN

        prompt_session = PromptSession(
            history=FileHistory(str(history_path)),
            completer=completer,
            multiline=True,
            key_bindings=kb,
            complete_while_typing=True,
            complete_style=_style,
            bottom_toolbar=_bottom_toolbar,
        )
        logger.info("prompt-toolkit ativo (histórico: %s)", history_path)
    except ImportError:
        logger.info("prompt-toolkit indisponível, usando input() nativo")
    proxy_url = os.environ.get("OPENAI_BASE_URL", settings.proxy_v1_url)
    proxy_url = proxy_url.replace("/v1", "").rstrip("/")
    if not proxy_url.startswith("http"):
        proxy_url = settings.proxy_url
    model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", settings.model))

    from nyx.agent.output import (
        format_args_preview,
        is_tool_error,
        nyx_spinner,
        render_assistant_end,
        render_assistant_start,
        render_compaction_event,
        render_tool_card_end,
        render_tool_card_start,
        render_user_input,
    )

    spinner_state: dict[str, object | None] = {"active": None}
    turn_state: dict[str, str] = {"streamed_text": ""}
    app_state: dict[str, bool] = {"bypass": False}
    image_counter: dict[str, int] = {"n": 0}
    image_map: dict[int, str] = {}
    tool_timers: dict[str, float] = {}

    def _stop_spinner() -> None:
        sp = spinner_state.get("active")
        if sp is not None:
            sp.stop()  # type: ignore[union-attr]
            spinner_state["active"] = None

    def on_token(token: str) -> None:
        _stop_spinner()
        turn_state["streamed_text"] += token
        sys.stdout.write(token)
        sys.stdout.flush()

    def on_tool(name: str, args: dict) -> None:
        _stop_spinner()
        turn_state["streamed_text"] = ""
        tool_timers[name] = time.monotonic()
        render_tool_card_start(name, format_args_preview(args))

    def on_tool_result(name: str, result: str) -> None:
        if name == "ask_user":
            import json as _json

            try:
                payload = _json.loads(result) if isinstance(result, str) and result.startswith("{") else {}
            except _json.JSONDecodeError:
                payload = {}
            if payload.get("kind") == "question":
                from nyx.agent.output import render_ask_user

                render_ask_user(payload.get("question", ""), payload.get("options", []))
                try:
                    answer = input("  Resposta: ").strip()
                except (EOFError, KeyboardInterrupt):
                    answer = ""
                if answer:
                    idx_opts = payload.get("options", []) or []
                    if answer.isdigit():
                        idx = int(answer) - 1
                        if 0 <= idx < len(idx_opts):
                            answer = idx_opts[idx].get("label", answer)
                    agent.session.add_user(f"[resposta] {answer}")
                return
        started = tool_timers.pop(name, None)
        duration_ms = int((time.monotonic() - started) * 1000) if started else 0
        first_line = next((ln.strip() for ln in (result or "").splitlines() if ln.strip()), "")
        render_tool_card_end(
            name,
            duration_ms=duration_ms,
            summary_line=first_line,
            is_error=is_tool_error(first_line),
        )

    def on_compaction(level: int, tokens_removed: int, pct_before: float, pct_after: float) -> None:
        render_compaction_event(level, tokens_removed, pct_before, pct_after)

    from nyx.agent.commands._observability import on_model_state_log

    agent = AgentLoop(
        project_root=project_root,
        proxy_url=proxy_url,
        model=model,
        on_token=on_token if streaming else None,
        on_tool=on_tool,
        on_tool_result=on_tool_result,
        on_permission=_make_ask_permission(app_state),
        on_compaction=on_compaction,
        on_model_state=on_model_state_log,
        streaming=streaming,
        settings=settings,
    )

    print(_build_banner(model, agent.tools_count, PROJECT_ROOT.name, settings=settings))

    memory_entries = agent._memory.index() if hasattr(agent, "_memory") else []
    if memory_entries:
        names = ", ".join(e["file"] for e in memory_entries[:3])
        suffix = f" (+{len(memory_entries) - 3})" if len(memory_entries) > 3 else ""
        print(f"  {DIM}[memória: {len(memory_entries)} entradas] {names}{suffix}{NC}")

    session_start = time.time()
    total_iterations = 0

    while True:
        try:
            ctx_info = agent.get_context_info()
            app_state["ctx_pct"] = int(ctx_info.get("pct", 0) * 100)
            app_state["total_tokens"] = ctx_info.get("total_tokens", 0)
            app_state["max_tokens"] = ctx_info.get("max_tokens", 0)
            app_state["iter_n"] = agent.session.iteration
            app_state["reads"] = agent.session.files_read_count
            app_state["mods"] = agent.session.files_modified_count
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

            if result == "__debug_session__":
                from nyx.agent.commands._observability import render_debug_session
                print(render_debug_session(agent))
                continue
            if isinstance(result, str) and result.startswith("__replay__"):
                from nyx.agent.commands._observability import render_replay
                print(render_replay(Path(project_root), result.replace("__replay__", "")))
                continue

            if result == "__trace__":
                entries = [e for e in agent.session.history if e.tool_name]
                if not entries:
                    print(f"  {DIM}Nenhuma tool call na sessão.{NC}")
                else:
                    print("  Últimas tool calls:")
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
                        _sp.run(["xclip", "-selection", "clipboard"], input=last_content.encode(), timeout=5)
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
            turn_state["streamed_text"] = ""
            spinner = nyx_spinner("pensando...")
            spinner.__enter__()
            spinner_state["active"] = spinner
            render_assistant_start()
            try:
                status = await agent.run(user_input)
            finally:
                _stop_spinner()
            total_iterations += status.iterations

            streamed = turn_state["streamed_text"].strip()
            summary = (status.summary or "").strip()
            already_shown = bool(streamed) and bool(summary) and (streamed == summary or streamed.endswith(summary))
            if summary and not already_shown:
                if use_rich and output:
                    output("nyx", status.summary)
                else:
                    print(f"\n{PRIMARY}{status.summary}{NC}\n")
            elif streamed:
                print()

            state_label = status.state.value
            if status.state != status.state.DONE:
                print(f"  {DIM}[{state_label}]{NC}")

            render_assistant_end()

            try:
                asyncio.create_task(agent.maybe_summarize())
            except RuntimeError as exc:
                logger.warning("sumarização adiada (loop indisponível): %s", exc)

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
    from nyx.config.settings import load_settings

    settings = load_settings()
    project_root = str(PROJECT_ROOT)
    proxy_url = os.environ.get("OPENAI_BASE_URL", settings.proxy_v1_url)
    proxy_url = proxy_url.replace("/v1", "").rstrip("/")
    if not proxy_url.startswith("http"):
        proxy_url = settings.proxy_url
    model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", settings.model))

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
        settings=settings,
    )

    shutdown_requested = False

    def _headless_shutdown(signum: int, frame: object) -> None:
        nonlocal shutdown_requested
        if shutdown_requested:
            return
        shutdown_requested = True
        saved = save_session(agent.session, PROJECT_ROOT.name)
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


def main() -> None:
    signal.signal(signal.SIGINT, lambda *_: None)

    parser = argparse.ArgumentParser(description="Nyx CLI -- Code Agent local")
    parser.add_argument("--no-stream", action="store_true", help="Desativa streaming de tokens")
    parser.add_argument("--headless", action="store_true", help="Modo headless: stdin/stdout JSON")
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Prova que imports resolvem (imprime 'boot ok' e sai).",
    )
    args = parser.parse_args()

    if args.smoke:
        print("boot ok")
        sys.exit(0)

    if args.headless:
        sys.exit(asyncio.run(run_headless()))
    else:
        sys.exit(asyncio.run(run_repl(streaming=not args.no_stream)))


if __name__ == "__main__":
    main()


# "O terminal é o lar do programador." -- Ken Thompson
