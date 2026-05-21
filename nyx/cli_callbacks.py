"""Callbacks de render do REPL: streaming, tool invocations, compaction.

Extraído de nyx/cli.py em INFRA-CLI-SPLIT-03. `build_render_callbacks` retorna
um dict com `on_token`, `on_tool`, `on_tool_result`, `on_compaction`,
`on_model_state`, `stop_spinner`, `flush_buffer`. Closures sobre os estados
mutáveis recebidos por referência (turn_state, spinner_state, etc.) preservam
a semântica original do REPL inline.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

TOKEN_FLUSH_CHARS = 32


def build_render_callbacks(
    *,
    agent_ref: list,
    app_state: dict,
    spinner_state: dict,
    turn_state: dict,
    side_rule_state: dict,
    tool_timers: dict[str, float],
    tool_args_cache: dict[str, dict],
    project_root: Path,
) -> dict[str, Any]:
    """Constrói o dict de callbacks que liga AgentLoop ao render do REPL.

    agent_ref: lista mutável [agent] (agent só existe após AgentLoop()), permite
    closure capturar referência sem reordenar instanciação.
    """
    from nyx.agent.commands._observability import on_model_state_log
    from nyx.agent.output import (
        is_tool_error,
        render_compaction_event,
        render_thinking_block,
    )

    def stop_spinner() -> None:
        sp = spinner_state.get("active")
        if sp is not None:
            sp.stop()  # type: ignore[union-attr]
            spinner_state["active"] = None

    def flush_buffer() -> None:
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
            stop_spinner()
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
            flush_buffer()

    def on_tool(name: str, args: dict) -> None:
        stop_spinner()
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
                    agent_ref[0].session.add_user(f"[resposta] {answer}")
                tool_args_cache.pop(name, None)
                return
        started = tool_timers.pop(name, None)
        duration_ms = int((time.monotonic() - started) * 1000) if started else 0
        first_line = next((ln.strip() for ln in (result or "").splitlines() if ln.strip()), "")
        is_err = is_tool_error(first_line)
        from nyx.agent.output import classify_error_actions, render_tool_chip
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
            project_root=str(project_root),
            error_actions=err_actions,
        )

    def on_compaction(level: int, tokens_removed: int, pct_before: float, pct_after: float) -> None:
        render_compaction_event(level, tokens_removed, pct_before, pct_after)

    def on_model_state(state: str) -> None:
        """Consumidor visual de transições cold/warming/warm (UX-BUG-02B).

        Grava em app_state para que _bottom_toolbar leia no próximo render.
        Mantém o log de debug do stub anterior intacto para auditoria.
        """
        app_state["model_state"] = state
        on_model_state_log(state)

    def on_thinking(text: str) -> None:
        """Render thinking colapsado (TUI-REDESIGN-25-12-PARTE-2).

        Consome `nyx_reasoning` propagado por _iteration.py:502. Default
        colapsado (1 linha preview); usuário expande via Tab (25-09-PARTE-2).
        """
        if not text:
            return
        render_thinking_block(text, duration_s=None, expanded=False)

    return {
        "stop_spinner": stop_spinner,
        "flush_buffer": flush_buffer,
        "on_token": on_token,
        "on_tool": on_tool,
        "on_tool_result": on_tool_result,
        "on_compaction": on_compaction,
        "on_model_state": on_model_state,
        "on_thinking": on_thinking,
    }


# "Callbacks são contratos invisíveis." -- anônimo
