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
from nyx.themes.design_tokens import (  # noqa: E402
    STATE_GLYPHS as _STATE_GLYPHS,
)

ACCENT = ANSI_ACCENT_FG
PRIMARY = ANSI_PRIMARY_FG
DIM = ANSI_DIM
BOLD = ANSI_BOLD
SUCCESS = ANSI_SUCCESS_FG
NC = ANSI_RESET


# Glifos do estado do modelo (UX-BUG-02B) -- fonte única em design_tokens.STATE_GLYPHS
# (TUI-STATE-GLYPHS-SYNC-06). Círculos da faixa Geometric Shapes ○ ◐ ● (U+25CB/D0/CF)
# -- não são emoji. NÃO remover via sanitizer global: invariante #14 protege.
# Literais aqui em comentário garantem o segundo escudo do invariante #14
# (cli.py precisa ter >=1 de cada glifo canônico para preservar a proteção
# anti-sanitizer mesmo após consolidação do dict em design_tokens).


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
from nyx.agent.output import redirect_stdout_to_emit  # noqa: E402

# INFRA-CLI-SPLIT-03: run_headless + boot pieces saem para módulos próprios.
# Re-exports preservam compatibilidade (`from nyx.cli import run_headless`).
from nyx.cli_boot import (  # noqa: E402
    compute_prompt_str,
    init_sandbox_roots,
    render_quit_card,
    run_quit_shutdown,
    run_select_modal,
    shutdown_repl,
)
from nyx.cli_callbacks import build_render_callbacks  # noqa: E402
from nyx.cli_handlers import HandlerCtx, dispatch_async, dispatch_sync  # noqa: E402
from nyx.cli_headless import run_headless  # noqa: E402, F401 -- re-export

# INFRA-CLI-SPLIT-01: helpers movidos para nyx/cli_helpers.py (mantemos re-export).
from nyx.cli_helpers import (  # noqa: E402
    _expand_images,
    _persist_image_index,
)
from nyx.cli_helpers import maybe_offer_resume as _maybe_offer_resume_impl  # noqa: E402

# INFRA-CLI-SPLIT-02: KeyBindings, bottom toolbar e dispatcher de sentinelas
# saíram para módulos dedicados. cli.py orquestra agora.
from nyx.cli_keybindings import (  # noqa: E402
    build_bottom_toolbar,
    build_keybindings,
    build_prompt_style,
)

