"""AgentLoop -- Ciclo plan-execute-observe do Nyx.

Fluxo integrado (P1-F):
1. Recebe pedido do usuário
2. ContextBudget verifica budget -> compacta se necessário
3. Envia ao proxy (/v1/chat/completions com tools)
4. Se tool_calls:
   a. PermissionChecker -> confirma/nega
   b. RepetitionDetector -> SKIP/FORCE_DONE se repetido
   c. Executa tool, coleta resultado, volta ao 2
5. Se texto puro:
   a. ActionParser (7 níveis fallback)
   b. Se extraiu ação: executa como tool call
   c. Se não: mostra texto ao usuário
6. Se done(): salva sessão, termina
7. Se max_iterations: force_done
"""

from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

import httpx

from nyx.agent.context import ContextBudget, render_context_bar
from nyx.agent.models import (
    ActionResult,
    ActionType,
    AgentAction,
    SessionState,
    SessionStatus,
)
from nyx.agent.parser import ActionParser
from nyx.agent.permissions import PermissionChecker, PermissionLevel
from nyx.agent.preflight import check as preflight_check
from nyx.agent.prompt import build_claude_md_context, build_system_prompt
from nyx.agent.tools.plan_mode import is_tool_allowed_in_plan_mode
from nyx.agent.repetition import SkipStrategy, get_skip_strategy
from nyx.agent.services.diagnostics import DiagnosticTracking
from nyx.agent.services.tool_use_summary import ToolUseSummary
from nyx.agent.session import CodeSession
from nyx.agent.streaming import StreamingCollector
from nyx.agent.tools.registry import ToolRegistry
from nyx.agent.validator import validate as post_validate

from nyx.config.defaults import MAX_ITERATIONS as MAX_ITERATIONS_DEFAULT

logger = logging.getLogger("nyx.agent")

LLM_TIMEOUT = 600

PermissionCallback = Callable[[str, str, dict[str, str]], bool]

ACTION_TO_TOOL: dict[ActionType, str] = {
    ActionType.READ_FILE: "read_file",
    ActionType.CREATE_FILE: "write_file",
    ActionType.WRITE_FILE: "write_file",
    ActionType.EDIT_FILE: "edit_file",
    ActionType.RUN_COMMAND: "run_command",
    ActionType.GLOB: "glob",
    ActionType.SEARCH: "search",
    ActionType.LIST_FILES: "list_files",
    ActionType.TODO_WRITE: "todo_write",
    ActionType.WEB_FETCH: "web_fetch",
    ActionType.WEB_SEARCH: "web_search",
    ActionType.DONE: "done",
}

PARAM_REMAP: dict[str, dict[str, str]] = {
    "read_file": {"path": "file_path"},
    "write_file": {"path": "file_path"},
    "edit_file": {"path": "file_path"},
    "run_command": {"cmd": "command"},
    "search": {"pattern": "pattern"},
    "glob": {"pattern": "pattern"},
    "list_files": {"path": "path"},
}


def _remap_params(tool_name: str, params: dict[str, str]) -> dict[str, str]:
    """Remapeia nomes de parâmetros do parser para os esperados pela tool."""
    mapping = PARAM_REMAP.get(tool_name, {})
    result: dict[str, str] = {}
    for k, v in params.items():
        new_key = mapping.get(k, k)
        result[new_key] = v
    return result


