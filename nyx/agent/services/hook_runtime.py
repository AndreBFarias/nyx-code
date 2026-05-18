"""HookRuntime — hooks dinâmicos por evento (HOOKS-DYNAMIC-01).

Carrega `~/.nyx/settings.json` seção `hooks` e expõe `run(event, payload)`
que executa hooks shell/skill com timeout, matcher regex, block_on_failure.

Eventos suportados:
  - PreToolUse, PostToolUse: matcher casa contra nome da tool.
  - UserPromptSubmit, Stop: matcher opcional contra texto.

Schema settings.json:

    {
      "hooks": {
        "PreToolUse": [
          {
            "command": "python3 /path/to/guard.py",
            "matcher": "write_file|edit_file",
            "timeout": 5,
            "block_on_failure": true
          },
          { "command": "skill:my-skill", "matcher": ".*", "timeout": 10 }
        ]
      }
    }

ADR-001 (Local First): hooks são locais; nada de URL remota.
"""

from __future__ import annotations

import json
import re
import shlex
import subprocess as _sp
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.hooks")

DEFAULT_TIMEOUT_S = 30
MAX_TIMEOUT_S = 300
ENV_WHITELIST = ("PATH", "HOME", "LANG", "LC_ALL", "USER", "SHELL")
SETTINGS_PATH = Path.home() / ".nyx" / "settings.json"

EVENTS = ("PreToolUse", "PostToolUse", "UserPromptSubmit", "Stop")


@dataclass
class HookSpec:
    event: str
    command: str
    matcher: re.Pattern[str] | None = None
    timeout: int = DEFAULT_TIMEOUT_S
    block_on_failure: bool = False


@dataclass
class HookResult:
    ok: bool
    blocked: bool = False
    output: str = ""
    error: str | None = None


class HookRuntime:
    def __init__(self, settings_path: str | Path = SETTINGS_PATH) -> None:
        self.settings_path = Path(settings_path)
        self.hooks: dict[str, list[HookSpec]] = {ev: [] for ev in EVENTS}
        self.load()

    def load(self) -> None:
        self.hooks = {ev: [] for ev in EVENTS}
        if not self.settings_path.is_file():
            return
        try:
            data = json.loads(self.settings_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.warning("settings.json inválido (%s): %s", self.settings_path, exc)
            return
        hooks_cfg = (data or {}).get("hooks") or {}
        for event, entries in hooks_cfg.items():
            if event not in EVENTS:
                logger.warning("hook event desconhecido: %s — ignorado", event)
                continue
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict) or "command" not in entry:
                    continue
                matcher_str = entry.get("matcher")
                try:
                    matcher = re.compile(matcher_str) if matcher_str else None
                except re.error as exc:
                    logger.warning("hook matcher regex inválido (%s): %s", matcher_str, exc)
                    matcher = None
                timeout = min(
                    int(entry.get("timeout") or DEFAULT_TIMEOUT_S),
                    MAX_TIMEOUT_S,
                )
                self.hooks[event].append(
                    HookSpec(
                        event=event,
                        command=str(entry["command"]),
                        matcher=matcher,
                        timeout=timeout,
                        block_on_failure=bool(entry.get("block_on_failure", False)),
                    )
                )

    def run(self, event: str, payload: dict[str, Any]) -> list[HookResult]:
        """Executa hooks aplicáveis ao evento; retorna resultados na ordem."""
        results: list[HookResult] = []
        for spec in self.hooks.get(event, []):
            target = (
                str(payload.get("tool_name") or payload.get("content") or "")
            )
            if spec.matcher is not None and not spec.matcher.search(target):
                continue
            results.append(self._invoke(spec, payload))
            if results[-1].blocked:
                break
        return results

    def _invoke(self, spec: HookSpec, payload: dict[str, Any]) -> HookResult:
        if spec.command.startswith("skill:"):
            # Marcador para integração futura via Skill tool; MVP loga + retorna OK.
            logger.info("hook skill (placeholder) %s payload=%s", spec.command, payload)
            return HookResult(ok=True)
        try:
            env = self._clean_env()
            stdin_payload = json.dumps(payload, ensure_ascii=False)
            proc = _sp.run(
                shlex.split(spec.command),
                input=stdin_payload,
                capture_output=True,
                text=True,
                timeout=spec.timeout,
                env=env,
                check=False,
            )
        except _sp.TimeoutExpired:
            logger.warning(
                "hook %s (%s) timeout em %ds", spec.event, spec.command, spec.timeout
            )
            return HookResult(
                ok=False,
                blocked=spec.block_on_failure,
                error=f"timeout {spec.timeout}s",
            )
        except FileNotFoundError as exc:
            logger.warning("hook %s comando não encontrado: %s", spec.event, exc)
            return HookResult(ok=False, blocked=spec.block_on_failure, error=str(exc))
        except Exception as exc:  # noqa: BLE001 -- hook pode falhar de muitas formas
            logger.warning("hook %s falhou: %s", spec.event, exc)
            return HookResult(ok=False, blocked=spec.block_on_failure, error=str(exc))

        ok = proc.returncode == 0
        return HookResult(
            ok=ok,
            blocked=(spec.block_on_failure and not ok),
            output=(proc.stdout or "").strip(),
            error=(proc.stderr or "").strip() if not ok else None,
        )

    @staticmethod
    def _clean_env() -> dict[str, str]:
        import os as _os

        return {k: _os.environ[k] for k in ENV_WHITELIST if k in _os.environ}
