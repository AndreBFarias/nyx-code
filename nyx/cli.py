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


# Glifos do estado do modelo (UX-BUG-02B).
# Círculos da faixa Geometric Shapes (U+25CB/D0/CF) — não são emoji.
# NÃO remover via sanitizer global: invariante #14 (sprint_invariants.sh) protege estes 3 caracteres.
_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}


from nyx.agent.banner import build_banner as _build_banner  # noqa: E402
from nyx.agent.output import make_ask_permission as _make_ask_permission  # noqa: E402
from nyx.agent.output import print_error as _print_error  # noqa: E402


_IMAGE_INDEX_PATH = Path.home() / ".nyx" / "image_index.json"


def _persist_image_index(image_map: dict[int, str]) -> None:
    """Persiste image_map em ~/.nyx/image_index.json (VISION-02).

    Permite que /vision N consulte mesmo depois de o usuário avançar
    em outros turns na sessão.
    """
    import json as _json

    try:
        _IMAGE_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        _IMAGE_INDEX_PATH.write_text(
            _json.dumps({str(k): v for k, v in image_map.items()}),
            encoding="utf-8",
        )
    except OSError as exc:
        import logging as _log

        _log.getLogger("nyx.cli").warning("image_index persist falhou: %s", exc)


def _shorten_description(desc: str, max_chars: int = 200) -> str:
    """Trunca descrição em duas primeiras frases ou max_chars (VISION-02)."""
    if len(desc) <= max_chars:
        return desc
    sentences = desc.split(". ")
    acc = ""
    for s in sentences[:2]:
        if len(acc) + len(s) > max_chars:
            break
        acc += s + ". "
    return (acc.strip() or desc[:max_chars]) + "…"


def _expand_images(
    user_input: str,
    image_map: dict[int, str],
    vision: "VisionService | None" = None,
) -> str:
    """Substitui `[Image #N]` pela descrição da imagem em image_map (VISION-02).

    Usa VisionService cache; se moondream ausente, retorna sentinela
    "[Imagem #N: visao indisponivel]" para não bloquear o fluxo.
    """
    import re

    from nyx.agent.services.vision_service import VisionService

    if not image_map:
        return user_input

    svc = vision if vision is not None else VisionService()

    def _repl(match: re.Match[str]) -> str:
        n = int(match.group(1))
        path_str = image_map.get(n)
        if not path_str:
            return f"[Imagem #{n}: referência inválida]"
        path = Path(path_str)
        if not path.is_file():
            return f"[Imagem #{n}: arquivo não encontrado]"
        desc = svc.describe(path)
        short = _shorten_description(desc)
        return f"[Imagem #{n}: {short}]"

    return re.sub(r"\[Image #(\d+)\]", _repl, user_input)


if TYPE_CHECKING:
    from nyx.agent.services.vision_service import VisionService


async def run_repl(streaming: bool = True) -> int:
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
              [model_state]             -- ○ cold | ◐ warming | ● warm (UX-BUG-02B)
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

            meta = f" · {model} · iter {iter_n} · lidos {reads} · modif {mods}"
            parts.append((f"fg:{NYX_MUTED}", meta))

            model_state = app_state.get("model_state", "cold")
            glyph = _STATE_GLYPHS.get(model_state, _STATE_GLYPHS["cold"])
            parts.append((f"fg:{NYX_MUTED}", f" · {glyph} {model_state}"))

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
    image_counter: dict[str, int] = {"n": 0}
    image_map: dict[int, str] = {}
    tool_timers: dict[str, float] = {}

    TOKEN_FLUSH_CHARS = 32

    def _stop_spinner() -> None:
        sp = spinner_state.get("active")
        if sp is not None:
            sp.stop()  # type: ignore[union-attr]
            spinner_state["active"] = None

    def _flush_buffer() -> None:
        buf = turn_state.get("token_buffer", "")
        if buf:
            sys.stdout.write(buf)
            sys.stdout.flush()
            turn_state["token_buffer"] = ""

    def on_token(token: str) -> None:
        if not turn_state["streamed_text"]:
            _stop_spinner()
            sys.stdout.write("\r\x1b[2K")
            sys.stdout.flush()
        turn_state["streamed_text"] += token
        turn_state["token_buffer"] += token
        if len(turn_state["token_buffer"]) >= TOKEN_FLUSH_CHARS or "\n" in token:
            _flush_buffer()

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
            # VISION-02: expande [Image #N] pela descrição da imagem antes do
            # render e do envio ao agent.run (ambos veem o texto já enriquecido).
            if image_map and "[Image #" in user_input:
                user_input = _expand_images(user_input, image_map)
            last_input_state["text"] = user_input
            render_user_input(user_input)

        if user_input.startswith("/"):
            result = handle_command(user_input, project_root)
            if result is None:
                continue

            if result == "__quit__":
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
                    print(f"  {ACCENT}[ok]{NC} Sessão salva: {saved.name}")
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
                    print(f"  {ACCENT}[ok]{NC} Sessão restaurada ({len(loaded.history)} entradas)")
                else:
                    _print_error(
                        "Nenhuma sessão salva para restaurar.",
                        hint="Use /quit para salvar esta sessão e rode novamente para carregá-la.",
                    )
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
            # decorrida desde o Enter. Usuário vê "◐ aquecendo modelo..."
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
            try:
                status = await agent.run(user_input)
            finally:
                _stop_spinner()
                _flush_buffer()
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

            render_assistant_end()

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
            _stop_spinner()
            _flush_buffer()
            sys.stdout.write("\r\x1b[2K")
            sys.stdout.flush()
            print(f"\n  {ACCENT}[cancelado]{NC}")

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
