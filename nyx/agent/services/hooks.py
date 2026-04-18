"""Tool Hooks -- Callbacks pré/pós execução de tools.

Permite registrar callbacks que executam antes e depois de cada tool.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger("nyx.services.hooks")

PreHookResult = dict[str, Any]
PreHook = Callable[[str, dict[str, Any]], PreHookResult | None]
PostHook = Callable[[str, dict[str, Any], Any], None]


class ToolHooks:
    """Registry de hooks pré/pós execução de tools."""

    def __init__(self) -> None:
        self._pre_hooks: list[PreHook] = []
        self._post_hooks: list[PostHook] = []

    def register_pre(self, hook: PreHook) -> None:
        """Registra hook que executa antes da tool.

        Hook recebe (tool_name, args) e pode retornar:
        - None: continua execução normal
        - {"block": True, "reason": "..."}: bloqueia execução
        - {"modify_args": {...}}: modifica argumentos
        """
        self._pre_hooks.append(hook)

    def register_post(self, hook: PostHook) -> None:
        """Registra hook que executa depois da tool.

        Hook recebe (tool_name, args, result).
        """
        self._post_hooks.append(hook)

    def run_pre(self, tool_name: str, args: dict[str, Any]) -> PreHookResult | None:
        """Executa todos os pre-hooks. Retorna bloqueio se algum bloquear."""
        for hook in self._pre_hooks:
            try:
                result = hook(tool_name, args)
                if result and result.get("block"):
                    logger.info("[hook] pre-hook bloqueou %s: %s", tool_name, result.get("reason", ""))
                    return result
                if result and "modify_args" in result:
                    args.update(result["modify_args"])
            except Exception as e:
                logger.warning("[hook] erro em pre-hook para %s: %s", tool_name, e)
        return None

    def run_post(self, tool_name: str, args: dict[str, Any], result: Any) -> None:
        """Executa todos os post-hooks."""
        for hook in self._post_hooks:
            try:
                hook(tool_name, args, result)
            except Exception as e:
                logger.warning("[hook] erro em post-hook para %s: %s", tool_name, e)

    @property
    def pre_count(self) -> int:
        return len(self._pre_hooks)

    @property
    def post_count(self) -> int:
        return len(self._post_hooks)


def create_logging_hook() -> PostHook:
    """Cria hook que loga toda execução de tool."""

    def _log(tool_name: str, args: dict[str, Any], result: Any) -> None:
        success = getattr(result, "success", True)
        logger.info("[hook:log] %s(%s) -> %s", tool_name, str(args)[:60], "OK" if success else "ERRO")

    return _log


def create_path_guard_hook(denied_patterns: list[str]) -> PreHook:
    """Cria hook que bloqueia tools em paths específicos."""

    def _guard(tool_name: str, args: dict[str, Any]) -> PreHookResult | None:
        path = args.get("file_path", args.get("path", ""))
        if not path:
            return None
        for pattern in denied_patterns:
            if pattern in path:
                return {"block": True, "reason": f"Path bloqueado: {pattern}"}
        return None

    return _guard


# "Os ganchos seguram o que a gravidade tenta derrubar." -- provérbio alpinista
