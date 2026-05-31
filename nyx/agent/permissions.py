"""Permission Model configurável para o Nyx Agent.

Port de Luna src/skills/code_agent/permissions.py.

4 níveis:
- auto_approve: executa sem perguntar
- confirm_once: confirma primeira vez, auto-aprova na sessão
- always_confirm: confirma toda vez
- deny: bloqueia sempre

Config em ~/.nyx/permissions.json.

Override por env (NYX-AUTO-APPROVE-01):
- NYX_AUTO_APPROVE=1 promove CONFIRM_ONCE -> AUTO (executa sem prompt).
  DENY permanece ativo. Uso: cockpit Control API e automação sem TTY.
  Opt-in: nada acontece por default; precisa setar a env explicitamente.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.permissions")

PERMISSIONS_FILE = Path.home() / ".nyx" / "permissions.json"

DEFAULT_PERMISSIONS: dict[str, Any] = {
    "auto_approve": [
        "read_file",
        "search",
        "list_files",
        "glob",
        "analyze",
        "done",
    ],
    "confirm_once": [
        "edit_file",
        "create_file",
        "write_file",
        "patch",
    ],
    "always_confirm": [
        "run_command",
        "write_memory",
    ],
    "deny": [
        "run_command:rm -rf *",
        "run_command:sudo *",
    ],
    "allowed_paths": [],
    "denied_paths": [
        ".env",
        ".git/",
        "credentials/",
    ],
}


class PermissionLevel:
    AUTO = "auto_approve"
    CONFIRM_ONCE = "confirm_once"
    ALWAYS_CONFIRM = "always_confirm"
    DENY = "deny"


class PermissionChecker:
    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self._config = config or _load_permissions()
        self._confirmed_actions: set[str] = set()
        # TUI-MODE-BEHAVIOR-01 (SPRINT 308): modo bypass (Shift+Tab) auto-aprova
        # CONFIRM_ONCE em runtime -- igual ao NYX_AUTO_APPROVE/--auto-approve,
        # mas ligável/desligável pela TUI sem env. DENY e ALWAYS_CONFIRM mantêm
        # o prompt (mesma garantia do modo automatizado documentado no README).
        self._bypass: bool = False

    def set_bypass(self, on: bool) -> None:
        """Liga/desliga o auto-aprovar de CONFIRM_ONCE (modo bypass, SPRINT 308)."""
        self._bypass = bool(on)

    @property
    def bypass(self) -> bool:
        return self._bypass

    def check(self, action_type: str, params: dict[str, str] | None = None) -> str:
        params = params or {}

        if self._is_denied(action_type, params):
            return PermissionLevel.DENY

        if action_type in self._config.get("auto_approve", []):
            return PermissionLevel.AUTO

        path = params.get("path", "")
        if path and self._is_path_denied(path):
            return PermissionLevel.DENY

        # NYX-AUTO-APPROVE-01: env-driven bypass de CONFIRM_ONCE em automação.
        # DENY já bloqueou acima; aqui só promovemos confirmações silenciáveis.
        # ALWAYS_CONFIRM permanece exigindo prompt (intenção do usuário ao
        # marcar tool como sempre-confirmar é nunca-automatizar).
        # SPRINT 308: bypass em runtime (Shift+Tab) OU env (--auto-approve)
        # promovem CONFIRM_ONCE -> AUTO. ALWAYS_CONFIRM e DENY seguem intactos.
        auto_approve = self._bypass or os.environ.get("NYX_AUTO_APPROVE") == "1"

        if action_type in self._config.get("confirm_once", []):
            if action_type in self._confirmed_actions:
                return PermissionLevel.AUTO
            if auto_approve:
                return PermissionLevel.AUTO
            return PermissionLevel.CONFIRM_ONCE

        if action_type in self._config.get("always_confirm", []):
            return PermissionLevel.ALWAYS_CONFIRM

        return PermissionLevel.ALWAYS_CONFIRM

    def mark_confirmed(self, action_type: str) -> None:
        self._confirmed_actions.add(action_type)

    def reset_session(self) -> None:
        self._confirmed_actions.clear()

    def _is_denied(self, action_type: str, params: dict[str, str]) -> bool:
        for rule in self._config.get("deny", []):
            if ":" in rule:
                rule_type, rule_pattern = rule.split(":", 1)
                if action_type != rule_type:
                    continue
                cmd = params.get("cmd", "")
                if rule_pattern.endswith("*") and cmd.startswith(rule_pattern[:-1]):
                    return True
                if cmd == rule_pattern:
                    return True
            elif action_type == rule:
                return True
        return False

    def _is_path_denied(self, path: str) -> bool:
        for dp in self._config.get("denied_paths", []):
            if path.startswith(dp) or path == dp:
                return True
        allowed = self._config.get("allowed_paths", [])
        if allowed:
            return not any(path.startswith(ap) for ap in allowed)
        return False


def _load_permissions() -> dict[str, Any]:
    if not PERMISSIONS_FILE.exists():
        return dict(DEFAULT_PERMISSIONS)
    try:
        data = json.loads(PERMISSIONS_FILE.read_text(encoding="utf-8"))
        merged = dict(DEFAULT_PERMISSIONS)
        merged.update(data)
        return merged
    except Exception as e:
        logger.warning("Erro ao carregar permissions: %s, usando defaults", e)
        return dict(DEFAULT_PERMISSIONS)


def save_default_permissions() -> Path:
    PERMISSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PERMISSIONS_FILE.write_text(
        json.dumps(DEFAULT_PERMISSIONS, indent=4, ensure_ascii=False),
        encoding="utf-8",
    )
    return PERMISSIONS_FILE


# "Segurança e liberdade não são opostos, são complementos." -- Benjamin Franklin
