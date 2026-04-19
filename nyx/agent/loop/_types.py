"""Tipos públicos do pacote nyx.agent.loop."""

from __future__ import annotations

from collections.abc import Callable

from nyx.agent.models import SessionState, SessionStatus

PermissionCallback = Callable[[str, str, dict[str, str]], bool]

__all__ = ["PermissionCallback", "SessionState", "SessionStatus"]


# "Nomear é o primeiro ato do engenheiro." -- Hoare (paráfrase)