class AgentLoop:
    def __init__(
        self,
        project_root: str,
        proxy_url: str = "http://127.0.0.1:11436",
        model: str = "qwen3:4b",
        max_iterations: int = MAX_ITERATIONS_DEFAULT,
        on_token: Any = None,
        on_tool: Any = None,
        on_tool_result: Any = None,
        on_permission: PermissionCallback | None = None,
        streaming: bool = True,
    ) -> None:
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
        self._streaming = streaming

        self._parser = ActionParser()
        self._budget = ContextBudget()
        self._permissions = PermissionChecker()
        self._last_action: AgentAction | None = None
        self._consecutive_skips: int = 0
        self._has_results: bool = False

        self._collector = StreamingCollector(on_token=on_token) if streaming and on_token else None
        self._http_client: httpx.AsyncClient | None = None
        self._diagnostics = DiagnosticTracking()
        self._tool_summary = ToolUseSummary()

        tool_names = [t["function"]["name"] for t in self._tools.tool_defs]
        self._system_prompt = build_system_prompt(project_root, tool_names)
        claude_ctx = build_claude_md_context(project_root)
        if claude_ctx:
            self._system_prompt += claude_ctx

    async def run(self, user_input: str) -> SessionStatus:
        """Executa o ciclo completo para um input do usuário."""
        self._session.add_user(user_input)
        self._session.iteration = 0
        self._consecutive_skips = 0
        self._has_results = False

        for i in range(self._max_iterations):
            self._session.iteration = i + 1
            logger.info("[loop] iteração %d/%d", i + 1, self._max_iterations)

            if self._budget.should_compact(self._session):
                level = self._budget.get_compaction_level(self._session)
                logger.info("[loop] compactação nível %d", level)
                self._budget.compact_history(self._session)

            response = await self._call_llm()
            if "error" in response:
                error_msg = response["error"]
                self._diagnostics.record_error("llm", error_msg[:200])
                # Auto-recovery: se conexão falhou ou Ollama crashou, tenta retentar
                if ("connection" in error_msg.lower() or "disconnect" in error_msg.lower()
                        or "Extra data" in error_msg or "500" in error_msg):
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

                self._session.add_assistant(content)
                return SessionStatus(
                    state=SessionState.DONE,
                    iterations=i + 1,
                    summary=content,
                )

        return SessionStatus(
            state=SessionState.MAX_ITERATIONS,
            iterations=self._max_iterations,
            summary=f"Atingiu limite de {self._max_iterations} iterações",
        )

    def _execute_tool_calls(self, tool_calls: list[dict], iteration: int) -> SessionStatus | None:
        """Executa tool calls do LLM. Retorna SessionStatus se done/force_done."""
        for tc in tool_calls:
            name = tc["name"]
            args = tc["arguments"]

            if self._on_tool:
                self._on_tool(name, args)

            if self._tools.is_done(name):
                summary = args.get("summary", "Tarefa concluída.")
                self._session.add_tool_call(name, args, summary, is_key=True)
                return SessionStatus(
                    state=SessionState.DONE,
                    iterations=iteration,
                    summary=summary,
                )

            if not is_tool_allowed_in_plan_mode(name):
                logger.warning("[loop] bloqueado por plan_mode: %s", name)
                self._session.add_tool_call(name, args, f"Bloqueado: modo planejamento ativo. Use exit_plan_mode primeiro.")
                continue

            perm = self._permissions.check(name, args)
            if perm == PermissionLevel.DENY:
                logger.warning("[loop] permissão negada: %s", name)
                self._session.add_tool_call(name, args, f"Permissão negada para {name}")
                continue

            if perm in (PermissionLevel.CONFIRM_ONCE, PermissionLevel.ALWAYS_CONFIRM):
                if self._on_permission:
                    approved = self._on_permission(perm, name, args)
                    if not approved:
                        self._session.add_tool_call(name, args, f"Usuário negou: {name}")
                        continue
                    if perm == PermissionLevel.CONFIRM_ONCE:
                        self._permissions.mark_confirmed(name)

            action = AgentAction(
                action_type=ActionType(name) if name in [a.value for a in ActionType] else ActionType.DONE,
                params=args,
            )
            skip = self._check_repetition(action)
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

            result = self._tools.execute(name, args)
            self._tool_summary.track(name, args)

            vr = post_validate(name, args, result)
            for warn in vr.warnings:
                logger.info("[loop] validator aviso para %s: %s", name, warn)

            if not result.success:
                self._diagnostics.record_warning("tool", f"{name}: {result.error[:120]}")

            if self._on_tool_result:
                self._on_tool_result(name, result.output if result.success else result.error)

            self._session.add_tool_call(
                name, args,
                result.output if result.success else result.error,
                is_key=name in ("write_file", "edit_file", "create_file", "run_command"),
            )
            self._session.track_files(result.files_read, result.files_modified)
            self._last_action = action
            self._consecutive_skips = 0
            if result.success:
                self._has_results = True

        return None

    def _execute_parsed_action(self, action: AgentAction, iteration: int) -> SessionStatus | None:
        """Executa ação extraída pelo parser fallback."""
        if action.action_type == ActionType.DONE:
            summary = action.params.get("summary", "Tarefa concluída.")
            self._session.add_tool_call("done", action.params, summary, is_key=True)
            return SessionStatus(
                state=SessionState.DONE,
                iterations=iteration,
                summary=summary,
            )

        tool_name = ACTION_TO_TOOL.get(action.action_type)
        if not tool_name:
            logger.warning("[loop] sem tool para %s", action.action_type.value)
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

        result = self._tools.execute(tool_name, remapped)

        vr = post_validate(tool_name, remapped, result)
        for warn in vr.warnings:
            logger.info("[loop] validator aviso para %s: %s", tool_name, warn)

        self._session.add_tool_call(
            tool_name, remapped,
            result.output if result.success else result.error,
            is_key=tool_name in ("write_file", "edit_file", "create_file", "run_command"),
        )
        self._session.track_files(result.files_read, result.files_modified)
        self._last_action = action
        self._consecutive_skips = 0
        if result.success:
            self._has_results = True

        return None

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

    def _check_repetition(self, action: AgentAction) -> SessionStatus | None:
        """Verifica repetição e retorna FORCE_DONE se necessário."""
        strategy = get_skip_strategy(
            action=action,
            last_action=self._last_action,
            history=self._session.history,
            files_modified=self._session._files_modified,
            consecutive_skips=self._consecutive_skips,
            has_results=self._has_results,
        )

        if strategy == SkipStrategy.FORCE_DONE:
            summary = self._build_force_done_summary()
            logger.info("[loop] FORCE_DONE por repetição: %s", summary[:80])
            return SessionStatus(
                state=SessionState.DONE,
                iterations=self._session.iteration,
                summary=summary,
            )

        if strategy == SkipStrategy.SKIP:
            self._consecutive_skips += 1
            logger.info("[loop] SKIP repetição (%d consecutivos)", self._consecutive_skips)
            self._session.add_tool_call(
                action.action_type.value, action.params,
                f"Ação repetida ignorada ({self._consecutive_skips}x)",
            )
            return None

        return None

    async def _call_llm(self) -> dict[str, Any]:
        """Envia request ao proxy com histórico e tools.

        Estratégia de contexto para GPU limitada:
        - Iteração 1: histórico completo (só tem user msg)
        - Iteração 2+: apenas últimas 4 mensagens (user + tool_call + result + resposta)
        - Compactação se budget > 40%
        """
        messages = [{"role": "system", "content": self._system_prompt}]
        history_msgs = self._session.to_messages()

        if len(history_msgs) > 4:
            # Após primeira iteração: manter apenas mensagens recentes
            messages.extend(history_msgs[-4:])
            logger.info("[loop] contexto reduzido: %d/%d msgs", 4, len(history_msgs))
        elif self._budget.should_compact(self._session):
            compacted = self._budget.compact_history(self._session)
            if compacted:
                messages.append({"role": "user", "content": f"[contexto compactado]\n{compacted}"})
            recent_msgs = history_msgs[-4:]
            messages.extend(recent_msgs)
        else:
            messages.extend(history_msgs)

        selected_tools = self._select_tools_for_context(messages)
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
                return {"error": f"Resposta sem choices: {str(data)[:200]}"}

            msg = data["choices"][0]["message"]
            tc = msg.get("tool_calls", [])
            content = msg.get("content", "")

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
                result["tool_calls"].append({
                    "name": fn.get("name", ""),
                    "arguments": args,
                })

            return result

        except httpx.TimeoutException:
            return {"error": "Timeout ao chamar LLM (proxy não respondeu)"}
        except Exception as e:
            return {"error": str(e)}

    async def _try_recovery(self) -> bool:
        """Tenta reiniciar o modelo Ollama após crash."""
        import asyncio
        ollama_base = self._proxy_url.replace("/v1", "").rstrip("/")
        # Extrair URL do Ollama a partir da proxy (porta -1)
        # Fallback: tentar aquecer via proxy
        logger.info("[recovery] Aguardando Ollama reiniciar...")
        for attempt in range(3):
            await asyncio.sleep(5)
            try:
                async with httpx.AsyncClient(timeout=30) as client:
                    r = await client.get(f"{ollama_base}/v1/models")
                    if r.status_code == 200:
                        logger.info("[recovery] Proxy respondendo, tentando aquecer modelo...")
                        # Aquecer modelo com request simples
                        warmup = await client.post(
                            f"{ollama_base}/v1/chat/completions",
                            json={"model": self._model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5},
                            timeout=120,
                        )
                        if warmup.status_code == 200:
                            logger.info("[recovery] Modelo aquecido, retomando")
                            return True
            except Exception as e:
                logger.warning("[recovery] Tentativa %d falhou: %s", attempt + 1, str(e)[:60])
        return False

    # Tools core: sempre enviadas (essenciais para qualquer tarefa)
    _CORE_TOOLS = {
        "read_file", "write_file", "edit_file", "run_command",
        "search", "glob", "list_files", "done",
    }

    # Keywords que ativam tools condicionais
    _TOOL_KEYWORDS: dict[str, set[str]] = {
        "notebook_edit": {"notebook", "ipynb", "jupyter"},
        "web_fetch": {"url", "http", "fetch", "download", "site", "web"},
        "web_search": {"pesquis", "web", "google", "search"},
        "todo_write": {"todo", "tarefa", "task", "lista"},
        "agent": {"agent", "subagent", "delegar"},
        "enter_plan_mode": {"plano", "plan", "planej"},
        "exit_plan_mode": {"plano", "plan"},
        "ask_user": {"perguntar", "confirmar", "ask"},
        "analyze": {"analis", "analyz", "complex"},
        "patch": {"patch", "diff", "aplicar"},
        "multi_edit": {"multi", "vários arquivos", "batch"},
        "enter_worktree": {"worktree", "isolar"},
        "exit_worktree": {"worktree"},
        "repl": {"repl", "executar python", "python -c"},
        "tool_search": {"tool_search", "buscar tool"},
        "skill": {"skill", "habilidade"},
        "send_message": {"mensagem", "message"},
        "brief": {"resumo", "brief"},
        "config": {"config", "configurar"},
        "sleep": {"esperar", "aguardar", "sleep"},
        "task_create": {"tarefa", "task"},
        "task_update": {"tarefa", "task"},
        "task_list": {"tarefa", "task"},
        "task_get": {"tarefa", "task"},
        "task_output": {"tarefa", "task"},
        "task_stop": {"tarefa", "task"},
    }

    def _select_tools_for_context(self, messages: list[dict]) -> list[dict]:
        """Seleciona tools relevantes baseado no contexto da conversa."""
        # Extrair texto recente (ignorar system prompt que contém nomes de tools)
        text_parts: list[str] = []
        for msg in messages[-4:]:
            if msg.get("role") == "system":
                continue
            content = msg.get("content", "")
            if content:
                text_parts.append(content.lower())
        context_text = " ".join(text_parts)

        # Sempre incluir tools core
        selected_names = set(self._CORE_TOOLS)

        # Adicionar tools condicionais por keyword
        for tool_name, keywords in self._TOOL_KEYWORDS.items():
            if any(kw in context_text for kw in keywords):
                selected_names.add(tool_name)

        # Incluir texto do user input do session (caso messages não tenha user)
        for entry in self._session.history[-3:]:
            if entry.role == "user":
                for tool_name, keywords in self._TOOL_KEYWORDS.items():
                    if any(kw in entry.content.lower() for kw in keywords):
                        selected_names.add(tool_name)

        # Se já houve tool calls na sessão, incluir tools usadas
        for entry in self._session.history:
            if entry.tool_name:
                selected_names.add(entry.tool_name)

        # Filtrar tool_defs para apenas as selecionadas
        all_defs = self._tools.tool_defs
        selected = [td for td in all_defs if td["function"]["name"] in selected_names]

        logger.info("[loop] tools selecionadas: %d/%d", len(selected), len(all_defs))
        return selected

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
