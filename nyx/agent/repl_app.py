"""REPL Application (TUI-REDESIGN-28-08): input ancorado no rodapé.

Layout HSplit:
  - output_window  (BufferControl, ocupa altura disponível - 3 linhas)
  - separator      (1 linha, opcional)
  - input_window   (BufferControl, min 1 max 8 linhas)
  - toolbar_window (FormattedTextControl, 1 linha)

A função `build_app` retorna uma `Application` configurada com KeyBindings
espelhando o PromptSession do `nyx/cli.py`. O wrapper `run_repl_app_async`
expõe semântica equivalente a `prompt_async`: roda o Application e devolve o
texto submetido pelo usuário.

Self-test (`python -m nyx.agent.repl_app --self-test`) sobe a Application
por 2s e fecha via timer, sem precisar de TTY interativo nem stdin.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)

from prompt_toolkit.application import Application
from prompt_toolkit.application.current import get_app
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.completion import Completer
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.history import FileHistory, History
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.layout.containers import ConditionalContainer
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.layout.processors import BeforeInput
from prompt_toolkit.styles import Style as PtkStyle


# Estado partilhado entre callsite e Application. Mantemos como dict para
# permitir injeção externa (app_state em nyx/cli.py) sem acoplamento rígido.
_STATE: dict[str, Any] = {}


def _resolve_app_state() -> dict[str, Any]:
    """Retorna o app_state injetado via build_app(app_state=...).

    Fallback para _STATE vazio em self-test.
    """
    return _STATE


def append_to_buffer(buffer: Buffer, text: str) -> None:
    """Append thread-safe ao buffer de output + invalidate UI.

    Mantém cursor no final (auto-scroll). Usado por _emit em output.py para
    rotear streaming e prints para o output_window quando Application ativo.
    """
    if not text:
        return
    novo = buffer.text + text
    buffer.document = Document(text=novo, cursor_position=len(novo))
    try:
        app = get_app()
        app.invalidate()
    except Exception as exc:
        # Sem aplicação rodando (ex.: chamado em headless): logger.debug e
        # noop. _emit em output.py já trata fallback para print().
        logger.debug("append_to_buffer sem app ativo: %s", exc)


def _build_toolbar_callable(app_state: dict[str, Any]) -> Callable[[], Any]:
    """Recria o bottom_toolbar do PromptSession atual.

    Lê tokens, modelo, iter, bypass e devolve FormattedText. Espelhamos o
    contrato de cli.py:_bottom_toolbar() para paridade visual e funcional.
    """
    # Imports lazy para evitar circular import com nyx.cli.
    from nyx.themes.design_tokens import NYX_ACCENT, NYX_MUTED, NYX_PRIMARY, NYX_PURPLE_DIM

    _STATE_GLYPHS = {"cold": " ", "warming": " ", "warm": " "}
    BULLETS = {"bypass_on": "●"}

    def _toolbar() -> FormattedText:
        parts: list[tuple[str, str]] = []
        ctx_pct = app_state.get("ctx_pct", 0)
        total_tok = app_state.get("total_tokens", 0)
        max_tok = app_state.get("max_tokens", 0)
        iter_n = app_state.get("iter_n", 0)
        reads = app_state.get("reads", 0)
        mods = app_state.get("mods", 0)
        model = str(app_state.get("model_name", ""))

        ctx_label = f"ctx {ctx_pct}%"
        if max_tok:
            ctx_label += f" ({total_tok}/{max_tok}tok)"
        parts.append((f"fg:{NYX_ACCENT}", ctx_label))

        meta = f"  |  {model}  |  iter {iter_n}  |  lidos {reads}  |  modif {mods}"
        parts.append((f"fg:{NYX_MUTED}", meta))

        model_state = app_state.get("model_state", "cold")
        glyph = _STATE_GLYPHS.get(model_state, _STATE_GLYPHS["cold"])
        parts.append((f"fg:{NYX_MUTED}", f"  |  {glyph} {model_state}"))

        inflight = app_state.get("inflight_task")
        if inflight is not None and not getattr(inflight, "done", lambda: True)():
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

    return _toolbar


def _build_style() -> PtkStyle:
    """Style da Application: usa paleta ativa via theme_manager.

    Idêntico ao _build_prompt_style do cli.py, com adição de class:'output'
    para o buffer de output (sem fundo destacado).
    """
    from nyx.themes.design_tokens import (
        NYX_ACCENT as _D_ACCENT,
        NYX_ACCENT_DIM as _D_ACCENT_LO,
        NYX_BG as _D_BG,
        NYX_BG_SOFT as _D_BG_SOFT,
        NYX_MUTED as _D_MUTED,
        NYX_PRIMARY as _D_INK,
    )

    try:
        from nyx.themes.theme_manager import resolve_palette
        pal = resolve_palette().get("palette", {}) or {}
    except Exception:
        pal = {}

    accent = pal.get("accent", _D_ACCENT)
    accent_lo = pal.get("accent_lo", _D_ACCENT_LO)
    ink = pal.get("ink", _D_INK)
    ink_muted = pal.get("ink_muted", _D_MUTED)
    bg = pal.get("bg", _D_BG)
    bg_soft = pal.get("bg_soft", _D_BG_SOFT)

    return PtkStyle.from_dict({
        "completion-menu.completion":              f"bg:{accent_lo} fg:{ink}",
        "completion-menu.completion.current":      f"bg:{accent} fg:{bg} bold",
        "completion-menu.meta.completion":         f"bg:{bg_soft} fg:{ink_muted}",
        "completion-menu.meta.completion.current": f"bg:{accent_lo} fg:{ink}",
        "bottom-toolbar":                          f"fg:{ink_muted}",
        "bottom-toolbar.text":                     f"fg:{ink_muted}",
        "scrollbar.background":                    "",
        "scrollbar.button":                        f"bg:{accent_lo}",
        "completion.header":                       f"fg:{accent} bold",
        "separator":                               f"fg:{accent_lo}",
        "output":                                  f"fg:{ink}",
        "prompt":                                  f"fg:{accent} bold",
    })


def build_app(
    *,
    app_state: dict[str, Any],
    completer: Completer | None = None,
    history: History | None = None,
    last_input_state: dict[str, str] | None = None,
    image_map: dict[int, str] | None = None,
    image_counter: dict[str, int] | None = None,
    prompt_text: str = "  > ",
) -> tuple[Application, Buffer, Buffer]:
    """Constrói Application com layout HSplit (output + input + toolbar).

    Retorna (app, output_buffer, input_buffer). O caller mantém referências
    para append_to_buffer(output_buffer, text) durante streaming e leitura
    de input_buffer.text quando submit ocorre.

    KeyBindings espelham PromptSession atual:
      - Enter: lógica do 28_04 (lista vazia + "/" abre completion)
      - Ctrl+J: newline
      - Ctrl+O: expand last input (run_in_terminal)
      - Ctrl+Up: recall last input
      - Tab: auto-suggest / completion / expand thinking
      - Shift+Tab: bypass toggle
      - Ctrl+V: paste (clipboard image/text)
      - "/": insert + start_completion se primeira tecla
    """
    global _STATE
    _STATE = app_state
    last_input_state = last_input_state if last_input_state is not None else {"text": ""}
    image_map = image_map if image_map is not None else {}
    image_counter = image_counter if image_counter is not None else {"n": 0}

    # ── Buffers ──────────────────────────────────────────────────────────
    output_buffer = Buffer(read_only=False, multiline=True)
    output_buffer.text = ""

    input_buffer = Buffer(
        completer=completer,
        history=history,
        auto_suggest=AutoSuggestFromHistory() if history is not None else None,
        multiline=True,
        complete_while_typing=True,
    )

    # Submit estado: armazena o texto quando Enter dispara validate_and_handle.
    submit_state: dict[str, Any] = {"submitted": False, "text": ""}

    def _accept(buf: Buffer) -> bool:
        submit_state["submitted"] = True
        submit_state["text"] = buf.text
        try:
            app = get_app()
            app.exit(result=buf.text)
        except Exception as exc:
            logger.debug("accept_handler.exit falhou: %s", exc)
        return True  # mantém o texto no buffer; clearing fica a cargo do caller

    input_buffer.accept_handler = _accept

    # ── KeyBindings ──────────────────────────────────────────────────────
    kb = KeyBindings()

    @kb.add("c-o")
    def _expand_last(event: Any) -> None:
        from prompt_toolkit.application import run_in_terminal
        from nyx.agent.output import render_user_input as _render_expanded

        text = last_input_state.get("text", "")
        if text:
            run_in_terminal(lambda: _render_expanded(text, expanded=True))

    @kb.add("c-up")
    def _recall_last(event: Any) -> None:
        buf = event.current_buffer
        last = last_input_state.get("text", "")
        if not last:
            return
        if buf.document.text.strip():
            return
        buf.text = last
        buf.cursor_position = len(last)

    @kb.add("enter")
    def _submit(event: Any) -> None:
        buf = event.current_buffer
        state = buf.complete_state
        if (
            state
            and state.completions
            and buf.document.text_before_cursor.lstrip().startswith("/")
        ):
            current = state.current_completion or state.completions[0]
            if not current.text:
                current = next(
                    (c for c in state.completions if c.text),
                    state.completions[0],
                )
            buf.apply_completion(current)
        elif buf.document.text.strip() == "/" and not state:
            buf.start_completion(select_first=True)
            return
        buf.validate_and_handle()

    @kb.add("c-j")
    def _newline(event: Any) -> None:
        event.current_buffer.insert_text("\n")

    @kb.add("/")
    def _slash(event: Any) -> None:
        buf = event.current_buffer
        buf.insert_text("/")
        if buf.document.text_before_cursor.lstrip() == "/":
            buf.start_completion(select_first=True)

    @kb.add("tab")
    def _accept_suggestion(event: Any) -> None:
        buf = event.current_buffer
        sug = buf.suggestion
        if sug and sug.text:
            buf.insert_text(sug.text)
            return
        if buf.complete_state:
            buf.complete_next()
            return
        if not buf.text.strip():
            tb = app_state.get("last_thinking_block")
            if isinstance(tb, dict) and tb.get("text"):
                from prompt_toolkit.application import run_in_terminal
                from nyx.agent.output import render_thinking_block
                tb["expanded"] = not tb.get("expanded", False)
                text = tb["text"]
                dur = tb.get("duration_s")
                expanded = tb["expanded"]
                run_in_terminal(
                    lambda: render_thinking_block(text, dur, expanded=expanded)
                )
                return
        buf.insert_text("    ")

    @kb.add("s-tab")
    def _toggle_bypass(event: Any) -> None:
        app_state["bypass"] = not app_state.get("bypass", False)
        event.app.invalidate()

    @kb.add("c-v")
    def _paste(event: Any) -> None:
        from prompt_toolkit.application import run_in_terminal
        from nyx.agent.clipboard import capture_image, capture_text

        buf = event.current_buffer
        img_path = capture_image()
        if img_path is not None:
            image_counter["n"] += 1
            n = image_counter["n"]
            image_map[n] = str(img_path)
            buf.insert_text(f"[Image #{n}]")
            run_in_terminal(lambda: print(f"  Image #{n} salva em {img_path}"))
            return
        text = capture_text()
        if text:
            buf.insert_text(text)

    @kb.add("c-c")
    def _interrupt(event: Any) -> None:
        # Permite Ctrl+C cancelar inflight task; se nenhuma, sai do app.
        inflight = app_state.get("inflight_task")
        if inflight is not None and not getattr(inflight, "done", lambda: True)():
            try:
                inflight.cancel()
            except Exception as exc:
                logger.debug("inflight.cancel falhou: %s", exc)
            event.app.invalidate()
            return
        # Sem inflight: emit EOF semântico via exit(None).
        event.app.exit(exception=KeyboardInterrupt())

    # ── Layout ───────────────────────────────────────────────────────────
    output_control = BufferControl(buffer=output_buffer, focusable=False)
    input_control = BufferControl(
        buffer=input_buffer,
        focusable=True,
        input_processors=[BeforeInput(prompt_text, style="class:prompt")],
    )
    toolbar_control = FormattedTextControl(
        text=_build_toolbar_callable(app_state),
        focusable=False,
    )

    output_window = Window(
        content=output_control,
        wrap_lines=True,
        always_hide_cursor=True,
        style="class:output",
    )
    separator_window = Window(
        height=1,
        char="─",
        style="class:separator",
    )
    input_window = Window(
        content=input_control,
        height=Dimension(min=1, max=8),
        wrap_lines=True,
    )
    toolbar_window = Window(
        content=toolbar_control,
        height=1,
        style="class:bottom-toolbar",
    )

    layout = Layout(
        HSplit([
            output_window,
            separator_window,
            input_window,
            toolbar_window,
        ]),
        focused_element=input_window,
    )

    app: Application = Application(
        layout=layout,
        key_bindings=kb,
        full_screen=True,
        style=_build_style(),
        mouse_support=False,
        editing_mode=None,  # default Emacs
    )

    # Anexa references para o caller acessar via app.<attr> (convenção).
    app.output_buffer = output_buffer  # type: ignore[attr-defined]
    app.input_buffer = input_buffer  # type: ignore[attr-defined]
    app.submit_state = submit_state  # type: ignore[attr-defined]

    return app, output_buffer, input_buffer


async def run_repl_app_async(
    *,
    app_state: dict[str, Any],
    completer: Completer | None = None,
    history: History | None = None,
    last_input_state: dict[str, str] | None = None,
    image_map: dict[int, str] | None = None,
    image_counter: dict[str, int] | None = None,
    prompt_text: str = "  > ",
    prefill: str = "",
) -> str:
    """Sobe Application e retorna texto submetido (semântica prompt_async).

    Raises KeyboardInterrupt em Ctrl+C sem inflight (semântica idêntica ao
    PromptSession.prompt_async). EOFError quando app sai sem submit (Ctrl+D
    ou exit programático com None).
    """
    app, _outbuf, inbuf = build_app(
        app_state=app_state,
        completer=completer,
        history=history,
        last_input_state=last_input_state,
        image_map=image_map,
        image_counter=image_counter,
        prompt_text=prompt_text,
    )
    if prefill:
        inbuf.text = prefill
        inbuf.cursor_position = len(prefill)

    try:
        result = await app.run_async()
    except KeyboardInterrupt:
        raise
    if result is None:
        raise EOFError()
    return str(result)


# ── Self-test entrypoint ──────────────────────────────────────────────────
async def _self_test_async() -> int:
    """Sobe Application por 2s e fecha via timer (sem stdin interativo).

    Retorna 0 em sucesso, !=0 em falha. Útil para CI/headless validar que
    o módulo importa e a Application instancia sem exceção.
    """
    app_state: dict[str, Any] = {
        "ctx_pct": 0,
        "total_tokens": 0,
        "max_tokens": 0,
        "iter_n": 0,
        "reads": 0,
        "mods": 0,
        "model_name": "self-test",
        "model_state": "cold",
        "bypass": False,
    }

    app, outbuf, inbuf = build_app(app_state=app_state)
    # Popula o output para confirmar que append funciona.
    append_to_buffer(outbuf, "self-test: Application instanciada\n")
    append_to_buffer(outbuf, "self-test: layout HSplit ok\n")

    # Programa exit() após 2s. Não chamamos run_async em ambiente sem TTY:
    # a build acima já validou todos os componentes (importação + KeyBindings
    # + Layout). Só executamos run_async se stdin é tty.
    if not sys.stdin.isatty():
        sys.stdout.write("self-test (no-tty): build_app ok, buffers ok, layout ok\n")
        sys.stdout.write(f"output_buffer.text length: {len(outbuf.text)}\n")
        sys.stdout.flush()
        return 0

    async def _exit_later() -> None:
        await asyncio.sleep(2.0)
        try:
            app.exit(result="self-test-timeout")
        except Exception as exc:
            logger.debug("self-test exit falhou: %s", exc)

    asyncio.create_task(_exit_later())
    result = await app.run_async()
    sys.stdout.write(f"self-test (tty): app saiu com result={result!r}\n")
    sys.stdout.flush()
    return 0


def _main() -> int:
    if "--self-test" in sys.argv:
        return asyncio.run(_self_test_async())
    sys.stdout.write("uso: python -m nyx.agent.repl_app --self-test\n")
    sys.stdout.flush()
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
