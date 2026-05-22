"""KeyBindings, bottom toolbar e prompt style extraídos de nyx/cli.py.

INFRA-CLI-SPLIT-02: fatorar peças do REPL que não dependem do AgentLoop
nem do laço de turnos, mantendo `run_repl` mais enxuto.

Cada factory recebe os refs mutáveis (`app_state`, `image_map`, etc.)
e devolve a peça pronta — sem efeitos colaterais até a chamada real
dos handlers do prompt_toolkit. Importações pesadas de prompt_toolkit
acontecem dentro das funções (boot best-effort: cli.py absorve
ImportError ao montar PromptSession).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
    from prompt_toolkit.key_binding import KeyBindings
    from prompt_toolkit.styles import Style as _PtkStyle


def build_prompt_style() -> "_PtkStyle":
    """TUI-REDESIGN-27-01: Style do prompt_toolkit a partir do theme_manager.

    Mapeia classes (completion-menu, bottom-toolbar, scrollbar) para
    hex da paleta ativa (NYX_AESTHETIC + NYX_ENTITY) via resolve_palette.
    Fallback para constantes de design_tokens.py se theme_manager falhar.
    """
    from prompt_toolkit.styles import Style as _PtkStyle

    from nyx.themes.design_tokens import (
        NYX_ACCENT as _D_ACCENT,
    )
    from nyx.themes.design_tokens import (
        NYX_ACCENT_DIM as _D_ACCENT_LO,
    )
    from nyx.themes.design_tokens import (
        NYX_BG as _D_BG,
    )
    from nyx.themes.design_tokens import (
        NYX_BG_SOFT as _D_BG_SOFT,
    )
    from nyx.themes.design_tokens import (
        NYX_MUTED as _D_MUTED,
    )
    from nyx.themes.design_tokens import (
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
    bg_soft = pal.get("bg_soft", _D_BG_SOFT)  # noqa: F841 -- reservado para extensão
    # TUI-REDESIGN-28-09: popup do completion adota bg do terminal
    # (bg:default) para integrar com o fundo, preservando o destaque
    # do item selecionado (.current) com bg:{accent}.
    return _PtkStyle.from_dict({
        "completion-menu.completion":                f"bg:default fg:{ink}",
        "completion-menu.completion.current":        f"bg:{accent} fg:{bg} bold",
        "completion-menu.meta.completion":           f"bg:default fg:{ink_muted}",
        "completion-menu.meta.completion.current":   f"bg:{accent_lo} fg:{ink}",
        "bottom-toolbar":                            f"fg:{ink_muted}",
        "bottom-toolbar.text":                       f"fg:{ink_muted}",
        "scrollbar.background":                      "",
        "scrollbar.button":                          f"bg:{accent_lo}",
        "completion.header":                         f"fg:{accent} bold",
    })


def build_keybindings(
    *,
    app_state: dict[str, Any],
    last_input_state: dict[str, str],
    image_map: dict[int, str],
    image_counter: dict[str, int],
    persist_image_index: Callable[[dict[int, str]], None],
    modes: tuple[str, ...],
    ansi_dim: str,
    ansi_reset: str,
    ansi_success: str,
) -> "KeyBindings":
    """Factory das KeyBindings do REPL.

    Encapsula:
      - Ctrl+O: render do último input expandido (UX-EXTRA-01).
      - Ctrl+Up: recarrega último input no buffer (UX-EXTRA-01).
      - Enter: submit com tratamento de completion popup (UX-CLAUDE-PARITY).
      - Ctrl+J: insere newline literal.
      - "/": abre popup do completer.
      - Tab: aceita sugestão / completion / expand-thinking
        (TUI-REDESIGN-25-09-PARTE-2).
      - Shift+Tab: cicla normal -> plan -> sudo -> bypass (SHIFT-TAB-CYCLE-01).
      - Ctrl+V: clipboard image/text (VISION-02).

    Todas as KeyBindings carregam closures sobre os refs mutáveis recebidos.
    """
    from prompt_toolkit.application import run_in_terminal
    from prompt_toolkit.key_binding import KeyBindings

    kb = KeyBindings()

    @kb.add("c-o")
    def _expand_last_input(event: object) -> None:
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
            run_in_terminal(lambda: print(f"  {ansi_dim}Nenhum input anterior{ansi_reset}"))
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
        elif buf.document.text.strip() == "/" and not state:
            # Texto é apenas "/" sem popup aberto: abre lista com primeiro
            # item selecionado em vez de submeter comando vazio inválido.
            buf.start_completion(select_first=True)
            return
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
            return
        # TUI-REDESIGN-25-09-PARTE-2: prompt vazio + thinking armazenado
        # em app_state alterna expand/collapse e re-renderiza.
        if not buf.text.strip():
            tb = app_state.get("last_thinking_block")
            if isinstance(tb, dict) and tb.get("text"):
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
    def _cycle_mode(event: object) -> None:
        # SHIFT-TAB-CYCLE-01: cicla normal -> plan -> sudo -> bypass -> normal.
        # Mantém flag legada app_state["bypass"] coerente para compat
        # (output.py:make_ask_permission lê state["bypass"] direto).
        # SUDO-MODE-01: ao entrar em sudo, pede senha via getpass (run_in_terminal
        # para não conflitar com prompt_toolkit). Ao sair, wipe sempre.
        from nyx.agent.tools import sudo_session
        from nyx.agent.tools.plan_mode import set_plan_mode

        cur = str(app_state.get("mode", "normal"))
        try:
            idx = modes.index(cur)
        except ValueError:
            idx = 0
        nxt = modes[(idx + 1) % len(modes)]
        app_state["mode"] = nxt
        app_state["bypass"] = (nxt == "bypass")
        app_state["plan_mode"] = (nxt == "plan")
        app_state["sudo_mode"] = (nxt == "sudo")
        set_plan_mode(nxt == "plan")

        # SUDO-MODE-01: handler de transição.
        if cur == "sudo" and nxt != "sudo":
            # saiu de sudo -> apaga senha cacheada.
            sudo_session.wipe()
        elif nxt == "sudo" and cur != "sudo":
            # entrou em sudo -> pede senha se ainda não cacheada.
            def _prompt_sudo() -> None:
                ok, msg = sudo_session.prompt_and_cache()
                if ok:
                    sudo_session.set_active(True)
                    print(f"  {ansi_success} {msg}{ansi_reset}")
                else:
                    # fallback: volta para normal (não fica em sudo sem senha).
                    sudo_session.set_active(False)
                    app_state["mode"] = "normal"
                    app_state["sudo_mode"] = False
                    print(f"  {ansi_dim}{msg}{ansi_reset}")

            run_in_terminal(_prompt_sudo)

        event.app.invalidate()  # type: ignore[attr-defined]

    @kb.add("c-v")
    def _paste(event: object) -> None:
        from nyx.agent.clipboard import capture_image, capture_text

        buf = event.current_buffer  # type: ignore[attr-defined]
        img_path = capture_image()
        if img_path is not None:
            image_counter["n"] += 1
            n = image_counter["n"]
            image_map[n] = str(img_path)
            persist_image_index(image_map)
            buf.insert_text(f"[Image #{n}]")
            run_in_terminal(lambda: print(f"  {ansi_dim}⇲ Image #{n} salva em {img_path}{ansi_reset}"))
            return
        text = capture_text()
        if text:
            buf.insert_text(text)

    @kb.add("c-q")
    def _quit_immediate(event: object) -> None:
        """Ctrl+Q: fecha REPL imediatamente. Reusa fluxo de /quit via sentinel.

        TUI-CTRL-Q-OLLAMA-STOP-04: convenção Unix de fechar app de terminal.
        Shutdown ordenado (sudo wipe, analytics.end_session, ollama stop all,
        save_session, agent.close) roda em cli.py + cli_boot.shutdown_repl.
        """
        event.app.exit(result="__quit__")  # type: ignore[attr-defined]

    return kb


def build_bottom_toolbar(
    *,
    app_state: dict[str, Any],
    model: str,
    state_glyphs: dict[str, str],
    bullets: dict[str, str],
    nyx_accent: str,
    nyx_muted: str,
    nyx_primary: str,
    nyx_purple: str,
    nyx_purple_dim: str,
    nyx_error: str,
) -> Callable[[], Any]:
    """Factory do bottom toolbar do PromptSession.

    Schema de secções (separadas por ' · '):
      [ctx]                     -- ctx X% (Ntok/Mtok) ou ctx X%
      [modelo · iter · lidos · modif]
      [model_state]             -- cold | warming | warm (UX-BUG-02B)
      [bypass]                  -- ON: fundo roxo; OFF: dica muted

    Contrato: cada secção é um FormattedText fragment. Extensões
    anexam seus fragments ao final de `parts`, sem sobrescrever.
    """
    from prompt_toolkit.formatted_text import FormattedText

    def _bottom_toolbar() -> Any:
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
        parts.append((f"fg:{nyx_accent}", ctx_label))

        # UX-CLAUDE-PARITY-01 (ADR-029): pipes ' | ' como separator
        # estrutural (paridade com CLI de referencia), preservando paleta e glifos.
        meta = f"  |  {model}  |  iter {iter_n}  |  lidos {reads}  |  modif {mods}"
        parts.append((f"fg:{nyx_muted}", meta))

        model_state = app_state.get("model_state", "cold")
        glyph = state_glyphs.get(model_state, state_glyphs["cold"])
        parts.append((f"fg:{nyx_muted}", f"  |  {glyph} {model_state}"))

        # UX-AGENCY-02: indicador de tool em curso (footer dinâmico)
        inflight = app_state.get("inflight_task")
        if inflight is not None and not inflight.done():
            parts.append((f"fg:{nyx_accent}", "  |   executando (Ctrl+C cancela)"))

        # SHIFT-TAB-CYCLE-01: 4 modos com cor distinta.
        #   normal -> muted (dica de cycling)
        #   plan   -> roxo
        #   sudo   -> vermelho
        #   bypass -> roxo dim + glifo
        mode = str(app_state.get("mode", "normal"))
        parts.append(("", "  "))
        if mode == "bypass":
            parts.append((
                f"bg:{nyx_purple_dim} fg:{nyx_primary} bold",
                f" {bullets['bypass_on']} bypass ON (shift+tab) ",
            ))
        elif mode == "plan":
            parts.append((
                f"bg:{nyx_purple} fg:{nyx_primary} bold",
                " [plan] read-only (shift+tab) ",
            ))
        elif mode == "sudo":
            parts.append((
                f"bg:{nyx_error} fg:{nyx_primary} bold",
                " [sudo] elevado (shift+tab) ",
            ))
        else:
            parts.append((f"fg:{nyx_muted}", "    shift+tab: normal/plan/sudo/bypass"))
        return FormattedText(parts)

    return _bottom_toolbar
