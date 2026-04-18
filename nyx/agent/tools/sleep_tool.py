"""Tool: Sleep -- Espera controlada."""

from __future__ import annotations

import logging
import time
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.sleep")

MAX_SLEEP_SECONDS = 30


class SleepTool(RegisteredTool):
    action_type = ActionType.DONE

    tool_def = ToolDef(
        name="sleep",
        description=(f"Espera um número de segundos antes de continuar. Máximo {MAX_SLEEP_SECONDS}s."),
        parameters={
            "seconds": {"type": "integer", "description": "Segundos para esperar (1-30)"},
        },
        required=["seconds"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        try:
            seconds = int(params.get("seconds", 1))
        except (ValueError, TypeError):
            return ActionResult(success=False, error="Parâmetro 'seconds' deve ser inteiro")

        seconds = max(1, min(seconds, MAX_SLEEP_SECONDS))
        t0 = time.monotonic()
        time.sleep(seconds)
        elapsed = time.monotonic() - t0

        logger.info("Sleep: %ds (real: %.1fs)", seconds, elapsed)
        return ActionResult(success=True, output=f"Esperou {seconds}s (real: {elapsed:.1f}s)")


# "Paciência é a companheira da sabedoria." -- Santo Agostinho
