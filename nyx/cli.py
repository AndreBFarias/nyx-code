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
    ANSI_SUCCESS_FG,
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
SUCCESS = ANSI_SUCCESS_FG
NC = ANSI_RESET


# Glifos do estado do modelo (UX-BUG-02B).
# Círculos da faixa Geometric Shapes (U+25CB/D0/CF) — não são emoji.
# NÃO remover via sanitizer global: invariante #14 (sprint_invariants.sh) protege estes 3 caracteres.
_STATE_GLYPHS = {"cold": "", "warming": "", "warm": ""}


from nyx.agent.banner import build_banner as _build_banner  # noqa: E402
from nyx.agent.output import make_ask_permission as _make_ask_permission  # noqa: E402
from nyx.agent.output import print_error as _print_error  # noqa: E402


# INFRA-CLI-SPLIT-01: helpers movidos para nyx/cli_helpers.py (mantemos re-export).
from nyx.cli_helpers import (  # noqa: E402
    _IMAGE_INDEX_PATH,
    _expand_images,
    _persist_image_index,
    _shorten_description,
)
from nyx.cli_helpers import maybe_offer_resume as _maybe_offer_resume_impl  # noqa: E402

if TYPE_CHECKING:
    from nyx.agent.services.vision_service import VisionService


def maybe_offer_resume(agent: object, project_name: str = "") -> None:
    """Wrapper que injeta cores ANSI (cli.py é dono dos defines visuais)."""
    _maybe_offer_resume_impl(agent, project_name, ansi_accent=ACCENT, ansi_reset=NC)