if TYPE_CHECKING:
    pass


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
    from nyx.config.settings import load_settings

    settings = load_settings()

    # PROJECT-ROOTS-MULTI-01: inicialização extraída para cli_boot.py
    # (INFRA-CLI-SPLIT-03). Sandbox preserva strictness (não autoriza fantasmas).
    init_sandbox_roots(settings, PROJECT_ROOT, logger)

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

    from nyx.agent.output import (
        build_warming_label,
        nyx_spinner,
        render_assistant_end,
        render_assistant_start,
        render_user_input,
    )

    # STREAMING-SIDE-RULE-01: estado da faixa lateral entre flushes.
    # TUI-REDESIGN-25-10: tool_args_cache mantém args entre on_tool e on_tool_result.
    side_rule_state: dict = {}
    tool_timers: dict[str, float] = {}
    tool_args_cache: dict[str, dict] = {}

    # INFRA-CLI-SPLIT-03: callbacks de render extraídos para cli_callbacks.
    # agent_ref é mutável para permitir closure capturar agent (instanciado abaixo).
    agent_ref: list = [None]
    callbacks = build_render_callbacks(
        agent_ref=agent_ref,
        app_state=app_state,
        spinner_state=spinner_state,
        turn_state=turn_state,
        side_rule_state=side_rule_state,
        tool_timers=tool_timers,
        tool_args_cache=tool_args_cache,
        project_root=PROJECT_ROOT,
    )
    _stop_spinner = callbacks["stop_spinner"]
    _flush_buffer = callbacks["flush_buffer"]

    agent = AgentLoop(
        project_root=project_root,
        proxy_url=proxy_url,
        model=model,
        on_token=callbacks["on_token"] if streaming else None,
        on_tool=callbacks["on_tool"],
        on_tool_result=callbacks["on_tool_result"],
        on_permission=_make_ask_permission(app_state),
        on_compaction=callbacks["on_compaction"],
        on_model_state=callbacks["on_model_state"],
        on_thinking=callbacks["on_thinking"],
        streaming=streaming,
        settings=settings,
    )
    agent_ref[0] = agent

    # TUI-BANNER-DEDUP-02: detecta cedo qual caminho será usado (Application vs
    # PromptSession legacy) para condicionar o banner cru + blink async ao
    # fallback legacy. No caminho Application (default), o banner aparece via
    # append_to_buffer dentro do alternate-screen (linhas mais abaixo),
    # eliminando o "banner fantasma" pré-render. Detecção definitiva (com
    # eventual fallback se build_app falhar) acontece no bloco principal abaixo.
    _legacy_env = os.environ.get("NYX_LEGACY_REPL", "").strip() == "1"
    use_application = (
        sys.stdin.isatty() and not _legacy_env and prompt_session is not None
    )

    if not use_application:
        # Caminho legacy PromptSession (NYX_LEGACY_REPL=1 ou stdin não-TTY):
        # banner cru no stdout + blink async ~1.4s — único momento que o
        # usuário verá o banner, pois não há alternate-screen para escondê-lo.
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

    _warmup_task = asyncio.create_task(_warmup())  # noqa: F841 -- fire-and-forget, ref viva contra GC
    # UX-BUG-03: rastreamos summarize_task entre turns para cancelar a
    # anterior se ainda não terminou (evita acúmulo) e incluir no shutdown.
    summarize_task: "asyncio.Task | None" = None

    # TUI-INPUT-DEADLOCK-01: a drenagem de stdin via termios.tcflush é executada
    # imediatamente antes do primeiro Application.run_async() (ver _stdin_drained
    # abaixo), e não aqui — passar pelo `await _warmup()` e import-overhead entre
    # esta linha e o run_async() abria janela onde novas keystrokes do cold-start
    # entravam após o flush e eram interpretadas fora de ordem ao trocar para
    # raw mode. UX-BUG-02C original ficava aqui (linha 386); deslocado conforme
    # spec da sprint.
    _stdin_drained = False

    session_start = time.time()
    total_iterations = 0

    # TEXTUAL-CUTOVER-01: dispatch opt-in via NYX_TUI_TEXTUAL=1.
    # Default continua prompt_toolkit (zero regressao); env=1 troca para NyxTUI
    # Textual. Quando ONDA-31 confirmar paridade, este branch vira default.
    # Em caso de qualquer falha (import, runtime), cai para o caminho
    # prompt_toolkit existente -- usuario nunca fica sem REPL.
    _tui_textual = os.environ.get("NYX_TUI_TEXTUAL", "").strip() == "1"
    if use_application and _tui_textual:
        try:
            from nyx.agent.tui.app import NyxTUI

            nyx_tui_app = NyxTUI(
                model=model,
                tools_count=agent.tools_count,
                project_name=PROJECT_ROOT.name,
                slash_completer=[],
                settings=settings,
            )
            tui_result = await nyx_tui_app.run_async()
            if tui_result == "__quit__":
                render_quit_card(agent, app_state, PROJECT_ROOT)
                await run_quit_shutdown(proxy_url, logger)
            return
        except Exception as _texc:  # noqa: BLE001 -- fallback graciso
            logger.warning(
                "NyxTUI opt-in falhou, fallback prompt_toolkit: %s", _texc
            )

    # TUI-REDESIGN-28-08c-PARTE-2: switch runtime entre Application e PromptSession.
    # use_application = True quando TTY real + NYX_LEGACY_REPL != "1" + prompt_session
    # disponível. Application full-screen ancora input no rodapé e output rolando
    # acima. NYX_LEGACY_REPL=1 mantém PromptSession (fallback de emergência).
    # TUI-BANNER-DEDUP-02: detecção foi promovida para antes do banner cru
    # (acima, logo após agent_ref[0] = agent) para condicionar print()+blink ao
    # caminho legacy. Aqui apenas reaproveita a variável já calculada.
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
                app_state["_banner_str"] = _banner_str
            except Exception as _bexc:
                logger.debug("pre-populate banner falhou: %s", _bexc)
                _banner_str = None
            # Ativa routing global do _emit para o buffer da Application.
            set_repl_app_output(repl_output_buffer, app_state)
            app_state["repl_app_active"] = True

            # TUI-BANNER-BLINK-DEFAULT-01: timer asyncio que alterna o cursor
            # do banner entre "|" (chr 0x7C) e " " (espaço) a cada 0.5s,
            # criando o blink visivel. Lição empirica da sprint 187 (revertida
            # pela 193): app.invalidate() global em loop curto durante streaming
            # cria flicker -- por isso o loop PAUSA quando inflight_task esta
            # ativa (race fica neutralizada por design). Cleanup via
            # shutdown_repl (cancela all_tasks com timeout). Necessario chamar
            # app.invalidate() pois FormattedTextControl usa callable lambda
            # que so re-renderiza quando o app sinaliza invalidacao -- a 0.5s
            # com pause-during-streaming, o profile e benigno (vs 187 que
            # invalidava 50ms continuo, incluindo durante stream).
            if _banner_str is not None:
                from prompt_toolkit.document import Document

                _initial_banner_len = len(_banner_str) + 1  # +1 do "\n" final

                async def _banner_blink_loop() -> None:
                    visible = True
                    prev_banner = _banner_str
                    while True:
                        try:
                            await asyncio.sleep(0.5)
                        except asyncio.CancelledError:
                            return
                        inflight = app_state.get("inflight_task")
                        if inflight is not None and not getattr(
                            inflight, "done", lambda: True,
                        )():
                            # Streaming ativo: pula este tick para evitar race
                            # com tokens sendo apendados em paralelo.
                            continue
                        visible = not visible
                        cursor = chr(0x7C) if visible else ""
                        try:
                            new_banner = _bb(
                                model, agent.tools_count, PROJECT_ROOT.name,
                                settings=settings, cursor=cursor,
                            )
                        except Exception as _exc:  # noqa: BLE001 -- blink best-effort
                            logger.debug("blink rebuild banner falhou: %s", _exc)
                            continue
                        # Replace cirurgico do prefixo: assume banner sempre
                        # no inicio do output_buffer (pre-populado em boot).
                        # Comprimento do banner anterior pode mudar entre
                        # frames (cursor "|" vs " " tem mesma largura em
                        # _build_compact/_build_wide gracas a defesa em
                        # banner.py); usamos len(prev_banner)+1 (com "\n").
                        try:
                            current = repl_output_buffer.text
                            prefix_len = len(prev_banner) + 1
                            if current.startswith(prev_banner):
                                suffix = current[prefix_len:]
                                novo = new_banner + "\n" + suffix
                                repl_output_buffer.document = Document(
                                    text=novo, cursor_position=len(novo),
                                )
                                prev_banner = new_banner
                                # FormattedTextControl usa callable; precisa
                                # de invalidate para chamar _ansi_output() de
                                # novo e re-parsear ANSI escapes do banner.
                                # Sem renderer.clear(), delta-rendering do
                                # prompt_toolkit assume append-only e deixa o
                                # banner antigo na tela com o novo overlaid
                                # com offset -- vide debug 2026-05-25 18:25.
                                try:
                                    from prompt_toolkit.application import (
                                        get_app as _get_app,
                                    )
                                    _app = _get_app()
                                    try:
                                        _app.renderer.clear()
                                    except Exception as _cexc:  # noqa: BLE001
                                        logger.debug(
                                            "blink renderer.clear falhou: %s",
                                            _cexc,
                                        )
                                    _app.invalidate()
                                except Exception as _iexc:  # noqa: BLE001
                                    logger.debug(
                                        "blink invalidate falhou: %s", _iexc,
                                    )
                        except Exception as _exc:  # noqa: BLE001
                            logger.debug("blink set_document falhou: %s", _exc)

                _banner_blink_task = asyncio.create_task(_banner_blink_loop())
                app_state["_banner_blink_task"] = _banner_blink_task
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
            # TUI-REDESIGN-27-02: prompt customizado extraído para cli_boot.py
            # (INFRA-CLI-SPLIT-03). Default "  > {nome} " (mockup-faithful).
            prompt_str = compute_prompt_str(app_state, ACCENT, BOLD, NC)
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
                # TUI-INPUT-DEADLOCK-01: drena stdin no primeiro turno, imediatamente
                # antes de transferir controle pro prompt_toolkit. Idempotente via
                # _stdin_drained: rodar a cada iteração descartaria keystrokes
                # válidas digitadas entre turns. Em não-tty, branch noop silencioso.
                if not _stdin_drained and sys.stdin.isatty():
                    try:
                        import termios
                        try:
                            termios.tcflush(sys.stdin.fileno(), termios.TCIFLUSH)
                        except (termios.error, OSError) as exc:
                            logger.warning("termios.tcflush pré-run_async falhou: %s", exc)
                    except ImportError as exc:
                        logger.debug("termios indisponível (plataforma não-POSIX): %s", exc)
                    _stdin_drained = True
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

        # TUI-CTRL-Q-OLLAMA-STOP-04: Application.exit(result="__quit__") via
        # Ctrl+Q chega aqui como string literal (não passa por handle_command).
        # Redireciona pro mesmo fluxo do /quit: card + shutdown ordenado.
        if user_input == "__quit__":
            render_quit_card(agent, app_state, PROJECT_ROOT)
            await run_quit_shutdown(proxy_url, logger)
            break

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
                # INFRA-CLI-SPLIT-03: card + wipe + admin/shutdown saíram para cli_boot.
                render_quit_card(agent, app_state, PROJECT_ROOT)
                await run_quit_shutdown(proxy_url, logger)
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

            # TUI-SLASH-DISPATCH-INVESTIGATE-01: handlers em cli_handlers.py
            # e RichOutput escrevem via print()/Console.print() em sys.stdout.
            # Em modo Application (full_screen=True), stdout fica oculto pela
            # tela do prompt_toolkit. redirect_stdout_to_emit() roteia para
            # output_buffer enquanto o dispatch slash executa. No-op fora de
            # Application mode (mantém semântica legacy/PromptSession/headless).
            with redirect_stdout_to_emit():
                # Caminho rápido síncrono primeiro (a maioria dos sentinels).
                if dispatch_sync(handler_ctx):
                    # /cd pode trocar project_root via mutação do agent + app_state.
                    new_pr = app_state.pop("__cd_new_root__", None)
                    if isinstance(new_pr, str):
                        project_root = new_pr
                    continue

                # TUI-REDESIGN-27-03: modal radiolist movido para cli_boot.run_select_modal.
                if result in ("__aesthetic_select__", "__schema_select__", "__theme_select__"):
                    kind = result.replace("__", "").replace("_select", "")
                    await run_select_modal(
                        kind, app_state, build_prompt_style, _print_error,
                        DIM, SUCCESS, NC,
                    )
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
            # TUI-NYX-SOFT-BOX-01: body_text consolidado materializa o box
            # roxo antes do footer (simetria com user box turquesa). Streamed
            # tem precedência (já vimos a resposta linha-a-linha durante o
            # turno); summary é fallback quando turno foi puramente tool calls
            # sem stream textual.
            _body_for_box: str | None = streamed or summary or None
            render_assistant_end(
                start_monotonic=request_started,
                tokens=_meta_tokens,
                body_text=_body_for_box,
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

    # INFRA-CLI-SPLIT-03: shutdown ordenado movido para cli_boot.shutdown_repl.
    # Wipe sudo + cancel pending tasks + Analytics.end_session + save_session.
    saved = await shutdown_repl(agent, analytics_ref, PROJECT_ROOT, logger)
    if saved:
        # DEPLOY-02 absorve O-04: feedback verde + path + dica /resume.
        from nyx.themes.design_tokens import ANSI_SUCCESS_FG

        print(f"\n  {ANSI_SUCCESS_FG} sessão salva{ANSI_RESET}")
        print(f"  {DIM}  {saved.resolve()}{NC}")
        print(f"  {DIM}  use /resume na próxima abertura para retomar{NC}")
    return 0


def main() -> None:
    # TUI-SIGINT-RECLAIM-07: removido `signal.signal(SIGINT, lambda *_: None)`.
    # Motivo: imports pesados (torch transitivo, prompt_toolkit, nyx.agent.*) já
    # ocorreram no topo do módulo antes de main() rodar; o masking aqui só
    # cobria argparse + bifurcação rápida e ficava ativo a sessão inteira,
    # neutralizando Ctrl+C durante warmup (cleanup_old_sessions, memory.index)
    # antes da Application/PromptSession assumir o terminal.
    # Headless instala seu próprio handler em cli_headless.py:96.
    # REPL deixa prompt_toolkit instalar via loop.add_signal_handler.
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
        sys.exit(asyncio.run(run_headless(PROJECT_ROOT, logger)))
    else:
        # ONBOARDING-01 + TUI-REDESIGN-28-05: wizard de primeiro uso (7 passos)
        # antes do REPL: nome + aesthetic + entity + schema + banner + model + auto_approve.
        from nyx.agent.onboarding import (
            mark_done as _mark_onboarding_done,
        )
        from nyx.agent.onboarding import (
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
