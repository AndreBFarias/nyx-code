"""AgentLoop -- Ciclo plan-execute-observe do Nyx.

Fluxo integrado:
1. Recebe pedido do usuário
2. ContextBudget verifica budget -> compacta se necessário
3. Envia ao proxy (/v1/chat/completions com tools)
4. Se tool_calls: executa via PermissionChecker + RepetitionDetector
5. Se texto puro: ActionParser (7 níveis fallback) -> executa como tool
6. Se done(): salva sessão, termina
7. Se max_iterations: force_done
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional

import httpx

from nyx.agent.context import ContextBudget
from nyx.agent.loop._iteration import _IterationMixin, _reminder_every
from nyx.agent.loop._types import PermissionCallback
from nyx.agent.memory import NyxMemory
from nyx.agent.models import (
    AgentAction,
    SessionState,
    SessionStatus,
)
from nyx.agent.parser import ActionParser
from nyx.agent.permissions import PermissionChecker
from nyx.agent.prompt import build_guide_md_context, build_system_prompt, build_system_prompt_compact
from nyx.agent.repomap import RepoMap
from nyx.agent.services.diagnostics import DiagnosticTracking
from nyx.agent.services.gsd_writer import GsdWriter
from nyx.agent.services.logging_service import get_logger
from nyx.agent.services.tool_use_summary import ToolUseSummary
from nyx.agent.session import CodeSession
from nyx.agent.streaming import StreamingCollector
from nyx.agent.summarizer import SessionSummarizer
from nyx.agent.tools.registry import ToolRegistry
from nyx.agent.validator import detect_forged_success
from nyx.config.defaults import DEFAULT_MODEL as _DEFAULT_MODEL
from nyx.config.defaults import MAX_ITERATIONS as MAX_ITERATIONS_DEFAULT
from nyx.config.defaults import PROXY_URL as _DEFAULT_PROXY_URL

if TYPE_CHECKING:
    from nyx.config.settings import NyxSettings

logger = get_logger("nyx.agent")


class AgentLoop(_IterationMixin):
    def __init__(
        self,
        project_root: str,
        proxy_url: str = _DEFAULT_PROXY_URL,
        model: str = _DEFAULT_MODEL,
        max_iterations: int = MAX_ITERATIONS_DEFAULT,
        on_token: Any = None,
        on_tool: Any = None,
        on_tool_result: Any = None,
        on_permission: PermissionCallback | None = None,
        on_compaction: Optional[Callable[[int, int, float, float], None]] = None,
        on_model_state: Optional[Callable[[str], None]] = None,
        on_thinking: Any = None,
        streaming: bool = True,
        settings: "NyxSettings | None" = None,
    ) -> None:
        if settings is not None:
            if proxy_url == _DEFAULT_PROXY_URL:
                proxy_url = settings.proxy_url
            if model == _DEFAULT_MODEL:
                model = settings.model
            if max_iterations == MAX_ITERATIONS_DEFAULT:
                max_iterations = settings.max_iterations

        self._settings = settings
        self._project_root = project_root
        self._proxy_url = proxy_url
        self._model = model
        self._max_iterations = max_iterations
        self._tools = ToolRegistry(project_root)
        self._session = CodeSession()
        self._on_token = on_token
        self._on_tool = on_tool
        self._on_tool_result = on_tool_result
        self._on_permission = on_permission
        self._on_compaction = on_compaction
        self._on_model_state = on_model_state
        # TUI-REDESIGN-25-12-PARTE-2: amarra callback consumido em _iteration.py:502
        # ao render_thinking_block (output.py:803). Quando None, propagação é no-op.
        self._on_thinking = on_thinking
        self._streaming = streaming
        self._tool_durations: dict[str, list[float]] = {}
        self._model_state: str = "cold"
        # UX-LIFECYCLE-01: VRAM check pré-inferência é executado apenas uma vez
        # por sessão (cold start). Mudanças de VRAM mid-session são raras e cobertas
        # pelo OOM degradation do proxy.
        self._vram_checked: bool = False
        self._emit_state("cold")

        self._parser = ActionParser()
        self._budget = ContextBudget()
        self._permissions = PermissionChecker()
        self._last_action: AgentAction | None = None
        self._consecutive_skips: int = 0
        self._has_results: bool = False
        # NYX-PROMPT-REINJECT-01: estado da reinjeção de system-reminders.
        # Cadência configurável via env NYX_REMINDER_EVERY (default 3).
        self._reminder_every: int = _reminder_every()
        self._tool_calls_count: int = 0
        self._tool_calls_this_turn: int = 0
        self._last_reminder_at_count: int = -1
        self._lang_drift_streak: int = 0
        self._force_reminder: bool = False
        self._reminder_extra: str | None = None
        self._original_input: str | None = None

        self._collector = StreamingCollector(on_token=on_token) if streaming and on_token else None
        self._http_client: httpx.AsyncClient | None = None
        self._diagnostics = DiagnosticTracking()
        self._tool_summary = ToolUseSummary()

        self._memory = NyxMemory(project_root)
        self._memory_bundle = self._memory.load()

        self._summarizer = SessionSummarizer(proxy_url=proxy_url, model=model)
        self._session_id: str = f"{Path(project_root).name}_{int(__import__('time').time())}"

        # NYX-GSD-CHECKPOINTS-01: progress.md write-through por sessão.
        # GsdWriter e best-effort: falhas de I/O não derrubam o agente.
        self._gsd = GsdWriter(self._session_id, Path(project_root).name)

        self._repomap = RepoMap(project_root)
        try:
            self._repomap.build()
        except Exception as e:  # noqa: BLE001 -- indexação não deve derrubar boot
            logger.warning("repomap: falha no build inicial: %s", e)

        def _on_post_tool(tool_name: str, args: dict, result: Any) -> None:
            if tool_name not in ("write_file", "edit_file", "create_file", "multi_edit", "patch"):
                return
            path = args.get("file_path") or args.get("path") or ""
            if not path or not path.endswith(".py"):
                return
            self._repomap.invalidate(path)

        self._tools.hooks.register_post(_on_post_tool)

        self._tool_names = [t["function"]["name"] for t in self._tools.tool_defs]
        self._guide_ctx = build_guide_md_context(project_root)
        self._rebuild_system_prompt()

        # HOOKS-DYNAMIC-03: instanciar HookRuntime tolerante.
        try:
            from nyx.agent.services.hook_runtime import HookRuntime

            self._hooks: "HookRuntime | None" = HookRuntime()
        except Exception as exc:  # noqa: BLE001 -- hooks são extensão opcional
            logger.warning("HookRuntime falhou ao instanciar: %s; sem hooks dinâmicos", exc)
            self._hooks = None

    def _emit_state(self, state: str) -> None:
        """Atualiza estado interno e notifica observadores (UX-BUG-02B).

        Observabilidade não pode derrubar o loop: callback envolto em try/except
        com log de warning (gambiarra #17 — silent except — explicitamente coberta).
        """
        self._model_state = state
        if self._on_model_state is None:
            return
        try:
            self._on_model_state(state)
        except Exception as exc:  # noqa: BLE001 -- callback do usuário não deve derrubar loop
            logger.warning("on_model_state raised: %s", exc)

    def session_state(self) -> dict:
        """Métricas da sessão corrente para /debug session (OBSERVABILITY-01)."""
        return {
            "iter": self._session.iteration,
            "tokens_total": int(self._budget._last_pct * self._budget.max_tokens),
            "compactions": self._budget._compactions,
            "tool_durations": {k: list(v) for k, v in self._tool_durations.items()},
            "model_state": self._model_state,
        }

    def _rebuild_system_prompt(self) -> None:
        """Reconstrói system prompt com placeholders dinâmicos atuais.

        Gera duas variantes (PERF-INFERENCE-01):
        - self._system_prompt: completo (tools + memoria + repomap + summary).
        - self._system_prompt_compact: curto (~200 tokens) p/ turnos sem tools.
        """
        repo_map = ""
        try:
            touched = set(self._session._files_modified) | set(self._session._files_read)
            repo_map = self._repomap.render(
                touched={
                    str(Path(p).relative_to(self._project_root))
                    for p in touched
                    if Path(p).is_relative_to(self._project_root)
                }
            )
        except Exception as e:  # noqa: BLE001
            logger.debug("repomap render falhou: %s", e)
        summary = getattr(self._session, "summary", "") if hasattr(self, "_session") else ""
        # CTX-04: bloco do plano ativo (opt-in, vazio quando não existe).
        active_plan_block = ""
        try:
            from nyx.agent.active_plan import render_active_plan_block

            active_plan_block = render_active_plan_block()
        except Exception as e:  # noqa: BLE001
            logger.debug("active_plan render falhou: %s", e)
        prompt = build_system_prompt(
            self._project_root,
            self._tool_names,
            memory_files=self._memory_bundle,
            repo_map=repo_map,
            session_summary=summary,
            active_plan=active_plan_block,
        )
        if self._guide_ctx:
            prompt += self._guide_ctx
        self._system_prompt = prompt
        self._system_prompt_compact = build_system_prompt_compact(self._project_root)

    async def run(self, user_input: str) -> SessionStatus:
        """Executa o ciclo completo para um input do usuário."""
        self._session.add_user(user_input)
        self._session.iteration = 0
        self._consecutive_skips = 0
        self._has_results = False
        # NYX-PROMPT-REINJECT-01: preserva o pedido original do turno para o
        # reminder periodico. tool_calls_count Não reseta entre turnos: cadencia
        # se mantem ao longo da sessão (mais drift quanto mais longa a sessão).
        self._original_input = user_input
        self._lang_drift_streak = 0
        self._force_reminder = False
        self._reminder_extra = None

        # NYX-GSD-CHECKPOINTS-01: registra pedido inicial em progress.md.
        self._gsd.user_input(user_input)

        # HOOKS-DYNAMIC-03: UserPromptSubmit antes da primeira iteração.
        if self._hooks is not None:
            try:
                self._hooks.run("UserPromptSubmit", {"content": user_input})
            except Exception as exc:  # noqa: BLE001 -- hook não derruba loop
                logger.warning("hook UserPromptSubmit falhou: %s", exc)

        if self._model_state != "warm":
            self._emit_state("warming")

        # HOOKS-DYNAMIC-03: envelope try/finally para garantir Stop hook
        # mesmo em retorno antecipado, exceção ou MAX_ITERATIONS.
        status: SessionStatus | None = None
        try:
            status = await self._run_iterations(user_input)
            return status
        finally:
            if self._hooks is not None:
                try:
                    summary = status.summary if status is not None else ""
                    self._hooks.run("Stop", {"turn_summary": summary[:500]})
                except Exception as exc:  # noqa: BLE001 -- hook não derruba loop
                    logger.warning("hook Stop falhou: %s", exc)

    async def _run_iterations(self, user_input: str) -> SessionStatus:
        """Corpo do loop plan-execute-observe (HOOKS-DYNAMIC-03). Separado
        de run() apenas para envelope try/finally do Stop hook."""
        for i in range(self._max_iterations):
            self._session.iteration = i + 1
            # NYX-PROMPT-REINJECT-01: zera tool calls da iteração para drift
            # de alucinação (afirmar sucesso sem tool no turno corrente).
            self._tool_calls_this_turn = 0
            logger.info("[loop] iteração %d/%d", i + 1, self._max_iterations)

            if self._budget.should_compact(self._session):
                level = self._budget.get_compaction_level(self._session)
                pct_before = self._budget._history_pct(self._session)
                tokens_before = int(pct_before * self._budget.max_tokens)
                logger.info("[loop] compactação nível %d", level)
                self._budget.compact_history(self._session)
                pct_after = self._budget._history_pct(self._session)
                tokens_after = int(pct_after * self._budget.max_tokens)
                tokens_removed = max(0, tokens_before - tokens_after)
                if self._on_compaction is not None:
                    self._on_compaction(level, tokens_removed, pct_before, pct_after)

            response = await self._call_llm()
            if "error" not in response and self._model_state != "warm":
                self._emit_state("warm")
            if "error" in response:
                self._emit_state("cold")
                error_msg = response["error"]
                self._diagnostics.record_error("llm", error_msg[:200])
                if (
                    "connection" in error_msg.lower()
                    or "disconnect" in error_msg.lower()
                    or "Extra data" in error_msg
                    or "500" in error_msg
                ):
                    logger.warning("[loop] LLM caiu, tentando recovery...")
                    recovered = await self._try_recovery()
                    if recovered:
                        response = await self._call_llm()
                        if "error" not in response:
                            logger.info("[loop] recovery OK, continuando")
                        else:
                            logger.error("[loop] recovery falhou: %s", response.get("error"))
                            if self._has_results:
                                return SessionStatus(
                                    state=SessionState.DONE,
                                    iterations=i + 1,
                                    summary=self._build_force_done_summary(),
                                )
                            return SessionStatus(
                                state=SessionState.ERROR,
                                iterations=i + 1,
                                summary=error_msg,
                            )
                    else:
                        if self._has_results:
                            return SessionStatus(
                                state=SessionState.DONE,
                                iterations=i + 1,
                                summary=self._build_force_done_summary(),
                            )
                        return SessionStatus(
                            state=SessionState.ERROR,
                            iterations=i + 1,
                            summary=error_msg,
                        )
                else:
                    logger.error("[loop] erro LLM: %s", error_msg)
                    return SessionStatus(
                        state=SessionState.ERROR,
                        iterations=i + 1,
                        summary=error_msg,
                    )

            tool_calls = response.get("tool_calls", [])

            if tool_calls:
                status = self._execute_tool_calls(tool_calls, i + 1)
                if status:
                    return status
                continue

            content = response.get("content", "")
            if content:
                # NYX-PROMPT-REINJECT-01: detecta drift de idioma/alucinação
                # no texto do assistente antes do parser fallback. Drift força
                # reminder no próximo _call_llm.
                try:
                    drifted, hint = self._detect_drift(content)
                    if drifted:
                        self._force_reminder = True
                        self._reminder_extra = hint
                        logger.info("[reinject] drift detectado: %s", (hint or "")[:80])
                except Exception as exc:  # noqa: BLE001 -- drift e best-effort
                    logger.debug("[reinject] _detect_drift erro: %s", exc)
                parse_result = self._parser.parse(content)
                if parse_result.success and parse_result.action:
                    action = parse_result.action
                    logger.info(
                        "[loop] parser fallback: %s (nível %s)",
                        action.action_type.value,
                        parse_result.level.value,
                    )
                    status = self._execute_parsed_action(action, i + 1)
                    if status:
                        return status
                    continue

                forge = detect_forged_success(content, self._session.history)
                final_content = content
                if forge.warnings:
                    self._diagnostics.record_warning("forge", forge.warnings[0])
                    aviso = "[atenção: resposta não verificada por tool]"
                    final_content = f"{content}\n\n{aviso}"
                self._session.add_assistant(final_content)
                self._gsd_record_turn_state("done")
                return SessionStatus(
                    state=SessionState.DONE,
                    iterations=i + 1,
                    summary=final_content,
                )

        self._gsd_record_turn_state("max_iter")
        return SessionStatus(
            state=SessionState.MAX_ITERATIONS,
            iterations=self._max_iterations,
            summary=f"Atingiu limite de {self._max_iterations} iterações",
        )

    def _gsd_record_turn_state(self, label: str = "turn") -> None:
        """NYX-GSD-CHECKPOINTS-01: registra snapshot do estado runtime no progress.md."""
        s = self._session
        msg = (
            f"{label} iter={s.iteration} lidos={s.files_read_count} "
            f"modif={s.files_modified_count}"
        )
        self._gsd.session(msg)

    def _build_force_done_summary(self) -> str:
        """Gera resumo real do que foi feito ao forçar done."""
        parts: list[str] = []
        for entry in reversed(self._session.history):
            if entry.tool_name and entry.tool_result and "OK:" in entry.tool_result:
                parts.append(entry.tool_result.split(". Se a tarefa")[0])
                break
            if entry.tool_name and entry.tool_result and entry.is_key_decision:
                parts.append(entry.tool_result[:200])
                break
        modified = sorted(self._session._files_modified)
        if modified:
            parts.append(f"Arquivos: {', '.join(modified[:5])}")
        if not parts:
            parts.append("Tarefa processada")
        return ". ".join(parts)

    @property
    def tools_count(self) -> int:
        return self._tools.tool_count

    @property
    def session(self) -> CodeSession:
        return self._session

    @property
    def budget(self) -> ContextBudget:
        return self._budget

    @property
    def parser_stats(self) -> dict[str, Any]:
        return self._parser.stats

    @property
    def permissions(self) -> PermissionChecker:
        return self._permissions

    @property
    def diagnostics(self) -> DiagnosticTracking:
        return self._diagnostics

    @property
    def tool_summary(self) -> ToolUseSummary:
        return self._tool_summary

    def reset(self) -> None:
        self._session.reset()
        self._parser.reset_stats()
        self._permissions.reset_session()
        self._last_action = None
        self._consecutive_skips = 0
        self._has_results = False
        # NYX-PROMPT-REINJECT-01: reset zera contadores da sessão.
        self._tool_calls_count = 0
        self._tool_calls_this_turn = 0
        self._last_reminder_at_count = -1
        self._lang_drift_streak = 0
        self._force_reminder = False
        self._reminder_extra = None
        self._original_input = None

    async def maybe_summarize(self) -> bool:
        """Atualiza o resumo da sessão se o batch fechou. Fire-and-forget friendly."""
        if not self._summarizer.should_summarize(self._session):
            return False
        try:
            summary = await self._summarizer.update(self._session)
        except Exception as e:  # noqa: BLE001 -- resumo falho não derruba loop
            logger.warning("summarizer: erro inesperado: %s", e)
            return False
        if summary:
            self._summarizer.write_to_disk(self._session_id, summary)
            self._rebuild_system_prompt()
        return bool(summary)

    async def close(self) -> None:
        """Libera recursos (httpx client)."""
        if self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    def get_context_info(self) -> dict:
        """Retorna info do budget para exibição no CLI."""
        history = self._session.get_compressed_history()
        return self._budget.estimate(self._system_prompt, history)


# "O loop é a essência da computação." -- Alan Turing
