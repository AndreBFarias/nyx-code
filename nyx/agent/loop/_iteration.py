"""Mixin com métodos de iteração do AgentLoop.

Separa do _core.py para manter cada arquivo abaixo de 400 linhas.
Este mixin NÃO funciona isolado -- espera atributos injetados por AgentLoop
(_tools, _session, _permissions, _parser, _on_tool, _on_tool_result,
_on_permission, _last_action, _consecutive_skips, _has_results, etc.).
"""

from __future__ import annotations

import asyncio
import inspect
import json
import os
from typing import Any

import httpx

from nyx.agent.intent import classify as _classify_intent
from nyx.agent.lang_check import is_pt_br
from nyx.agent.loop._constants import ACTION_TO_TOOL, CORE_TOOLS, LLM_TIMEOUT, TOOL_KEYWORDS, _remap_params
from nyx.agent.models import (
    ActionType,
    AgentAction,
    SessionState,
    SessionStatus,
)
from nyx.agent.permissions import PermissionLevel
from nyx.agent.preflight import check as preflight_check
from nyx.agent.prompt import build_reminder
from nyx.agent.repetition import SkipStrategy, get_skip_strategy
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.plan_mode import is_tool_allowed_in_plan_mode
from nyx.agent.validator import FORGE_PATTERNS
from nyx.agent.validator import validate as post_validate
from nyx.providers.base import ProviderError

logger = get_logger("nyx.agent")


# TUI-AGENT-LOOP-CONVERGE-01: sentinel retornado por _check_repetition no caso
# SkipStrategy.SKIP. O caller PULA a execução e continua o loop (return None)
# SEM passar pelo reset de _consecutive_skips -- a pressão para FORCE_DONE
# acumula. Antes o SKIP retornava None e, como o caller só age em valor truthy,
# a tool executava mesmo (skip morto desde o port) e o reset pós-execução zerava
# o contador, impedindo a convergência (loop até MAX_ITERATIONS).
_SKIP_ACTION = object()


# NYX-OUTPUT-LIMITS-01: heuristica de truncate em resposta de chat.
# Disparada por terminacoes abruptas (virgula, hifen aberto, parenteses aberto)
# em respostas com ao menos 100 caracteres; ignora outputs curtos onde a
# terminacao pode ser legitima ('ok,' '-' rotulos etc.).
_TRUNCATE_SUFFIXES = (",", "-", "(", "—", ":", ";")


def _detect_truncate(text: str) -> bool:
    if not text:
        return False
    stripped = text.rstrip()
    if len(stripped) < 100:
        return False
    return stripped.endswith(_TRUNCATE_SUFFIXES)


# NYX-PROMPT-REINJECT-01: cadência default de reinjeção de system-reminder
# canônico no histórico. Sobrescrita via env NYX_REMINDER_EVERY (int > 0).
# Cadência 3 escolhida empiricamente: turnos típicos de qwen2.5-coder:3b com
# tarefa multi-passo encadeiam 3-5 tool calls; reminder a cada 3 mantém
# pedido original e invariantes vivos sem inflar input em chats curtos.
_REMINDER_EVERY_DEFAULT = 3


def _reminder_every() -> int:
    """Lê NYX_REMINDER_EVERY se válido (int >= 1); senão default 3."""
    raw = os.environ.get("NYX_REMINDER_EVERY", "")
    if not raw:
        return _REMINDER_EVERY_DEFAULT
    try:
        n = int(raw)
    except ValueError:
        return _REMINDER_EVERY_DEFAULT
    return n if n >= 1 else _REMINDER_EVERY_DEFAULT


