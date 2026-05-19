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
    NYX_ERROR,
    NYX_MUTED,
    NYX_PRIMARY,
    NYX_PURPLE,
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
_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}


# SHIFT-TAB-CYCLE-01: Shift+Tab cicla 4 modos em vez de toggle binário.
# Ordem: normal -> plan -> sudo -> bypass -> normal.
# - normal:  comportamento padrão (permissões + sandbox).
# - plan:    read-only via plan_mode.set_plan_mode(True); write bloqueado.
# - sudo:    libera prefixo sudo em run_command (depende de SUDO-MODE-01 para cache de senha).
# - bypass:  pula CONFIRM_ONCE silenciosamente (paridade com CLI de referência).
_MODES: tuple[str, ...] = ("normal", "plan", "sudo", "bypass")


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

# INFRA-CLI-SPLIT-02: KeyBindings, bottom toolbar e dispatcher de sentinelas
# saíram para módulos dedicados. cli.py orquestra agora.
from nyx.cli_keybindings import (  # noqa: E402
    build_bottom_toolbar,
    build_keybindings,
    build_prompt_style,
)
from nyx.cli_handlers import HandlerCtx, dispatch_async, dispatch_sync  # noqa: E402


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
    from nyx.agent.loop import AgentLoop
    from nyx.agent.persistence import save_session
    from nyx.config.settings import load_settings

    settings = load_settings()

    # PROJECT-ROOTS-MULTI-01: inicializa sandbox roots no módulo base.
    # _ACTIVE_ROOT recebe o project_root atual; extras do env/toml entram
    # via add_extra_root() (idempotente). Paths inexistentes são logados
    # e ignorados -- sandbox preserva strictness (não autoriza fantasmas).
    try:
        from nyx.agent.tools.base import add_extra_root, set_active_project_root

        set_active_project_root(str(PROJECT_ROOT))
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

    # NYX-AUTO-APPROVE-01: alerta visível quando modo automatizado está ativo.
    # CONFIRM_ONCE será silenciosamente aprovado em PermissionChecker.check.
    # DENY continua bloqueando. Usar somente em automação confiável (CI, cockpit).
    if os.environ.get("NYX_AUTO_APPROVE") == "1":
        logger.warning(
            "NYX_AUTO_APPROVE=1 ativo: CONFIRM_ONCE auto-aprovado. "
            "Use somente em automação confiável."
        )

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

    proxy_url = os.environ.get("OPENAI_BASE_URL", settings.proxy_v1_url)
    proxy_url = proxy_url.replace("/v1", "").rstrip("/")
    if not proxy_url.startswith("http"):
        proxy_url = settings.proxy_url
    model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", settings.model))

    # INFRA-CLI-SPLIT-02: estado mutável (app_state, last_input_state,
    # image_map, image_counter) é alocado ANTES das factories de
    # PromptSession porque KeyBindings/_bottom_toolbar fecham sobre estes
    # refs. No layout original (pré-split) o late binding do Python
    # permitia ordem invertida; aqui forçamos a ordem explícita.
    spinner_state: dict[str, object | None] = {"active": None}
    turn_state: dict[str, str] = {"streamed_text": "", "token_buffer": ""}
    # app_state: bool para flags, str para estados ("model_state": cold/warming/warm — UX-BUG-02B).
    # TUI-REDESIGN-28-08b: repl_app_active sinaliza routing para output_buffer
    # da Application (False = comportamento legacy via stdout/PromptSession).
    app_state: dict[str, object] = {
        # SHIFT-TAB-CYCLE-01: "mode" é canônico; "bypass"/"plan_mode"/"sudo_mode"
        # ficam sincronizados pelo handler _cycle_mode para retrocompat.
        "mode": "normal",
        "bypass": False,
        "plan_mode": False,
        "sudo_mode": False,
        "model_state": "cold",
        "repl_app_active": False,
    }
    # TUI-REDESIGN-25-04: nome do usuário via git config (silent, fallback "visitante").
    from nyx.agent.onboarding import resolve_user_display_name
    app_state["user_display_name"] = resolve_user_display_name()
    # TUI-REDESIGN-25-14: marca início da sessão para card de stats no /quit.
    app_state["session_started_monotonic"] = time.monotonic()
    last_input_state: dict[str, str] = {"text": ""}
    image_counter: dict[str, int] = {"n": 0}
    image_map: dict[int, str] = {}

    prompt_session = None
    history_path = Path.home() / ".nyx" / "history"
    completer = None
    kb = None
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
        from prompt_toolkit.formatted_text import ANSI
        from prompt_toolkit.history import FileHistory
        from prompt_toolkit.shortcuts import CompleteStyle

        from nyx.agent.completer import create_completer

        history_path.parent.mkdir(parents=True, exist_ok=True)
        completer = create_completer(project_root)

        kb = build_keybindings(
            app_state=app_state,
            last_input_state=last_input_state,
            image_map=image_map,
            image_counter=image_counter,
            persist_image_index=_persist_image_index,
            modes=_MODES,
            ansi_dim=DIM,
            ansi_reset=NC,
            ansi_success=SUCCESS,
        )

        _bottom_toolbar = build_bottom_toolbar(
            app_state=app_state,
            model=model,
            state_glyphs=_STATE_GLYPHS,
            bullets=BULLETS,
            nyx_accent=NYX_ACCENT,
            nyx_muted=NYX_MUTED,
            nyx_primary=NYX_PRIMARY,
            nyx_purple=NYX_PURPLE,
            nyx_purple_dim=NYX_PURPLE_DIM,
            nyx_error=NYX_ERROR,
        )

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
            # TUI-REDESIGN-27-01: style customizado puxa cores Nyx para popup
            # de completion e bottom toolbar (substitui amarelo/cinza default).
            style=build_prompt_style(),
        )
        logger.info("prompt-toolkit ativo (histórico: %s)", history_path)
    except ImportError:
        logger.info("prompt-toolkit indisponível, usando input() nativo")

    from nyx.agent.context import render_context_bar
    from nyx.agent.output import (
        build_warming_label,
        is_tool_error,
        nyx_spinner,
        render_assistant_end,
        render_assistant_start,
        render_compaction_event,
        render_user_input,
    )

    TOKEN_FLUSH_CHARS = 32
    # STREAMING-SIDE-RULE-01: estado da faixa lateral entre flushes.
    side_rule_state: dict = {}
    tool_timers: dict[str, float] = {}

    def _stop_spinner() -> None:
        sp = spinner_state.get("active")
        if sp is not None:
            sp.stop()  # type: ignore[union-attr]
            spinner_state["active"] = None

    def _flush_buffer() -> None:
        buf = turn_state.get("token_buffer", "")
        if buf:
            from nyx.agent.output import _emit, wrap_token_with_side_rule
            wrapped = wrap_token_with_side_rule(buf, side_rule_state)
            # TUI-REDESIGN-28-08c-PARTE-2: routing via _emit quando Application
            # ativo (repl_app_active=True). Em legacy/headless, _emit cai em
            # sys.stdout.write + flush, preservando comportamento anterior.
            _emit(wrapped)
            turn_state["token_buffer"] = ""

    def on_token(token: str) -> None:
        if not turn_state["streamed_text"]:
            _stop_spinner()
            # TUI-REDESIGN-28-08c-PARTE-2: clear ANSI só faz sentido em stdout
            # direto (terminal raw). Em Application ativo, output_buffer não
            # interpreta ANSI cursor; o append_to_buffer recebe texto puro.
            if not app_state.get("repl_app_active"):
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
            render_tool_chip,
        )
        # TUI-REDESIGN-26-03-PARTE-2: ações classificadas vão para chip,
        # que alinha à direita da mesma linha quando há largura.
        err_actions = (
            classify_error_actions(first_line) if is_err and first_line else None
        )
        render_tool_chip(
            name=name,
            args=tool_args_cache.pop(name, {}),
            status="erro" if is_err else "ok",
            duration_ms=duration_ms,
            error_preview=first_line if is_err else None,
            project_root=str(PROJECT_ROOT),
            error_actions=err_actions,
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

    # PROJECT-ROOTS-MULTI-01: linha discreta sob o banner contando extras
    # autorizados. Mantém o grid do banner intacto (sem mutação de layout).
    try:
        from nyx.agent.tools.base import list_extra_roots as _extras

        _ext = _extras()
        if _ext:
            print(f"  {DIM}+{len(_ext)} root(s) extra(s) autorizado(s) -- /sandbox list{NC}")
    except Exception as _exc:  # noqa: BLE001 -- aviso best-effort
        logger.debug("contagem de extra roots no banner falhou: %s", _exc)

    # TUI-REDESIGN-28-07: cursor blink async no banner $nyx.code (~1.4s).
    # Skip silencioso em headless/CI (isatty=False) ou NYX_NO_ANIMATION=1.
    try:
        from nyx.agent.banner_blink import blink_cursor_at

        await blink_cursor_at()
    except Exception as _blink_exc:  # noqa: BLE001 -- animação best-effort
        logger.debug("blink_cursor_at falhou: %s", _blink_exc)

    # SESSION-RESUME-01: --resume <id> ou prompt de retomada pós-banner.
    if resume_id:
        from nyx.agent.persistence import load_session_by_id
        from nyx.agent.services.gsd_writer import load_progress_tail

        loaded = load_session_by_id(resume_id)
        if loaded:
            agent._session = loaded
            # NYX-GSD-CHECKPOINTS-01: anexa progress tail ao --resume.
            extra = load_progress_tail(resume_id, n=50)
            if extra:
                loaded.add_user(f"[contexto-anterior]\n{extra}")
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

    # TUI-REDESIGN-28-08c-PARTE-2: switch runtime entre Application e PromptSession.
    # use_application = True quando TTY real + NYX_LEGACY_REPL != "1" + prompt_session
    # disponível. Application full-screen ancora input no rodapé e output rolando
    # acima. NYX_LEGACY_REPL=1 mantém PromptSession (fallback de emergência).
    _legacy_env = os.environ.get("NYX_LEGACY_REPL", "").strip() == "1"
    use_application = (
        sys.stdin.isatty() and not _legacy_env and prompt_session is not None
    )
    repl_app: object | None = None
    repl_output_buffer: object | None = None
    repl_input_buffer: object | None = None
    if use_application:
        try:
            from prompt_toolkit.history import FileHistory as _FH
            from nyx.agent.output import set_repl_app_output
            from nyx.agent.repl_app import append_to_buffer, build_app

            repl_app, repl_output_buffer, repl_input_buffer = build_app(
                app_state=app_state,
                completer=completer,
                history=_FH(str(history_path)),
                last_input_state=last_input_state,
                image_map=image_map,
                image_counter=image_counter,
                prompt_text="  > ",
            )
            # Pre-popula banner no output_buffer: como Application full_screen
            # ocupa toda a tela, o banner impresso anteriormente por print() já
            # foi para o terminal cru — ao entrar em alternate screen ele fica
            # invisível. Reaplicar via append_to_buffer garante presença no topo.
            # TUI-REDESIGN-28-08c-PARTE-3: output_window agora usa
            # FormattedTextControl(ANSI(buffer.text)); banner com escapes ANSI
            # é renderizado COM CORES pelo parser nativo do prompt_toolkit.
            try:
                from nyx.agent.banner import build_banner as _bb
                _banner_str = _bb(model, agent.tools_count, PROJECT_ROOT.name, settings=settings)
                append_to_buffer(repl_output_buffer, _banner_str + "\n")
            except Exception as _bexc:
                logger.debug("pre-populate banner falhou: %s", _bexc)
            # Ativa routing global do _emit para o buffer da Application.
            set_repl_app_output(repl_output_buffer, app_state)
            app_state["repl_app_active"] = True
        except Exception as _aexc:
            logger.warning(
                "Application repl_app indisponível, fallback PromptSession: %s",
                _aexc,
            )
            use_application = False
            repl_app = None
            repl_output_buffer = None
            repl_input_buffer = None
            app_state["repl_app_active"] = False

    while True:
        try:
            ctx_info = agent.get_context_info()
            app_state["ctx_pct"] = int(ctx_info.get("pct", 0) * 100)
            app_state["total_tokens"] = ctx_info.get("total_tokens", 0)
            app_state["max_tokens"] = ctx_info.get("max_tokens", 0)
            app_state["iter_n"] = agent.session.iteration
            app_state["reads"] = agent.session.files_read_count
            app_state["mods"] = agent.session.files_modified_count
            # TUI-REDESIGN-27-02: prompt customizado com nome + template opcional.
            # Default: "  > {nome} " (mockup-faithful). NYX_PROMPT_TEMPLATE
            # aceita placeholders {user_name}/{schema}/{model}; rejeita
            # template com escape ANSI inline (anti-injection).
            _u_name = str(app_state.get("user_display_name") or "visitante")
            _schema_now = os.environ.get("NYX_SCHEMA", "hybrid")
            _model_now = os.environ.get("NYX_MODEL", "qwen2.5-coder:3b")
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
            prompt_str = f"  {ACCENT}{BOLD}{_body}{NC} "
            if use_application and repl_app is not None and repl_input_buffer is not None:
                # TUI-REDESIGN-28-08c-PARTE-2: roda mesmo Application a cada turno.
                # accept_handler chama app.exit(result=text); reset entre iterações
                # via run_async() interno faz self.reset(). Input limpo manualmente
                # para evitar re-submit do texto anterior.
                prefill = str(app_state.pop("prefill", "") or "")
                if prefill:
                    repl_input_buffer.text = prefill
                    repl_input_buffer.cursor_position = len(prefill)
                else:
                    repl_input_buffer.text = ""
                    repl_input_buffer.cursor_position = 0
                _raw_result = await repl_app.run_async()  # type: ignore[attr-defined]
                if _raw_result is None:
                    raise EOFError()
                user_input = str(_raw_result).strip()
                # Limpa input para próxima iteração (Application reusa o buffer).
                repl_input_buffer.text = ""
                repl_input_buffer.cursor_position = 0
            elif prompt_session:
                from prompt_toolkit.formatted_text import ANSI as _ANSI
                # UX-EXTRA-01: prefill via /edit pré-popula próximo prompt_async.
                prefill = str(app_state.pop("prefill", "") or "")
                user_input = (
                    await prompt_session.prompt_async(_ANSI(prompt_str), default=prefill)
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
            # TUI-REDESIGN-28-08c-PARTE-2: pular em Application (input no buffer
            # não gera eco no stdout; \033[1A corromperia output_buffer/banner).
            if sys.stdout.isatty() and not app_state.get("repl_app_active"):
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
                # SUDO-MODE-01: wipe da senha cacheada no /quit.
                try:
                    from nyx.agent.tools import sudo_session as _sudo_quit
                    _sudo_quit.wipe()
                except Exception as _exc:  # noqa: BLE001 -- shutdown best-effort
                    logger.debug("sudo wipe best-effort falhou: %s", _exc)
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

            # INFRA-CLI-SPLIT-02: handlers de sentinela ficam em cli_handlers.py.
            # ctx carrega refs ao agente + estado + cores; handlers retornam
            # True se reconheceram o sentinel, False caso contrário.
            handler_ctx = HandlerCtx(
                result=result,
                agent=agent,
                app_state=app_state,
                project_root_path=PROJECT_ROOT,
                last_input_state=last_input_state,
                use_rich=use_rich,
                output=output,
                print_error=_print_error,
                accent=ACCENT,
                primary=PRIMARY,
                dim=DIM,
                success=SUCCESS,
                nc=NC,
            )

            # Caminho rápido síncrono primeiro (a maioria dos sentinels).
            if dispatch_sync(handler_ctx):
                # /cd pode trocar project_root via mutação do agent + app_state.
                new_pr = app_state.pop("__cd_new_root__", None)
                if isinstance(new_pr, str):
                    project_root = new_pr
                continue

            # TUI-REDESIGN-27-03: 3 modais radiolist para escolha interativa.
            if result in ("__aesthetic_select__", "__schema_select__", "__theme_select__"):
                try:
                    from prompt_toolkit.shortcuts import radiolist_dialog
                except ImportError:
                    _print_error(
                        "prompt_toolkit indisponível para modal interativo.",
                        hint="Use /aesthetic set <id> (ou /schema set / /theme <id>).",
                    )
                    continue

                kind = result.replace("__", "").replace("_select", "")
                title = {"aesthetic": "Aesthetic", "schema": "Schema", "theme": "Theme"}.get(kind, kind)
                values: list[tuple[str, str]] = []
                default_val: str | None = None
                if kind == "aesthetic":
                    from nyx.themes.design_tokens_extended import list_aesthetics
                    default_val = str(app_state.get("aesthetic_id") or os.environ.get("NYX_AESTHETIC", "default"))
                    values = [(a["id"], f"{a['name']} -- {a['tagline']}") for a in list_aesthetics()]
                elif kind == "schema":
                    from nyx.themes.design_tokens_extended import list_schemas, DEFAULT_SCHEMA
                    default_val = str(app_state.get("schema_id") or os.environ.get("NYX_SCHEMA", DEFAULT_SCHEMA))
                    values = [
                        (s["id"], f"{s['id']} -- case {s['heading_case']} · user {s['user_bubble']}")
                        for s in list_schemas()
                    ]
                elif kind == "theme":
                    try:
                        from nyx.themes import ThemeManager
                        _tm = ThemeManager()
                        default_val = str(app_state.get("theme_id") or "nyx")
                        values = [
                            (t["id"], f"{t.get('name', t['id'])} -- {t.get('description', '').strip()[:60]}")
                            for t in _tm.list_themes()
                        ]
                    except Exception as exc:
                        _print_error(f"ThemeManager indisponível: {exc}")
                        continue

                if not values:
                    _print_error(f"Sem opções para {kind}.")
                    continue

                try:
                    choice = await radiolist_dialog(
                        title=title,
                        text="Use as setas para navegar, Enter para confirmar, Esc para cancelar.",
                        values=values,
                        default=default_val,
                        style=build_prompt_style(),
                    ).run_async()
                except Exception as exc:  # noqa: BLE001 -- modal best-effort
                    _print_error(
                        f"Modal {kind} falhou: {exc}",
                        hint=f"Use /{kind} set <id> como fallback.",
                    )
                    continue

                if not choice:
                    print(f"  {DIM}/{kind} select cancelado{NC}")
                    continue

                if kind == "aesthetic":
                    app_state["aesthetic_id"] = choice
                    os.environ["NYX_AESTHETIC"] = choice
                elif kind == "schema":
                    app_state["schema_id"] = choice
                    os.environ["NYX_SCHEMA"] = choice
                elif kind == "theme":
                    app_state["theme_id"] = choice
                print(f"  {SUCCESS} {kind}{NC}: {choice} (próxima invocação aplica)")
                continue

            # Handlers async (MCP).
            if await dispatch_async(handler_ctx):
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
                # TUI-REDESIGN-28-08c-PARTE-2: clear ANSI só em legacy stdout.
                if not app_state.get("repl_app_active"):
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
            # TUI-REDESIGN-28-08c-PARTE-2: clear ANSI só em legacy stdout. No
            # Application, append_to_buffer recebe texto puro; sequência cursor
            # corromperia o output_buffer.
            if not app_state.get("repl_app_active"):
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
    # SUDO-MODE-01: garantia final de wipe. Cobre Ctrl+D, EOF e exceptions
    # que pulam o /quit explícito. Idempotente: wipe sem cache vira no-op.
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

    # PROJECT-ROOTS-MULTI-01: mesma inicialização do REPL para sandbox.
    try:
        from nyx.agent.tools.base import add_extra_root, set_active_project_root

        set_active_project_root(str(PROJECT_ROOT))
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

        # PROJECT-ROOTS-MULTI-01: aceita slash command direto em headless.
        # Conveniência para scripts/testes (ex.: smoke do spec) que enviam
        # "/sandbox list" sem encapsular em JSON. Resposta sai como linha
        # de output cru (mesma semântica do REPL).
        if line.startswith("/"):
            from nyx.agent.commands import handle_command

            cmd_result = handle_command(line, project_root)
            if cmd_result is None:
                continue
            if cmd_result == "__sandbox_list__":
                from nyx.agent.tools.base import (
                    get_active_project_root,
                    list_extra_roots,
                )
                active = get_active_project_root() or PROJECT_ROOT
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
                active = get_active_project_root() or PROJECT_ROOT
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
                    old_root = get_active_project_root() or PROJECT_ROOT
                    new_root = set_active_project_root(cand)
                    add_extra_root(old_root)
                    project_root = str(new_root)
                    agent._project_root = project_root
                    agent._tools.project_root = project_root
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
        # ONBOARDING-01 + TUI-REDESIGN-28-05: wizard de primeiro uso (7 passos)
        # antes do REPL: nome + aesthetic + entity + schema + banner + model + auto_approve.
        from nyx.agent.onboarding import (
            mark_done as _mark_onboarding_done,
            run_first_run_wizard,
            should_run_tutorial,
        )

        if should_run_tutorial(args.skip_onboarding):
            run_first_run_wizard()
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
