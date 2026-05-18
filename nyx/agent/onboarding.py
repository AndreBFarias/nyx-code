"""Tutorial de primeiro uso (ONBOARDING-01).

Invocado uma vez por instalação. Idempotência via ~/.nyx/.first_run_done.
Pula automaticamente em pipe/CI (stdin não-tty) e respeita timeout de 60s
nas pausas para nunca travar.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.onboarding")

NYX_HOME = Path.home() / ".nyx"
FIRST_RUN_MARKER = NYX_HOME / ".first_run_done"
PAUSE_TIMEOUT_S = 60


def resolve_user_display_name() -> str:
    """Lê git config user.name silenciosamente; fallback 'visitante' (TUI-REDESIGN-25-04).

    Timeout 2s. Qualquer falha (git ausente, config vazio, OSError)
    retorna 'visitante'. Sem prompt interativo: a decisão é silenciosa
    e respeita usuários sem git instalado.
    """
    try:
        out = subprocess.run(
            ["git", "config", "--get", "user.name"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        name = out.stdout.strip()
        return name if name else "visitante"
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return "visitante"


def _build_steps(user_name: str) -> tuple[tuple[str, str], ...]:
    """Gera STEPS personalizado com nome resolvido (TUI-REDESIGN-25-04)."""
    return (
        (
            f"Bem-vindo, {user_name}",
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


# Mantido para compat: STEPS genérico (sem nome). Novos call-sites devem
# usar _build_steps(user_name). Removível em Onda 26 após consumers migrarem.
STEPS: tuple[tuple[str, str], ...] = _build_steps("visitante")


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


def run_first_time_tutorial(user_name: str | None = None) -> None:
    """Roda tutorial de 5 steps com pausas timeoutadas. Marca .first_run_done ao fim.

    TUI-REDESIGN-25-04: aceita user_name opcional para personalizar a
    primeira tela. Se None, resolve via resolve_user_display_name() (lê
    git config user.name silenciosamente; fallback 'visitante').
    """
    if not sys.stdin.isatty():
        mark_done()
        return

    if user_name is None:
        user_name = resolve_user_display_name()
    steps = _build_steps(user_name)

    out = sys.stdout
    out.write("\n  ── Tutorial rápido — 30 segundos ──\n\n")
    out.flush()
    try:
        for idx, (title, body) in enumerate(steps, 1):
            out.write(f"  [{idx}/{len(steps)}] {title}\n")
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
