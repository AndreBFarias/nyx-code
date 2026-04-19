"""Mixin com métodos de iteração do AgentLoop.

Separa do _core.py para manter cada arquivo abaixo de 400 linhas.
Este mixin NÃO funciona isolado -- espera atributos injetados por AgentLoop
(_tools, _session, _permissions, _parser, _on_tool, _on_tool_result,
_on_permission, _last_action, _consecutive_skips, _has_results, etc.).
"""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from nyx.agent.loop._constants import ACTION_TO_TOOL, CORE_TOOLS, LLM_TIMEOUT, TOOL_KEYWORDS, _remap_params
from nyx.agent.models import (
    ActionType,
    AgentAction,
    SessionState,
    SessionStatus,
)
from nyx.agent.permissions import PermissionLevel
from nyx.agent.preflight import check as preflight_check
from nyx.agent.repetition import SkipStrategy, get_skip_strategy
from nyx.agent.tools.plan_mode import is_tool_allowed_in_plan_mode
from nyx.agent.validator import validate as post_validate

logger = logging.getLogger("nyx.agent")


class _IterationMixin:
    """Métodos de iteração/LLM extraídos de AgentLoop."""

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
                name,
                args,
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
            tool_name,
            remapped,
            result.output if result.success else result.error,
            is_key=tool_name in ("write_file", "edit_file", "create_file", "run_command"),
        )
        self._session.track_files(result.files_read, result.files_modified)
        self._last_action = action
        self._consecutive_skips = 0
        if result.success:
            self._has_results = True

        return None

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
                action.action_type.value,
                action.params,
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
                result["tool_calls"].append(
                    {
                        "name": fn.get("name", ""),
                        "arguments": args,
                    }
                )

            return result

        except httpx.TimeoutException:
            return {"error": "Timeout ao chamar LLM (proxy não respondeu)"}
        except Exception as e:
            return {"error": str(e)}

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
        """Seleciona tools relevantes baseado no contexto da conversa."""
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

        logger.info("[loop] tools selecionadas: %d/%d", len(selected), len(all_defs))
        return selected


# "A iteração revela o que a intenção escondia." -- anônimo