async def run_repl(
    streaming: bool = True,
    resume_id: str | None = None,
    no_resume_prompt: bool = False,
) -> int:
    from nyx.agent.commands import handle_command
    from nyx.agent.context import render_context_bar
    from nyx.agent.loop import AgentLoop
    from nyx.agent.persistence import save_session
    from nyx.config.settings import load_settings

    settings = load_settings()

    # UX-BUG-03: Analytics() sai do caminho síncrono pré-banner. Mantemos
    # referência mutável (analytics_ref[0]) para que o shutdown leia mesmo
    # se a task de warm-up não tiver completado — neste caso end_session
    # é best-effort: o _session_start já estará registrado quando a task
    # criar o Analytics; se ainda não criou, o shutdown ignora.
    analytics_ref: list[object | None] = [None]

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
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.formatted_text import ANSI
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.key_binding import KeyBindings
        from prompt_toolkit.shortcuts import CompleteStyle

        from nyx.agent.completer import create_completer

        history_path = Path.home() / ".nyx" / "history"
        history_path.parent.mkdir(parents=True, exist_ok=True)
        completer = create_completer(project_root)

        kb = KeyBindings()
        last_input_state: dict[str, str] = {"text": ""}

        @kb.add("c-o")
        def _expand_last_input(event: object) -> None:
            from prompt_toolkit.application import run_in_terminal

            from nyx.agent.output import render_user_input as _render_expanded

            text = last_input_state.get("text", "")
            if text:
                run_in_terminal(lambda: _render_expanded(text, expanded=True))

        @kb.add("c-up")
        def _recall_last_input(event: object) -> None:
            """UX-EXTRA-01: Ctrl+Up carrega último input no buffer (editável)."""
            buf = event.current_buffer  # type: ignore[attr-defined]
            last = last_input_state.get("text", "")
            if not last:
                from prompt_toolkit.application import run_in_terminal

                run_in_terminal(lambda: print(f"  {DIM}Nenhum input anterior{NC}"))
                return
            if buf.document.text.strip():
                return
            buf.text = last
            buf.cursor_position = len(last)

        @kb.add("enter")
        def _submit(event: object) -> None:
            buf = event.current_buffer  # type: ignore[attr-defined]
            state = buf.complete_state
            if (
                state
                and state.completions
                and buf.document.text_before_cursor.lstrip().startswith("/")
            ):
                current = state.current_completion or state.completions[0]
                # Pula cabeçalhos de categoria (text=""): busca próximo Completion real.
                # Se só houver cabeçalhos (impossível por construção do completer),
                # fallback para o primeiro Completion disponível.
                if not current.text:
                    current = next(
                        (c for c in state.completions if c.text),
                        state.completions[0],
                    )
                buf.apply_completion(current)
            buf.validate_and_handle()

        @kb.add("c-j")
        def _newline(event: object) -> None:
            event.current_buffer.insert_text("\n")  # type: ignore[attr-defined]

        @kb.add("/")
        def _slash(event: object) -> None:
            buf = event.current_buffer  # type: ignore[attr-defined]
            buf.insert_text("/")
            if buf.document.text_before_cursor.lstrip() == "/":
                buf.start_completion(select_first=True)

        @kb.add("tab")
        def _accept_suggestion(event: object) -> None:
            buf = event.current_buffer  # type: ignore[attr-defined]
            sug = buf.suggestion
            if sug and sug.text:
                buf.insert_text(sug.text)
                return
            if buf.complete_state:
                buf.complete_next()
            else:
                buf.insert_text("    ")

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
                _persist_image_index(image_map)
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
              [model_state]             --  cold |  warming |  warm (UX-BUG-02B)
              [bypass]                  -- ON: fundo roxo; OFF: dica muted

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

            # UX-CLAUDE-PARITY-01 (ADR-029): pipes ' | ' como separator
            # estrutural (paridade com CLI de referencia), preservando paleta e glifos.
            meta = f"  |  {model}  |  iter {iter_n}  |  lidos {reads}  |  modif {mods}"
            parts.append((f"fg:{NYX_MUTED}", meta))

            model_state = app_state.get("model_state", "cold")
            glyph = _STATE_GLYPHS.get(model_state, _STATE_GLYPHS["cold"])
            parts.append((f"fg:{NYX_MUTED}", f"  |  {glyph} {model_state}"))

            # UX-AGENCY-02: indicador de tool em curso (footer dinâmico)
            inflight = app_state.get("inflight_task")
            if inflight is not None and not inflight.done():
                parts.append((f"fg:{NYX_ACCENT}", "  |   executando (Ctrl+C cancela)"))

            if app_state.get("bypass"):
                parts.append(("", "  "))
                parts.append((
                    f"bg:{NYX_PURPLE_DIM} fg:{NYX_PRIMARY} bold",
                    f" {BULLETS['bypass_on']} bypass ON (shift+tab) ",
                ))
            else:
                parts.append((f"fg:{NYX_MUTED}", "    shift+tab: bypass"))
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
            auto_suggest=AutoSuggestFromHistory(),
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
        build_warming_label,
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
    turn_state: dict[str, str] = {"streamed_text": "", "token_buffer": ""}
    # app_state: bool para flags, str para estados ("model_state": cold/warming/warm — UX-BUG-02B).
    app_state: dict[str, object] = {"bypass": False, "model_state": "cold"}
    # TUI-REDESIGN-25-04: nome do usuário via git config (silent, fallback "visitante").
    from nyx.agent.onboarding import resolve_user_display_name
    app_state["user_display_name"] = resolve_user_display_name()
    # TUI-REDESIGN-25-14: marca início da sessão para card de stats no /quit.
    app_state["session_started_monotonic"] = time.monotonic()
    image_counter: dict[str, int] = {"n": 0}
    image_map: dict[int, str] = {}
    tool_timers: dict[str, float] = {}
    # STREAMING-SIDE-RULE-01: estado da faixa lateral entre flushes.
    side_rule_state: dict = {}

    TOKEN_FLUSH_CHARS = 32

    def _stop_spinner() -> None:
        sp = spinner_state.get("active")
        if sp is not None:
            sp.stop()  # type: ignore[union-attr]
            spinner_state["active"] = None

    def _flush_buffer() -> None:
        buf = turn_state.get("token_buffer", "")
        if buf:
            from nyx.agent.output import wrap_token_with_side_rule
            wrapped = wrap_token_with_side_rule(buf, side_rule_state)
            sys.stdout.write(wrapped)
            sys.stdout.flush()
            turn_state["token_buffer"] = ""

    def on_token(token: str) -> None:
        if not turn_state["streamed_text"]:
            _stop_spinner()
            sys.stdout.write("\r\x1b[2K")
            sys.stdout.flush()
            # STREAMING-SIDE-RULE-01: reset state no início do turno.
            side_rule_state.clear()
        turn_state["streamed_text"] += token
        turn_state["token_buffer"] += token
        if len(turn_state["token_buffer"]) >= TOKEN_FLUSH_CHARS or "\n" in token:
            _flush_buffer()

    # TUI-REDESIGN-25-10: tool_args_cache mantém args entre on_tool e
    # on_tool_result para render_tool_chip ter acesso ao arg_preview.
    tool_args_cache: dict[str, dict] = {}

    def on_tool(name: str, args: dict) -> None:
        _stop_spinner()
        turn_state["streamed_text"] = ""
        tool_timers[name] = time.monotonic()
        tool_args_cache[name] = args or {}

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
                tool_args_cache.pop(name, None)
                return
        started = tool_timers.pop(name, None)
        duration_ms = int((time.monotonic() - started) * 1000) if started else 0
        first_line = next((ln.strip() for ln in (result or "").splitlines() if ln.strip()), "")
        is_err = is_tool_error(first_line)
        from nyx.agent.output import (
            classify_error_actions,
            render_error_with_actions,
            render_tool_chip,
        )
        render_tool_chip(
            name=name,
            args=tool_args_cache.pop(name, {}),
            status="erro" if is_err else "ok",
            duration_ms=duration_ms,
            error_preview=first_line if is_err else None,
            project_root=str(PROJECT_ROOT),
        )
        # TUI-REDESIGN-25-11: erros conhecidos ganham bloco de ações sugeridas.
        if is_err and first_line:
            actions = classify_error_actions(first_line)
            if actions:
                render_error_with_actions(first_line, actions=actions)

    def on_compaction(level: int, tokens_removed: int, pct_before: float, pct_after: float) -> None:
        render_compaction_event(level, tokens_removed, pct_before, pct_after)

    from nyx.agent.commands._observability import on_model_state_log

    def on_model_state(state: str) -> None:
        """Consumidor visual de transições cold/warming/warm (UX-BUG-02B).

        Grava em app_state para que _bottom_toolbar leia no próximo render.
        Mantém o log de debug do stub anterior intacto para auditoria.
        """
        app_state["model_state"] = state
        on_model_state_log(state)

    agent = AgentLoop(
        project_root=project_root,
        proxy_url=proxy_url,
        model=model,
        on_token=on_token if streaming else None,
        on_tool=on_tool,
        on_tool_result=on_tool_result,
        on_permission=_make_ask_permission(app_state),
        on_compaction=on_compaction,
        on_model_state=on_model_state,
        streaming=streaming,
        settings=settings,
    )

    print(_build_banner(model, agent.tools_count, PROJECT_ROOT.name, settings=settings))

    # SESSION-RESUME-01: --resume <id> ou prompt de retomada pós-banner.
    if resume_id:
        from nyx.agent.persistence import load_session_by_id

        loaded = load_session_by_id(resume_id)
        if loaded:
            agent._session = loaded
            print(
                f"  {ACCENT}[ok]{NC} Sessão {resume_id} restaurada "
                f"({len(loaded.history)} entradas)"
            )
        else:
            _print_error(
                f"--resume '{resume_id}' não encontrou sessão única.",
                hint="Use /resume list após o boot para ver os ids disponíveis.",
            )
    elif not no_resume_prompt:
        maybe_offer_resume(agent, project_name=PROJECT_ROOT.name)

    # UX-BUG-02C + UX-BUG-03: warm-up pós-banner em task. Inclui agora
    # também Analytics() (que era síncrono pré-banner). cleanup_old_sessions
    # e Analytics são file I/O pequenos; memory.index() é cacheado lazy
    # (segunda chamada O(1)). render visual das entradas roda quando termina.
    async def _warmup() -> None:
        try:
            from nyx.agent.persistence import cleanup_old_sessions
            from nyx.agent.services.analytics import Analytics

            cleanup_old_sessions()
            analytics_ref[0] = Analytics()
            memory_entries = agent._memory.index() if hasattr(agent, "_memory") else []
            if memory_entries:
                names = ", ".join(e["file"] for e in memory_entries[:3])
                suffix = f" (+{len(memory_entries) - 3})" if len(memory_entries) > 3 else ""
                print(f"  {DIM}[memória: {len(memory_entries)} entradas] {names}{suffix}{NC}")
        except Exception as exc:  # noqa: BLE001 -- warm-up best-effort
            logger.warning("warm-up pos-banner falhou: %s", exc)

    warmup_task = asyncio.create_task(_warmup())
    # UX-BUG-03: rastreamos summarize_task entre turns para cancelar a
    # anterior se ainda não terminou (evita acúmulo) e incluir no shutdown.
    summarize_task: "asyncio.Task | None" = None

    # UX-BUG-02C: drenar stdin antes do primeiro prompt_async em tty real.
    # Descarta keystrokes que o usuário digitou durante o cold-start, evitando
    # que prompt_toolkit os interprete fora de ordem ao trocar para raw mode.
    # Em não-tty (CI/headless/pipe) o flush é noop e tratamos com fallback
    # silencioso. Em tty real, falhas viram logger.warning (nunca silent pass).
    if sys.stdin.isatty():
        try:
            import termios

            try:
                termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
            except (termios.error, OSError) as exc:
                logger.warning("termios.tcflush falhou: %s", exc)
        except ImportError as exc:
            # termios só existe em POSIX; em outras plataformas o drain
            # de stdin é noop e seguimos sem ele.
            logger.debug("termios indisponível (plataforma não-POSIX): %s", exc)

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
                # UX-EXTRA-01: prefill via /edit pré-popula próximo prompt_async.
                prefill = str(app_state.pop("prefill", "") or "")
                user_input = (
                    await prompt_session.prompt_async(ANSI(prompt_str), default=prefill)
                ).strip()
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
            # VISION-02: expande [Image #N] pela descrição da imagem antes do
            # render e do envio ao agent.run (ambos veem o texto já enriquecido).
            if image_map and "[Image #" in user_input:
                user_input = _expand_images(user_input, image_map)
            last_input_state["text"] = user_input
            # TUI-REDESIGN-25-07: remove eco "nyx> X" do prompt_toolkit antes
            # de renderizar a bubble. \033[1A move up, \r retorna ao início,
            # \033[2K limpa a linha. Sem efeito em pipe/headless (stdout não-tty).
            if sys.stdout.isatty():
                sys.stdout.write("\033[1A\r\033[2K")
                sys.stdout.flush()
            render_user_input(
                user_input,
                user_name=str(app_state.get("user_display_name", "você")),
            )

        if user_input.startswith("/"):
            result = handle_command(user_input, project_root)
            if result is None:
                continue

            if result == "__quit__":
                # TUI-REDESIGN-25-14: card de stats da sessão antes do shutdown.
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
                    project_root=str(PROJECT_ROOT),
                )
                # UX-LIFECYCLE-01: shutdown explícito do proxy via loopback.
                # Resposta volta antes do auto-SIGTERM do proxy, então usamos
                # timeout curto e ignoramos falhas (run.sh trap cobre o resto).
                try:
                    import httpx as _httpx_quit

                    async with _httpx_quit.AsyncClient(timeout=2.0) as _qs:
                        await _qs.post(f"{proxy_url}/admin/shutdown")
                except Exception as _exc:  # noqa: BLE001 -- shutdown best-effort
                    logger.debug("admin/shutdown best-effort falhou: %s", _exc)
                break

            if result == "__clear__":
                agent.reset()
                if use_rich and output:
                    output("ok", " sessão limpa")
                else:
                    print(f"  {SUCCESS} sessão limpa{NC}")
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
                    output("sessão", status_msg)
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
                    print(f"  {SUCCESS} sessão salva{NC}: {saved.name}")
                else:
                    _print_error(
                        "Falha ao salvar a sessão atual.",
                        hint="Verifique permissões de escrita em ~/.nyx/sessions/.",
                    )
                continue

            if result == "__session_load__":
                from nyx.agent.persistence import load_latest_session

                loaded = load_latest_session(PROJECT_ROOT.name)
                if loaded:
                    agent._session = loaded
                    print(f"  {SUCCESS} sessão restaurada{NC} ({len(loaded.history)} entradas)")
                else:
                    _print_error(
                        "Nenhuma sessão salva para restaurar.",
                        hint="Use /quit para salvar esta sessão e rode novamente para carregá-la.",
                    )
                continue

            if isinstance(result, str) and result.startswith("__session_load_id__"):
                # SESSION-RESUME-01: /resume <prefixo>
                prefix = result[len("__session_load_id__"):]
                from nyx.agent.persistence import load_session_by_id

                loaded = load_session_by_id(prefix)
                if loaded:
                    agent._session = loaded
                    print(
                        f"  {ACCENT}[ok]{NC} Sessão {prefix} restaurada "
                        f"({len(loaded.history)} entradas)"
                    )
                else:
                    _print_error(
                        f"Nenhuma sessão única casa com '{prefix}'.",
                        hint="Use /resume list para ver todas, depois /resume <prefixo único>.",
                    )
                continue

            if result == "__cancel_inflight__":
                # UX-AGENCY-02: cancel real via asyncio.
                # /cancel via prompt só funciona se a tool ainda estiver em curso
                # (normalmente o REPL só processa /cancel após tool concluir, então
                # o caminho prático é Ctrl+C; este handler é fallback para shells
                # com input buffer ou modo headless onde Ctrl+C pode não bubblar).
                inflight = app_state.get("inflight_task")
                if inflight is not None and not inflight.done():
                    inflight.cancel()
                    print(f"  {SUCCESS} cancel sinalizado{NC} (asyncio.CancelledError despachado)")
                else:
                    print(
                        f"  {DIM}/cancel: nenhuma tool em curso. "
                        f"Use Ctrl+C durante execução para interromper.{NC}"
                    )
                continue

            if result == "__aesthetic_list__":
                from nyx.themes.design_tokens_extended import list_aesthetics, list_entities

                cur = app_state.get(
                    "aesthetic_id",
                    os.environ.get("NYX_AESTHETIC", "default"),
                )
                cur_ent = app_state.get(
                    "entity_id",
                    os.environ.get("NYX_ENTITY", "nyx"),
                )
                print(f"  Estéticos disponíveis (atual: {ACCENT}{cur}{NC}):")
                for a in list_aesthetics():
                    marker = f"{ACCENT}* {NC}" if a["id"] == cur else "  "
                    print(f"    {marker}{ACCENT}{a['id']:<10}{NC} -- {a['tagline']}")
                print(f"  Entidades disponíveis (atual: {SUCCESS}{cur_ent}{NC}):")
                for e in list_entities():
                    marker = f"{SUCCESS}* {NC}" if e["id"] == cur_ent else "  "
                    print(f"    {marker}{SUCCESS}{e['id']:<6}{NC} {e['name']:<6} accent {e['accent']}")
                continue

            if result == "__aesthetic_get__":
                cur = app_state.get(
                    "aesthetic_id",
                    os.environ.get("NYX_AESTHETIC", "default"),
                )
                cur_ent = app_state.get(
                    "entity_id",
                    os.environ.get("NYX_ENTITY", "nyx"),
                )
                print(f"  Estético atual: {ACCENT}{cur}{NC} | Entidade: {SUCCESS}{cur_ent}{NC}")
                continue

            if isinstance(result, str) and result.startswith("__aesthetic_set__"):
                from nyx.themes.design_tokens_extended import AESTHETICS, ENTITIES

                target = result[len("__aesthetic_set__"):].strip()
                # Aceita 'aesthetic' ou 'aesthetic:entity'
                if ":" in target:
                    a_id, e_id = target.split(":", 1)
                    a_id, e_id = a_id.strip(), e_id.strip()
                else:
                    a_id, e_id = target.strip(), None
                if a_id and a_id not in AESTHETICS:
                    _print_error(
                        f"Estético '{a_id}' não existe.",
                        hint="Use /aesthetic list para ver opções.",
                    )
                    continue
                if e_id and e_id not in ENTITIES:
                    _print_error(
                        f"Entidade '{e_id}' não existe.",
                        hint="Use /aesthetic list para ver opções.",
                    )
                    continue
                if a_id:
                    app_state["aesthetic_id"] = a_id
                    os.environ["NYX_AESTHETIC"] = a_id
                if e_id:
                    app_state["entity_id"] = e_id
                    os.environ["NYX_ENTITY"] = e_id
                final_a = app_state.get("aesthetic_id", "default")
                final_e = app_state.get("entity_id", "nyx")
                print(f"  {SUCCESS} aesthetic{NC}: {final_a}:{final_e} (próxima invocação aplica)")
                continue

            if result == "__schema_list__":
                from nyx.themes.design_tokens_extended import (
                    DEFAULT_SCHEMA,
                    list_schemas,
                )

                cur = app_state.get(
                    "schema_id",
                    os.environ.get("NYX_SCHEMA", DEFAULT_SCHEMA),
                )
                print(f"  Schemas disponíveis (atual: {ACCENT}{cur}{NC}):")
                for s in list_schemas():
                    marker = f"{ACCENT}* {NC}" if s["id"] == cur else "  "
                    print(
                        f"    {marker}{ACCENT}{s['id']:<10}{NC} -- "
                        f"case {s['heading_case']} · user {s['user_bubble']} · nyx {s['nyx_bubble']}"
                    )
                continue

            if result == "__schema_get__":
                from nyx.themes.design_tokens_extended import DEFAULT_SCHEMA

                cur = app_state.get(
                    "schema_id",
                    os.environ.get("NYX_SCHEMA", DEFAULT_SCHEMA),
                )
                print(f"  Schema atual: {ACCENT}{cur}{NC}")
                continue

            if isinstance(result, str) and result.startswith("__schema_set__"):
                from nyx.themes.design_tokens_extended import INTERFACE_SCHEMAS

                target = result[len("__schema_set__"):].strip()
                if target not in INTERFACE_SCHEMAS:
                    _print_error(
                        f"Schema '{target}' não existe.",
                        hint="Use /schema list para ver opções.",
                    )
                    continue
                app_state["schema_id"] = target
                os.environ["NYX_SCHEMA"] = target
                print(
                    f"  {SUCCESS} schema{NC}: {target} (próxima invocação aplica)"
                )
                continue

            if result == "__output_style_list__":
                from nyx.agent.output_style import list_styles

                current = str(app_state.get("output_style", "default"))
                print("  Estilos de saída:")
                for st in list_styles():
                    marker = f"{ACCENT}* {NC}" if st.name == current else "  "
                    print(f"    {marker}{ACCENT}{st.name:<10}{NC} -- {st.description}")
                continue

            if result == "__output_style_get__":
                current = str(app_state.get("output_style", "default"))
                print(f"  Estilo atual: {ACCENT}{current}{NC}")
                continue

            if isinstance(result, str) and result.startswith("__output_style_set__"):
                from nyx.agent.output_style import STYLES

                target = result[len("__output_style_set__"):].strip()
                if target not in STYLES:
                    _print_error(
                        f"Estilo '{target}' não existe.",
                        hint="Use /output-style list para ver opções.",
                    )
                    continue
                app_state["output_style"] = target
                print(f"  {ACCENT}[ok]{NC} estilo trocado para {target} (próxima request usa)")
                continue

            if result == "__plugin_list__":
                from nyx.agent.services.plugin_manager import PluginManager

                pm = PluginManager()
                plugins = pm.list()
                if not plugins:
                    _print_error(
                        "Nenhum plugin em ~/.nyx/plugins/.",
                        hint="Use /plugin install <path> para instalar um.",
                    )
                    continue
                print(f"  Plugins ({len(plugins)}):")
                for p in plugins:
                    status = f"{DIM}({p.error}){NC}" if p.error else f"{ACCENT}OK{NC}"
                    print(
                        f"    {ACCENT}{p.name}{NC} v{p.version} [{status}] "
                        f"-- tools={len(p.tools)} cmds={len(p.commands)}"
                    )
                    if p.description:
                        print(f"      {DIM}{p.description}{NC}")
                continue

            if result == "__plugin_reload__":
                from nyx.agent.services.plugin_manager import PluginManager

                pm = PluginManager()
                results = pm.reload()
                ok = sum(1 for v in results.values() if v)
                print(
                    f"  {ACCENT}[ok]{NC} plugins recarregados: "
                    f"{ok}/{len(results)} OK"
                )
                continue

            if isinstance(result, str) and result.startswith("__plugin_install__"):
                src = result[len("__plugin_install__"):].strip()
                from nyx.agent.services.plugin_manager import PluginManager

                pm = PluginManager()
                name = pm.install(src)
                if name:
                    print(f"  {ACCENT}[ok]{NC} plugin '{name}' instalado")
                else:
                    _print_error(
                        f"Falha ao instalar plugin a partir de {src!r}.",
                        hint="Confirme que o diretório existe e contém manifest.toml válido.",
                    )
                continue

            if isinstance(result, str) and result.startswith("__plugin_uninstall__"):
                name = result[len("__plugin_uninstall__"):].strip()
                from nyx.agent.services.plugin_manager import PluginManager

                pm = PluginManager()
                pm.discover()
                if pm.uninstall(name):
                    print(f"  {ACCENT}[ok]{NC} plugin '{name}' removido")
                else:
                    _print_error(
                        f"Plugin '{name}' não encontrado.",
                        hint="Use /plugin list para ver instalados.",
                    )
                continue

            if result == "__mcp_list__":
                # MCP-SERVER-01: lista servers + tools de ~/.nyx/mcp.json
                from nyx.agent.services.mcp_client import McpClient

                client = McpClient.from_config()
                if not client.servers:
                    _print_error(
                        "Nenhum server MCP configurado.",
                        hint="Crie ~/.nyx/mcp.json com {\"servers\": {...}}.",
                    )
                    continue
                await client.connect_all()
                print(f"  Servers MCP ({len(client.servers)}):")
                for name, srv in client.servers.items():
                    status = (
                        f"{ACCENT}OK{NC}" if srv.connected else f"{DIM}{srv.error or 'down'}{NC}"
                    )
                    print(f"    {ACCENT}{name}{NC} [{status}] -- {len(srv.tools)} tool(s)")
                    for tool in srv.tools[:5]:
                        tname = tool.get("name", "?")
                        tdesc = (tool.get("description") or "").strip()[:60]
                        print(f"      {DIM}- {tname}: {tdesc}{NC}")
                    if len(srv.tools) > 5:
                        print(f"      {DIM}... (+{len(srv.tools) - 5} tools){NC}")
                await client.close_all()
                continue

            if result == "__mcp_reload__":
                from nyx.agent.services.mcp_client import McpClient

                client = McpClient.from_config()
                if not client.servers:
                    _print_error("Nenhum server MCP em ~/.nyx/mcp.json.", hint=None)
                    continue
                results = await client.connect_all()
                ok = sum(1 for v in results.values() if v)
                print(f"  {ACCENT}[ok]{NC} MCP recarregado: {ok}/{len(results)} server(s) conectado(s)")
                await client.close_all()
                continue

            if isinstance(result, str) and result.startswith("__mcp_test__"):
                target = result[len("__mcp_test__"):].strip()
                from nyx.agent.services.mcp_client import McpClient

                client = McpClient.from_config()
                if target not in client.servers:
                    _print_error(
                        f"Server MCP '{target}' não encontrado.",
                        hint="Veja /mcp list.",
                    )
                    continue
                await client.connect_all()
                alive = await client.ping(target)
                if alive:
                    print(f"  {ACCENT}[ok]{NC} MCP {target} responde (ping ok)")
                else:
                    _print_error(
                        f"MCP {target} não responde ao ping.",
                        hint="Verifique o command/args em ~/.nyx/mcp.json.",
                    )
                await client.close_all()
                continue

            if result == "__edit_last__":
                # UX-EXTRA-01: pré-popula próximo prompt_async via app_state["prefill"].
                last = last_input_state.get("text", "")
                if not last:
                    _print_error(
                        "Nenhum input anterior para editar.",
                        hint="Envie uma mensagem antes de usar /edit.",
                    )
                    continue
                app_state["prefill"] = last
                print(f"  {DIM}último input prefillado no próximo prompt; edite e Enter.{NC}")
                continue

            if result == "__config_setup__":
                # ONBOARDING-01: wizard interativo grava ~/.nyx/config.toml.
                config_path = Path.home() / ".nyx" / "config.toml"
                config_path.parent.mkdir(parents=True, exist_ok=True)
                if config_path.exists():
                    backup = config_path.with_suffix(".toml.bak")
                    backup.write_bytes(config_path.read_bytes())
                    print(f"  {DIM}backup salvo em {backup}{NC}")
                try:
                    from nyx.config.defaults import DEFAULT_MODEL as _DM

                    modelo = input(f"  modelo preferido [{_DM}]: ").strip() or _DM
                    tema = input("  tema [paleta_d]: ").strip() or "paleta_d"
                    bypass = input(
                        "  bypass default (cauteloso/moderado/ousado) [cauteloso]: "
                    ).strip() or "cauteloso"
                    ctx_raw = input("  limite de contexto em turnos [40]: ").strip() or "40"
                    try:
                        ctx_limit = int(ctx_raw)
                    except ValueError:
                        print(f"  {DIM}valor inválido, usando 40{NC}")
                        ctx_limit = 40
                except (EOFError, KeyboardInterrupt):
                    print(f"\n  {DIM}/config setup cancelado{NC}")
                    continue

                content = (
                    "# Configuração Nyx gerada via /config setup (ONBOARDING-01)\n"
                    f'modelo = "{modelo}"\n'
                    f'tema = "{tema}"\n'
                    f'bypass = "{bypass}"\n'
                    f"ctx_limit = {ctx_limit}\n"
                )
                tmp = config_path.with_suffix(".toml.tmp")
                tmp.write_text(content, encoding="utf-8")
                tmp.replace(config_path)
                print(f"  {ACCENT}[ok]{NC} configuração salva em {config_path}")
                continue

            if result == "__session_index__":
                # SESSION-RESUME-01: /resume list
                from nyx.agent.persistence import load_index

                idx = load_index()
                if not idx:
                    _print_error(
                        "Nenhuma sessão indexada.",
                        hint="Saia com /quit para gerar a primeira entrada do índice.",
                    )
                    continue
                print(f"  {len(idx)} sessões no índice (mais recentes embaixo):")
                for entry in idx[-20:]:
                    sid = entry.get("id", "?")
                    prompt_preview = entry.get("primeiro_prompt", "")[:60]
                    n = entry.get("n_turnos", 0)
                    print(f"    {ACCENT}{sid[:32]:<32}{NC}  {n:>2} turnos  {DIM}{prompt_preview}{NC}")
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
                if ctx:
                    print(f"  {ctx}")
                else:
                    _print_error(
                        "Nenhum arquivo no contexto da sessão.",
                        hint="Peça a Nyx para ler um arquivo ou use /read <caminho>.",
                    )
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
                    _print_error(
                        "Nenhuma tool call registrada nesta sessão.",
                        hint="Faça uma pergunta à Nyx para gerar atividade antes de inspecionar /trace.",
                    )
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
                    except FileNotFoundError as exc:
                        tmp = Path.home() / ".nyx" / "clipboard.txt"
                        tmp.write_text(last_content, encoding="utf-8")
                        _print_error(
                            "xclip indisponível no sistema.",
                            hint=f"Conteúdo salvo em {tmp}. Instale com: sudo apt install xclip",
                            debug_detail=str(exc),
                        )
                else:
                    _print_error(
                        "Nenhum output disponível para copiar.",
                        hint="Aguarde uma resposta da Nyx ou execute um comando antes de /copy.",
                    )
                continue

            if isinstance(result, str) and result.startswith("__error__"):
                payload = result[len("__error__"):]
                if "||" in payload:
                    msg, hint = payload.split("||", 1)
                else:
                    msg, hint = payload, None
                _print_error(msg, hint=hint)
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
            turn_state["token_buffer"] = ""
            # UX-LOOP-VISIBILITY-01: label dinâmico do spinner reflete o
            # estado do modelo (warming/warm) lido de app_state e a duração
            # decorrida desde o Enter. Usuário vê " aquecendo modelo..."
            # nos primeiros 3s quando model_state=="warming", depois transita
            # para "pensando..." e cronômetro discreto.
            request_started = time.monotonic()
            spinner = nyx_spinner(
                lambda: build_warming_label(
                    str(app_state.get("model_state", "cold")),
                    request_started,
                )
            )
            spinner.__enter__()
            spinner_state["active"] = spinner
            render_assistant_start()
            # UX-AGENCY-02: cancel real via asyncio.create_task + tracking em app_state.
            # /cancel ou Ctrl+C cancelam essa task (Ctrl+C captura via KeyboardInterrupt;
            # /cancel via app_state["inflight_task"].cancel() no handler).
            inflight = asyncio.create_task(agent.run(user_input))
            app_state["inflight_task"] = inflight
            try:
                status = await inflight
            except asyncio.CancelledError:
                _stop_spinner()
                _flush_buffer()
                sys.stdout.write("\r\x1b[2K")
                sys.stdout.flush()
                print(f"\n  {SUCCESS} cancelado{NC} (tool em curso interrompida)")
                # Continua o REPL — usuário recupera controle.
                app_state["inflight_task"] = None
                continue
            finally:
                _stop_spinner()
                _flush_buffer()
                app_state["inflight_task"] = None
            total_iterations += status.iterations

            streamed = turn_state["streamed_text"].strip()
            summary = (status.summary or "").strip()

            def _is_subset(a: str, b: str) -> bool:
                """Retorna True se a é essencialmente contida em b (ignora whitespace)."""
                ca = " ".join(a.split())
                cb = " ".join(b.split())
                return bool(ca) and bool(cb) and (ca in cb or cb in ca)

            already_shown = bool(streamed) and bool(summary) and _is_subset(streamed, summary)
            if summary and not already_shown:
                if use_rich and output:
                    output("nyx", status.summary)
                else:
                    print(f"\n{PRIMARY}{status.summary}{NC}\n")
            elif streamed:
                print()

            state_label = status.state.value
            if status.state != status.state.DONE:
                if state_label == "error":
                    _print_error(
                        f"Iteração encerrou em estado '{state_label}'.",
                        hint="Consulte ~/.nyx/logs/nyx.log para o traceback completo.",
                    )
                else:
                    print(f"  {DIM}[{state_label}]{NC}")

            # TUI-REDESIGN-25-08: meta inline (tempo + tokens) ao fim.
            _meta_tokens: int | None = None
            try:
                usage = getattr(status, "usage", None) or {}
                if isinstance(usage, dict):
                    _meta_tokens = (
                        usage.get("total_tokens")
                        or usage.get("output_tokens")
                        or usage.get("completion_tokens")
                    )
            except Exception:
                _meta_tokens = None
            render_assistant_end(
                start_monotonic=request_started,
                tokens=_meta_tokens,
            )

            # UX-BUG-03: cancelar summarize anterior se ainda não terminou
            # antes de criar nova. Evita acúmulo de tasks pendentes em
            # conversas longas.
            if summarize_task is not None and not summarize_task.done():
                summarize_task.cancel()
            try:
                summarize_task = asyncio.create_task(agent.maybe_summarize())
            except RuntimeError as exc:
                logger.warning("sumarização adiada (loop indisponível): %s", exc)
                summarize_task = None

        except KeyboardInterrupt:
            # UX-AGENCY-02: cancela inflight task explicitamente para que
            # asyncio.CancelledError propague e tools encerrem limpas.
            _inflight = app_state.get("inflight_task")
            if _inflight is not None and not _inflight.done():
                _inflight.cancel()
            _stop_spinner()
            _flush_buffer()
            sys.stdout.write("\r\x1b[2K")
            sys.stdout.flush()
            print(f"\n  {SUCCESS} cancelado{NC}")

    elapsed = time.time() - session_start

    session_summary = (
        f"Iterações: {total_iterations} | "
        f"Lidos: {agent.session.files_read_count} | "
        f"Modificados: {agent.session.files_modified_count} | "
        f"Tempo: {elapsed:.1f}s"
    )
    if use_rich and output:
        output("sessão", session_summary)
    else:
        print(f"\n  {ACCENT}[sessão]{NC} {session_summary}\n")

    # UX-BUG-03: shutdown ordenado.
    # 1) Cancela todas as tasks pendentes (exceto a corrente). Inclui:
    #    warmup_task (se ainda não terminou), summarize_task (última),
    #    qualquer task spawnada por handlers via run_in_terminal etc.
    # 2) Aguarda finalização com gather(return_exceptions=True) para
    #    drenar CancelledError sem propagar. Timeout curto via wait_for
    #    para não travar o shutdown se uma task ignorar cancelamento.
    # 3) end_session() só se Analytics() já foi criado pela warmup task.
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

    project_name = PROJECT_ROOT.name
    saved = save_session(agent.session, project_name)
    if saved:
        # DEPLOY-02 absorve O-04: feedback verde + path + dica /resume.
        from nyx.themes.design_tokens import ANSI_SUCCESS_FG

        print(f"\n  {ANSI_SUCCESS_FG} sessão salva{ANSI_RESET}")
        print(f"  {DIM}  {saved.resolve()}{NC}")
        print(f"  {DIM}  use /resume na próxima abertura para retomar{NC}")

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
    parser.add_argument(
        "--resume",
        metavar="ID",
        default=None,
        help="Retoma sessão por id ou prefixo único (SESSION-RESUME-01).",
    )
    parser.add_argument(
        "--no-resume-prompt",
        action="store_true",
        help="Suprime o prompt 'Retomar última sessão?' no boot.",
    )
    parser.add_argument(
        "--skip-onboarding",
        action="store_true",
        help="Pula tutorial de primeiro uso (ONBOARDING-01).",
    )
    args = parser.parse_args()

    if args.smoke:
        print("boot ok")
        sys.exit(0)

    if args.headless:
        sys.exit(asyncio.run(run_headless()))
    else:
        # ONBOARDING-01: tutorial de primeiro uso antes do REPL.
        from nyx.agent.onboarding import (
            mark_done as _mark_onboarding_done,
            run_first_time_tutorial,
            should_run_tutorial,
        )

        if should_run_tutorial(args.skip_onboarding):
            # TUI-REDESIGN-25-04: tutorial usa nome resolvido em runtime.
            from nyx.agent.onboarding import resolve_user_display_name as _resolve_un
            run_first_time_tutorial(user_name=_resolve_un())
        elif args.skip_onboarding:
            _mark_onboarding_done()

        sys.exit(
            asyncio.run(
                run_repl(
                    streaming=not args.no_stream,
                    resume_id=args.resume,
                    no_resume_prompt=args.no_resume_prompt,
                )
            )
        )


if __name__ == "__main__":
    main()


# "O terminal é o lar do programador." -- Ken Thompson
