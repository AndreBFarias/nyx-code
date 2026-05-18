"""Tutorial de primeiro uso (ONBOARDING-01).

Invocado uma vez por instalação. Idempotência via ~/.nyx/.first_run_done.
Pula automaticamente em pipe/CI (stdin não-tty) e respeita timeout de 60s
nas pausas para nunca travar.
"""

from __future__ import annotations

import sys
from pathlib import Path

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.onboarding")

NYX_HOME = Path.home() / ".nyx"
FIRST_RUN_MARKER = NYX_HOME / ".first_run_done"
PAUSE_TIMEOUT_S = 60

STEPS: tuple[tuple[str, str], ...] = (
    (
        "Bem-vindo ao Nyx",
        "Codificadora local em PT-BR, 100% offline, sem telemetria. Sua máquina, suas regras.",
    ),
    (
        "Prompt livre",
        "Digite qualquer pergunta ou tarefa em português. Eu respondo e executo no seu workspace.",
    ),
    (
        "Slash commands",
        "Comandos começam com /. Exemplos: /help, /tools, /quit. Veja todos com /help.",
    ),
    (
        "Bypass de permissão",
        "Quando uma tool pedir permissão, responda [s/N]. Use Shift+Tab para alternar bypass.",
    ),
    (
        "Memória persistente",
        "Suas sessões ficam em ~/.nyx/sessions/. Use /resume para retomar a última, ou /resume list para escolher.",
    ),
)


def _timed_input(prompt: str, timeout: int = PAUSE_TIMEOUT_S) -> str | None:
    """input() com timeout via SIGALRM (Linux/macOS). Retorna None se EOF ou timeout."""
    import signal

    def _handler(_signum: int, _frame: object) -> None:  # noqa: D401
        raise TimeoutError

    if not hasattr(signal, "SIGALRM"):
        try:
            return input(prompt)
        except (EOFError, KeyboardInterrupt):
            return None

    old = signal.signal(signal.SIGALRM, _handler)  # type: ignore[arg-type]
    signal.alarm(timeout)
    try:
        return input(prompt)
    except (TimeoutError, EOFError, KeyboardInterrupt):
        return None
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def should_run_tutorial(skip_flag: bool) -> bool:
    """True quando primeira execução e stdin é tty (ONBOARDING-01)."""
    if skip_flag:
        return False
    if FIRST_RUN_MARKER.exists():
        return False
    return sys.stdin.isatty()


def mark_done() -> None:
    """Cria ~/.nyx/.first_run_done idempotentemente."""
    try:
        NYX_HOME.mkdir(parents=True, exist_ok=True)
        FIRST_RUN_MARKER.touch(exist_ok=True)
    except OSError as exc:
        logger.warning("não foi possível marcar first_run_done: %s", exc)


def run_first_time_tutorial() -> None:
    """Roda tutorial de 5 steps com pausas timeoutadas. Marca .first_run_done ao fim."""
    if not sys.stdin.isatty():
        mark_done()
        return

    out = sys.stdout
    out.write("\n  ── Tutorial rápido — 30 segundos ──\n\n")
    out.flush()
    try:
        for idx, (title, body) in enumerate(STEPS, 1):
            out.write(f"  [{idx}/{len(STEPS)}] {title}\n")
            out.write(f"      {body}\n")
            out.flush()
            resposta = _timed_input(
                "      pressione Enter para continuar (ou aguarde 60s)... "
            )
            if resposta is None:
                out.write("      tempo esgotado, seguindo.\n")
            out.write("\n")
            out.flush()
    except KeyboardInterrupt:
        out.write("\n  tutorial interrompido. Para rever depois, remova ~/.nyx/.first_run_done.\n")
    out.write("  Pronto. Qualquer dúvida: /help. Vamos ao trabalho.\n\n")
    out.flush()
    mark_done()