class _IterationMixin:
    """Métodos de iteração/LLM extraídos de AgentLoop."""

    # LOOP-DONE-VERIFY-ARTIFACTS-01 (#351): combate o "done alucinado" -- o 3b
    # declara um arquivo criado sem criar (ex.: README anunciado mas ausente).
    _DONE_REJECT_HINT = (
        "Você ainda NÃO criou nem alterou nenhum arquivo neste turno. NÃO chame "
        "done. Chame a tool write_file (ou edit_file) com o conteúdo de verdade "
        "primeiro; só chame done depois que o arquivo existir."
    )

    def _init_done_guard(self, user_input: str) -> None:
        """Arma o guard de done no início do turno: baseline de writes + se o
        pedido é de criar/escrever arquivo (intent 'code')."""
        self._turn_writes_baseline = self._session.files_modified_count
        self._turn_wants_create = _classify_intent(user_input) == "code"
        self._done_rejected = False

    def _turn_create_unmet(self) -> bool:
        """True se o turno pediu criar/escrever (intent 'code') e nenhum write
        efetivou em relação ao baseline do início do turno.

        Predicado puro de observação -- NÃO consome o gate _done_rejected (que é
        do mecanismo de rejeição-1x do done explícito, 351). Reusado pelo
        FORCE_DONE (344) para tornar o summary honesto sem bloquear o fim do turno
        (ADR-033: forçar o fim é aceitável; mentir sobre o fim, não)."""
        if not getattr(self, "_turn_wants_create", False):
            return False
        baseline = getattr(self, "_turn_writes_baseline", 0)
        wrote = self._session.files_modified_count > baseline
        return not wrote

    def _should_reject_done(self) -> bool:
        """Rejeita o done UMA vez se o turno pediu criar/escrever e nenhum write
        efetivou. Rejeita no máximo 1x/turno; MAX_ITERATIONS é a rede final."""
        if getattr(self, "_done_rejected", False):
            return False
        return self._turn_create_unmet()

    async def _execute_tool_calls(self, tool_calls: list[dict], iteration: int) -> SessionStatus | None:
        """Executa tool calls do LLM. Retorna SessionStatus se done/force_done.

        TUI-FIX-HTTPX-LOOP-AFFINITY-01 (ONDA-33): async para rodar no event
        loop principal do Textual (sem worker thread). A execução bloqueante
        da tool (`self._tools.execute`) vai para `asyncio.to_thread` para não
        congelar a UI; os callbacks (`_on_tool`/`_on_tool_result`) permanecem
        no loop principal -- podem tocar widgets sem `call_from_thread`.
        """
        for tc in tool_calls:
            name = tc["name"]
            args = tc["arguments"]

            if self._on_tool:
                self._on_tool(name, args)

            if self._tools.is_done(name):
                if self._should_reject_done():
                    self._done_rejected = True
                    self._session.add_tool_call(name, args, self._DONE_REJECT_HINT)
                    continue
                summary = args.get("summary", "Tarefa concluída.")
                self._session.add_tool_call(name, args, summary, is_key=True)
                return SessionStatus(
                    state=SessionState.DONE,
                    iterations=iteration,
                    summary=summary,
                )

            if not is_tool_allowed_in_plan_mode(name):
                logger.warning("[loop] bloqueado por plan_mode: %s", name)
                self._session.add_tool_call(
                    name, args, "Bloqueado: modo planejamento ativo. Use exit_plan_mode primeiro."
                )
                continue

            perm = self._permissions.check(name, args)
            if perm == PermissionLevel.DENY:
                logger.warning("[loop] permissão negada: %s", name)
                self._session.add_tool_call(name, args, f"Permissão negada para {name}")
                continue

            if perm in (PermissionLevel.CONFIRM_ONCE, PermissionLevel.ALWAYS_CONFIRM):
                if self._on_permission:
                    approved = self._on_permission(perm, name, args)
                    # TUI-PERMISSION-CONFIRM-01 (ONDA-37): suporta callback ASYNC -- a
                    # TUI abre um ConfirmScreen e espera (push_screen_wait). Callback
                    # síncrono (prompt_toolkit/headless) segue igual. Não muda a
                    # assinatura pública (on_permission já é param de construção).
                    if inspect.isawaitable(approved):
                        approved = await approved
                    if not approved:
                        self._session.add_tool_call(name, args, f"Usuário negou: {name}")
                        continue
                    if perm == PermissionLevel.CONFIRM_ONCE:
                        self._permissions.mark_confirmed(name)

            # LOOP-ACTIONTYPE-FALLBACK-DONE-01: tools fora do enum ActionType
            # (multi_edit, skill, task_*, agent, ask_user, ...) NÃO viram mais
            # ActionType.DONE. Colapsar em DONE quebrava o detector de repetição:
            # is_in_recent/is_semantic chaveiam por action_type.value e o
            # histórico guarda o tool_name real -- "done" nunca casava com
            # "multi_edit", então repetição real passava batido; e tools
            # distintas colapsadas em DONE colidiam falso em is_exact_repeat.
            # Rótulo opaco MCP_TOOL (não-terminal) + o `name` real passado como
            # chave de identidade ao detector. O done que conclui o turno vem SÓ
            # de is_done (tratado acima, ~L129), nunca deste fallback.
            is_canon = name in [a.value for a in ActionType]
            action = AgentAction(
                action_type=ActionType(name) if is_canon else ActionType.MCP_TOOL,
                params=args,
            )
            skip = self._check_repetition(action, tool_name=name)
            if skip is _SKIP_ACTION:
                return None
            if skip:
                return skip

            pf = preflight_check(name, args, self._project_root)
            if not pf.ok:
                reason = "; ".join(pf.errors)
                logger.warning("[loop] preflight bloqueou %s: %s", name, reason)
                self._session.add_tool_call(name, args, f"Bloqueado por validação: {reason}")
                continue
            for warn in pf.warnings:
                logger.info("[loop] preflight aviso para %s: %s", name, warn)

            # HOOKS-DYNAMIC-03: PreToolUse antes da execução. block_on_failure
            # honrado via HookResult.blocked=True -> pula tool (continue).
            hooks = getattr(self, "_hooks", None)
            if hooks is not None:
                try:
                    pre_results = hooks.run(
                        "PreToolUse", {"tool_name": name, "tool_input": args}
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("hook PreToolUse falhou: %s", exc)
                    pre_results = []
                if any(r.blocked for r in pre_results):
                    logger.warning("[loop] hook PreToolUse bloqueou %s", name)
                    self._session.add_tool_call(
                        name, args, f"Bloqueado por hook PreToolUse: {name}"
                    )
                    continue

            import time as _time

            _t0 = _time.monotonic()
            result = await asyncio.to_thread(self._tools.execute, name, args)
            self._tool_durations.setdefault(name, []).append((_time.monotonic() - _t0) * 1000.0)
            self._tool_summary.track(name, args)

            # HOOKS-DYNAMIC-03: PostToolUse com tool_result.
            if hooks is not None:
                try:
                    hooks.run(
                        "PostToolUse",
                        {
                            "tool_name": name,
                            "tool_result": (
                                result.output if result.success else (result.error or "")
                            ),
                        },
                    )
                except Exception as exc:  # noqa: BLE001
                    logger.warning("hook PostToolUse falhou: %s", exc)

            vr = post_validate(name, args, result)
            for warn in vr.warnings:
                logger.info("[loop] validator aviso para %s: %s", name, warn)

            if not result.success:
                self._diagnostics.record_warning("tool", f"{name}: {result.error[:120]}")

            if self._on_tool_result:
                self._on_tool_result(name, result.output if result.success else result.error)

            self._session.add_tool_call(
                name,
                args,
                result.output if result.success else result.error,
                is_key=name in ("write_file", "edit_file", "create_file", "run_command"),
            )
            self._session.track_files(result.files_read, result.files_modified)
            # NYX-GSD-CHECKPOINTS-01: write-through do tool call em progress.md.
            self._gsd.tool(
                name,
                args,
                result.output if result.success else result.error,
            )
            # NYX-PROMPT-REINJECT-01: contador de tool calls dispara reinjeção
            # periódica em _call_llm. Conta no turno e na sessão.
            self._tool_calls_count = getattr(self, "_tool_calls_count", 0) + 1
            self._tool_calls_this_turn = getattr(self, "_tool_calls_this_turn", 0) + 1
            self._last_action = action
            # LOOP-ACTIONTYPE-FALLBACK-DONE-01: nome real da última ação, usado
            # como `last_key` em is_exact_repeat (distingue tools fora do enum).
            self._last_action_name = name
            self._consecutive_skips = 0
            if result.success:
                self._has_results = True

        return None

    async def _execute_parsed_action(self, action: AgentAction, iteration: int) -> SessionStatus | None:
        """Executa ação extraída pelo parser fallback.

        TUI-FIX-HTTPX-LOOP-AFFINITY-01 (ONDA-33): async pelo mesmo motivo de
        `_execute_tool_calls` -- `self._tools.execute` vai para `to_thread`.
        """
        if action.action_type == ActionType.DONE:
            if self._should_reject_done():
                self._done_rejected = True
                self._session.add_tool_call("done", action.params, self._DONE_REJECT_HINT)
                return None  # continua o loop -- força o write_file antes do done
            summary = action.params.get("summary", "Tarefa concluída.")
            self._session.add_tool_call("done", action.params, summary, is_key=True)
            return SessionStatus(
                state=SessionState.DONE,
                iterations=iteration,
                summary=summary,
            )

        tool_name = ACTION_TO_TOOL.get(action.action_type)
        if not tool_name:
            unrouted = action.action_type.value
            logger.warning("[loop] sem tool para %s", unrouted)
            # ADR-026: nada silencioso. O descarte vira evento visível no chat
            # para que qualquer lacuna futura (enum sem rota) apareça ao
            # usuário/validador, em vez de sumir só no log.
            self._session.add_tool_call(
                unrouted,
                action.params,
                f"ação não roteável: {unrouted} (sem entrada em ACTION_TO_TOOL)",
            )
            return None

        remapped = _remap_params(tool_name, action.params)

        if self._on_tool:
            self._on_tool(tool_name, remapped)

        perm = self._permissions.check(tool_name, remapped)
        if perm == PermissionLevel.DENY:
            logger.warning("[loop] permissão negada (parser): %s", tool_name)
            self._session.add_tool_call(tool_name, remapped, f"Permissão negada para {tool_name}")
            return None

        if perm in (PermissionLevel.CONFIRM_ONCE, PermissionLevel.ALWAYS_CONFIRM):
            if self._on_permission:
                approved = self._on_permission(perm, tool_name, remapped)
                if not approved:
                    self._session.add_tool_call(tool_name, remapped, f"Usuário negou: {tool_name}")
                    return None
                if perm == PermissionLevel.CONFIRM_ONCE:
                    self._permissions.mark_confirmed(tool_name)

        skip = self._check_repetition(action)
        if skip is _SKIP_ACTION:
            return None
        if skip:
            return skip

        pf = preflight_check(tool_name, remapped, self._project_root)
        if not pf.ok:
            reason = "; ".join(pf.errors)
            logger.warning("[loop] preflight bloqueou %s (parser): %s", tool_name, reason)
            self._session.add_tool_call(tool_name, remapped, f"Bloqueado por validação: {reason}")
            return None
        for warn in pf.warnings:
            logger.info("[loop] preflight aviso para %s: %s", tool_name, warn)

        import time as _time

        _t0 = _time.monotonic()
        result = await asyncio.to_thread(self._tools.execute, tool_name, remapped)
        self._tool_durations.setdefault(tool_name, []).append((_time.monotonic() - _t0) * 1000.0)

        vr = post_validate(tool_name, remapped, result)
        for warn in vr.warnings:
            logger.info("[loop] validator aviso para %s: %s", tool_name, warn)

        self._session.add_tool_call(
            tool_name,
            remapped,
            result.output if result.success else result.error,
            is_key=tool_name in ("write_file", "edit_file", "create_file", "run_command"),
        )
        self._session.track_files(result.files_read, result.files_modified)
        # NYX-GSD-CHECKPOINTS-01: write-through do tool call (parser fallback).
        self._gsd.tool(
            tool_name,
            remapped,
            result.output if result.success else result.error,
        )
        # NYX-PROMPT-REINJECT-01: contador de tool calls (fallback via parser).
        self._tool_calls_count = getattr(self, "_tool_calls_count", 0) + 1
        self._tool_calls_this_turn = getattr(self, "_tool_calls_this_turn", 0) + 1
        self._last_action = action
        # LOOP-ACTIONTYPE-FALLBACK-DONE-01: no parser fallback o action_type é
        # canônico, então tool_name == action_type.value; mantém last_key coerente.
        self._last_action_name = tool_name
        self._consecutive_skips = 0
        if result.success:
            self._has_results = True

        return None

    def _check_repetition(
        self, action: AgentAction, tool_name: str | None = None
    ) -> SessionStatus | None:
        """Verifica repetição e retorna FORCE_DONE se necessário.

        LOOP-ACTIONTYPE-FALLBACK-DONE-01: `tool_name` é o nome real da tool. Para
        tools fora do enum ActionType (action_type opaco MCP_TOOL) ele é a chave
        de identidade no detector -- sem isso, repetição real escapava e tools
        distintas colidiam. None (ou caminho do parser, onde tool_name ==
        action_type.value) preserva o comportamento canônico da 344.
        """
        key = tool_name if tool_name is not None else action.action_type.value
        strategy = get_skip_strategy(
            action=action,
            last_action=self._last_action,
            history=self._session.history,
            files_modified=self._session._files_modified,
            consecutive_skips=self._consecutive_skips,
            has_results=self._has_results,
            key=key,
            last_key=getattr(self, "_last_action_name", None),
        )

        if strategy == SkipStrategy.FORCE_DONE:
            # LOOP-FORCE-DONE-HARDENING-01 (A7): o FORCE_DONE fecha o turno mesmo
            # (rede anti-MAX_ITERATIONS, não-bloqueante por design). Mas se o turno
            # pediu criar/escrever e nenhum write efetivou, o summary deve ser
            # HONESTO -- repetir read_file/list_files até o teto e anunciar sucesso
            # é o "done alucinado" que a 351 corta no done explícito, voltando por
            # esta porta. _turn_create_unmet() é o mesmo predicado do guard, sem o
            # gate de rejeição-1x (aqui não rejeitamos nada; ADR-033).
            repeated = key if key is not None else action.action_type.value
            summary = self._build_force_done_summary(
                create_unmet=self._turn_create_unmet(),
                repeated_action=repeated,
            )
            logger.info("[loop] FORCE_DONE por repetição: %s", summary[:80])
            return SessionStatus(
                state=SessionState.DONE,
                iterations=self._session.iteration,
                summary=summary,
            )

        if strategy == SkipStrategy.SKIP:
            self._consecutive_skips += 1
            logger.info("[loop] SKIP repetição (%d consecutivos)", self._consecutive_skips)
            # Loga o nome real da tool (não action_type.value, que para tools
            # fora do enum seria o rótulo opaco) -- histórico fiel e is_in_recent
            # subsequente continua casando.
            self._session.add_tool_call(
                key,
                action.params,
                f"Ação repetida ignorada ({self._consecutive_skips}x)",
            )
            return _SKIP_ACTION

        return None

    def _maybe_inject_reminder(self) -> None:
        """NYX-PROMPT-REINJECT-01: injeta <system-reminder> periodicamente.

        Cadência primaria por tool calls (cada REMINDER_EVERY). Drift detectado
        (idioma ou alucinacao) força injeção imediata via flag _force_reminder.
        Skip se histórico ainda não tem turno fechado (iter==0/sem tool count).
        """
        force = getattr(self, "_force_reminder", False)
        count = getattr(self, "_tool_calls_count", 0)
        every = getattr(self, "_reminder_every", _REMINDER_EVERY_DEFAULT)
        if not force:
            if count == 0:
                return
            if count % every != 0:
                return
            # Evita reinjetar no mesmo tick (idempotente por turno).
            if getattr(self, "_last_reminder_at_count", -1) == count:
                return
        try:
            reminder = build_reminder(
                self._session,
                self._project_root,
                original_input=getattr(self, "_original_input", None),
                extra=getattr(self, "_reminder_extra", None),
            )
        except Exception as exc:  # noqa: BLE001 -- reminder e best-effort, não derruba loop
            logger.warning("[reinject] build_reminder falhou: %s", exc)
            return
        # System role no histórico via add_user evitaria conflito de schema; usamos
        # add_user com prefixo canônico para que to_messages preserve role=user
        # mas o conteúdo entregue ao modelo seja o bloco system-reminder cru.
        # Modelos OpenAI-compatible aceitam role=user com bloco <system-reminder>;  # noqa-anonimato
        # o que importa é a presença visual do bloco no contexto reduzido.
        self._session.add_user(reminder)
        self._last_reminder_at_count = count
        self._force_reminder = False
        self._reminder_extra = None
        if getattr(self, "_gsd", None):
            try:
                origem = "drift" if force else f"cadencia/{count}"
                self._gsd.write("reminder", f"injetado ({origem})")
            except Exception as exc:  # noqa: BLE001 -- gsd e best-effort
                logger.debug("[reinject] gsd write falhou: %s", exc)
        logger.info(
            "[reinject] system-reminder injetado (tool_calls=%d, force=%s)",
            count,
            force,
        )

    def _detect_drift(self, last_assistant_text: str) -> tuple[bool, str | None]:
        """Detecta drift de idioma (2x EN consecutivo) ou alucinação de sucesso.

        Retorna (drift_detectado, hint_extra) para o próximo reminder. hint vazio
        quando não houve drift.
        """
        text = (last_assistant_text or "").strip()
        if not text:
            return (False, None)

        # Lang drift: 2 turnos consecutivos não-PT-BR.
        try:
            pt_ok = is_pt_br(text)
        except Exception:  # noqa: BLE001 -- detector e heuristico
            pt_ok = True
        if not pt_ok:
            self._lang_drift_streak = getattr(self, "_lang_drift_streak", 0) + 1
            if self._lang_drift_streak >= 2:
                return (
                    True,
                    "- DRIFT DE IDIOMA detectado: responda em PT-BR acentuado SEMPRE.",
                )
        else:
            self._lang_drift_streak = 0

        # Hallucination drift: afirma sucesso sem tool no turno.
        tool_calls_this_turn = getattr(self, "_tool_calls_this_turn", 0)
        if tool_calls_this_turn == 0:
            for pattern in FORGE_PATTERNS:
                if pattern.search(text):
                    return (
                        True,
                        "- NYX-NO-HALLUCINATE: não afirme sucesso sem write_file/edit_file/create_file.",
                    )

        return (False, None)

    async def _call_llm(self) -> dict[str, Any]:
        """Envia request ao proxy com histórico e tools.

        Estratégia de contexto para GPU limitada (num_ctx=4096, RTX 3050 4GB):
        - Histórico curto (<= 4 msgs): envia tudo.
        - Histórico longo (> 4 msgs): envia só as últimas 4 (user + tool_call +
          result + resposta). É uma escolha deliberada de sobrevivência em janela
          apertada; a memória de longo prazo é reinjetada de forma barata pelo
          <system-reminder> (repo_map + session_summary + pedido original) via
          _maybe_inject_reminder, não por este ponto.

        Trade-off assumido (LOOP-CONTEXT-WINDOW-AUDIT-01): a janela de 4 pode
        omitir citações antigas (ex.: arquivo mencionado muitos turnos atrás),
        sintoma mitigado por prompt nas sprints 354/355. A compactação progressiva
        do ContextBudget roda em _run_iterations (não aqui); medição registrada em
        dev-journey/07-reports/RELATORIO_LOOP_CONTEXT_WINDOW_AUDIT_01.md mostrou
        que anexar o resumo aqui (opção b) custaria até ~84% do num_ctx em
        conversas médias sem comprimir, por isso foi descartada.
        """
        # NYX-PROMPT-REINJECT-01: reinjeta <system-reminder> antes da request,
        # com base em contagem de tool calls ou drift detectado no turno anterior.
        self._maybe_inject_reminder()

        # UX-LIFECYCLE-01: VRAM check pré-inferência em cold start.
        # Só roda uma vez por sessão. Em CPU mode (_OOM_DEGRADED pelo proxy)
        # ou sem nvidia-smi, retorna ok=True silenciosamente.
        if not getattr(self, "_vram_checked", False):
            self._vram_checked = True
            from nyx.agent.services.lifecycle import Lifecycle

            ok, free_mib = Lifecycle().vram_check()
            if not ok:
                logger.warning("[loop] VRAM insuficiente: %d MiB livres", free_mib)
                return {
                    "error": (
                        f"VRAM insuficiente ({free_mib} MiB livres). "
                        "Feche outros processos GPU ou rode em CPU com NYX_NUM_GPU=0."
                    ),
                    "error_detail": f"vram_free={free_mib}MiB threshold=800MiB",
                }
            if free_mib >= 0:
                logger.info("[loop] VRAM OK: %d MiB livres", free_mib)

        history_msgs = self._session.to_messages()

        # Seleção de tools precisa do user real, não do system_prompt;
        # passamos apenas history para a heurística.
        _probe = list(history_msgs)
        selected_tools = self._select_tools_for_context(_probe)

        # System prompt compacto quando não há tools: economiza ~1.5k tokens
        # de input por turno (PERF-INFERENCE-01).
        if not selected_tools and getattr(self, "_system_prompt_compact", None):
            system_content = self._system_prompt_compact
        else:
            system_content = self._system_prompt

        messages = [{"role": "system", "content": system_content}]

        # Janela fixa de 4 quando o histórico é longo. O ramo de compactação
        # local foi removido por ser inalcançável (LOOP-CONTEXT-WINDOW-AUDIT-01):
        # should_compact só vira True por volta de ~50 turnos, ponto em que este
        # `if len > 4` já captura; a compactação efetiva mora em _run_iterations.
        if len(history_msgs) > 4:
            messages.extend(history_msgs[-4:])
            logger.info("[loop] contexto reduzido: %d/%d msgs", 4, len(history_msgs))
        else:
            messages.extend(history_msgs)

        payload: dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "tools": selected_tools,
        }

        try:
            if self._http_client is None:
                self._http_client = httpx.AsyncClient(timeout=LLM_TIMEOUT)

            r = await self._http_client.post(
                f"{self._proxy_url}/v1/chat/completions",
                json=payload,
            )
            data = r.json()

            if "choices" not in data:
                return {
                    "error": "Resposta do proxy sem campo 'choices'. "
                    "Reinicie o proxy com ./run.sh ou inspecione ~/.nyx/logs/proxy.log.",
                    "error_detail": str(data)[:200],
                }

            msg = data["choices"][0]["message"]
            tc = msg.get("tool_calls", [])
            content = msg.get("content", "")

            # TUI-REDESIGN-25-09-PARTE-3: thinking capturado pelo proxy chega
            # como campo aditivo `nyx_reasoning`. Propaga via callback opcional
            # `_on_thinking` (mesmo shape de _on_tool/_on_tool_result). Quando
            # ausente, callsite/proxy não injetou — silêncio é correto.
            reasoning = msg.get("nyx_reasoning", "")
            if reasoning:
                on_thinking = getattr(self, "_on_thinking", None)
                if on_thinking:
                    try:
                        on_thinking(reasoning)
                    except Exception as exc:  # noqa: BLE001 -- callback é best-effort
                        logger.warning("[loop] on_thinking callback falhou: %s", exc)

            # NYX-OUTPUT-LIMITS-01: log warning se resposta parece truncada.
            # Heuristica passiva (so loga); não reissue para não bloquear ciclo.
            if content and not tc and _detect_truncate(content):
                logger.warning(
                    "[loop] possivel truncate (sufixo abrupto): '...%s'",
                    content.rstrip()[-50:],
                )

            if self._collector and content:
                self._collector.reset()
                for char in content:
                    self._collector.feed(char)

            result: dict[str, Any] = {"content": content, "tool_calls": []}
            for call in tc:
                fn = call.get("function", {})
                args = fn.get("arguments", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except json.JSONDecodeError:
                        args = {"raw": args}
                result["tool_calls"].append(
                    {
                        "name": fn.get("name", ""),
                        "arguments": args,
                    }
                )

            return result

        except httpx.TimeoutException as e:
            return {
                "error": f"Proxy de inferência não respondeu em {LLM_TIMEOUT}s. "
                "Verifique se o Ollama e o proxy estão vivos: systemctl status ollama && ss -ltnp | grep 1143",
                "error_detail": f"{type(e).__name__}: {e}",
            }
        except httpx.ConnectError as e:
            return {
                "error": "Conexão recusada pelo proxy de inferência. "
                "Reinicie o stack com ./run.sh ou confira ~/.nyx/logs/proxy.log.",
                "error_detail": f"{type(e).__name__}: {e}",
            }
        except ProviderError as e:
            return {
                "error": f"{e.user_message}" + (f" {e.hint}" if e.hint else ""),
                "error_detail": f"{type(e.cause).__name__ if e.cause else type(e).__name__}: {e.cause or e}",
            }
        except Exception as e:
            return {
                "error": f"Falha inesperada ao contatar o proxy: {type(e).__name__}. "
                "Abra ~/.nyx/logs/nyx.log para o traceback completo.",
                "error_detail": f"{type(e).__name__}: {e}",
            }

    async def _try_recovery(self) -> bool:
        """Tenta reiniciar o modelo Ollama após crash."""
        import asyncio

        ollama_base = self._proxy_url.replace("/v1", "").rstrip("/")
        logger.info("[recovery] Aguardando Ollama reiniciar...")
        for attempt in range(3):
            await asyncio.sleep(5)
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    r = await client.get(f"{ollama_base}/v1/models")
                    if r.status_code == 200:
                        logger.info("[recovery] Proxy respondendo, tentando aquecer modelo...")
                        warmup = await client.post(
                            f"{ollama_base}/v1/chat/completions",
                            json={
                                "model": self._model,
                                "messages": [{"role": "user", "content": "hi"}],
                                "max_tokens": 5,
                            },
                            timeout=120,
                        )
                        if warmup.status_code == 200:
                            logger.info("[recovery] Modelo aquecido, retomando")
                            return True
            except Exception as e:
                logger.warning("[recovery] Tentativa %d falhou: %s", attempt + 1, str(e)[:60])
        return False

    def _select_tools_for_context(self, messages: list[dict]) -> list[dict]:
        """Seleciona tools relevantes baseado no contexto.

        Gating agressivo (PERF-INFERENCE-01):
        - intent do último user = saudacao/chat -> retorna [].
        - intent = comando -> retorna [] (slash sai antes do LLM em fluxo normal).
        - intent = tool-needed -> CORE_TOOLS + ativadas por keyword, cap em 5.

        Tools já usadas anteriormente na sessão permanecem ativadas para
        continuidade (ex: leu README, agora pergunta sobre conteúdo).
        """
        last_user = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                content = msg.get("content", "")
                if isinstance(content, str):
                    last_user = content
                break
        intent = _classify_intent(last_user)

        if intent in ("saudacao", "chat", "comando"):
            logger.info("[loop] intent=%s -> tools=[]", intent)
            return []

        text_parts: list[str] = []
        for msg in messages[-4:]:
            if msg.get("role") == "system":
                continue
            content = msg.get("content", "")
            if content:
                text_parts.append(content.lower())
        context_text = " ".join(text_parts)

        selected_names = set(CORE_TOOLS)

        for tool_name, keywords in TOOL_KEYWORDS.items():
            if any(kw in context_text for kw in keywords):
                selected_names.add(tool_name)

        for entry in self._session.history[-3:]:
            if entry.role == "user":
                for tool_name, keywords in TOOL_KEYWORDS.items():
                    if any(kw in entry.content.lower() for kw in keywords):
                        selected_names.add(tool_name)

        for entry in self._session.history:
            if entry.tool_name:
                selected_names.add(entry.tool_name)

        all_defs = self._tools.tool_defs
        selected = [td for td in all_defs if td["function"]["name"] in selected_names]

        # Cap em 5 tools por turno: VRAM-limitada, schemas inflam input.
        # Prioridade: CORE primeiro (preserva read/write/edit/run/etc).
        if len(selected) > 5:
            # MEMORY-INTENT-CLASSIFY-01: write_memory é essencial para o pedido de
            # memória ("lembra que X"); sem prioridade o cap a corta (CORE tem 8 > 5)
            # e a memória nunca grava (achado do estresse ONDA-44).
            from nyx.agent.intent import wants_save_memory as _wsm

            must = {"write_memory"} if _wsm(last_user) else set()
            must_defs = [td for td in selected if td["function"]["name"] in must]
            core_ordered = [
                td for td in selected
                if td["function"]["name"] in CORE_TOOLS and td["function"]["name"] not in must
            ]
            extras = [
                td for td in selected
                if td["function"]["name"] not in CORE_TOOLS and td["function"]["name"] not in must
            ]
            selected = (must_defs + core_ordered + extras)[:5]

        logger.info("[loop] tools selecionadas: %d/%d (intent=%s)", len(selected), len(all_defs), intent)
        return selected


# "A iteração revela o que a intenção escondia." -- anônimo
