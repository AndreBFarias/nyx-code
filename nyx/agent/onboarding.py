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
CONFIG_PATH = NYX_HOME / "config.toml"
PAUSE_TIMEOUT_S = 60


def _read_persisted_user_name() -> str | None:
    """Lê user_display_name de ~/.nyx/config.toml (TUI-REDESIGN-26-05).

    Retorna None se o arquivo não existir, chave ausente, ou parse falhar.
    Usa tomllib (Python 3.11+).
    """
    if not CONFIG_PATH.is_file():
        return None
    try:
        import tomllib
        with CONFIG_PATH.open("rb") as f:
            data = tomllib.load(f)
        val = data.get("user_display_name")
        if isinstance(val, str) and val.strip():
            return val.strip()
    except Exception as exc:  # noqa: BLE001 -- parse silencioso
        logger.debug("config.toml parse falhou: %s", exc)
    return None


def read_persisted_config() -> dict:
    """Lê ~/.nyx/config.toml e retorna o dict completo (ONBOARDING-REPLAY-FLAG-01).

    Retorna {} se o arquivo não existir ou o parse falhar. Usado pelo modo
    replay (--onboarding) para ecoar o estado persistido ao fim do wizard.
    """
    if not CONFIG_PATH.is_file():
        return {}
    try:
        import tomllib
        with CONFIG_PATH.open("rb") as f:
            return tomllib.load(f)
    except Exception as exc:  # noqa: BLE001 -- parse silencioso
        logger.debug("config.toml parse falhou (read_persisted_config): %s", exc)
        return {}


def _persist_user_name(name: str) -> None:
    """Persiste user_display_name em ~/.nyx/config.toml (TUI-REDESIGN-26-05).

    Preserva outras chaves existentes (merge não-destrutivo). Escrita
    manual em TOML simples (chave = "valor"); stdlib não tem tomli-w.
    """
    try:
        NYX_HOME.mkdir(parents=True, exist_ok=True)
        existing: dict = {}
        if CONFIG_PATH.is_file():
            try:
                import tomllib
                with CONFIG_PATH.open("rb") as f:
                    existing = tomllib.load(f)
            except Exception as exc:  # noqa: BLE001
                logger.debug("config.toml read p/ merge falhou: %s", exc)
                existing = {}
        existing["user_display_name"] = name
        lines = ["# ~/.nyx/config.toml (gerado por nyx)", ""]
        for k, v in existing.items():
            if isinstance(v, bool):
                v_s = "true" if v else "false"
            elif isinstance(v, (int, float)):
                v_s = str(v)
            else:
                v_s = f'"{v}"'
            lines.append(f"{k} = {v_s}")
        CONFIG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except OSError as exc:
        logger.warning("não foi possível persistir user_display_name: %s", exc)


def _git_user_name() -> str:
    """Helper isolado: git config user.name (timeout 2s, fallback ''')."""
    try:
        out = subprocess.run(
            ["git", "config", "--get", "user.name"],
            capture_output=True, text=True, timeout=2, check=False,
        )
        return out.stdout.strip()
    except (FileNotFoundError, OSError, subprocess.TimeoutExpired):
        return ""


def resolve_user_display_name() -> str:
    """Resolve nome do usuário com prioridade: config.toml -> git config -> 'visitante'.

    TUI-REDESIGN-25-04 (inicial): git config; TUI-REDESIGN-26-05: config.toml
    vira fonte primária para permitir que o usuário customize via onboarding.
    """
    persisted = _read_persisted_user_name()
    if persisted:
        return persisted
    git_name = _git_user_name()
    return git_name if git_name else "visitante"


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


def run_first_run_wizard(force: bool = False) -> None:
    """First-run completo (TUI-REDESIGN-28-05): nome + 6 passos do menu_wizard.

    Sequência integrada de 7 passos:

      01/07  Como devo te chamar? (default: nome persistido -> git config user.name -> 'visitante')
      02/07  Aesthetic visual    (menu_wizard.main)
      03/07  Entidade            (menu_wizard.main)
      04/07  Schema de interface (menu_wizard.main)
      05/07  Banner mode         (menu_wizard.main)
      06/07  Modelo Ollama       (menu_wizard.main)
      07/07  Auto-aprovar?       (menu_wizard.main)

    Pula em ambiente não-tty (CI/pipe) e em segunda execução
    (``.first_run_done`` bloqueia via ``should_run_tutorial``).

    ``force=True`` (modo replay via ``run.sh --onboarding``) re-pergunta o nome
    mesmo com nome já persistido (ONBOARDING-REPLAY-FLAG-01).

    Persiste tudo em ``~/.nyx/config.toml`` (merge não-destrutivo) e marca
    ``.first_run_done`` ao final, idempotente.
    """
    if not sys.stdin.isatty():
        mark_done()
        return

    # Passo 01/07 -- nome do usuário (force=True re-pergunta mesmo com nome persistido)
    persisted = _read_persisted_user_name()
    if persisted and not force:
        user_name = persisted
    else:
        git_hint = _git_user_name()
        default = persisted or git_hint or "visitante"
        sys.stdout.write("\n")
        sys.stdout.write("  ── Configuração inicial — Nyx-Code ──\n\n")
        sys.stdout.write(f"  01/07 · Como devo te chamar? [Enter = '{default}']: ")
        sys.stdout.flush()
        response = _timed_input("")
        user_name = (response or "").strip() or default
        _persist_user_name(user_name)

    # Passos 02-07/07 -- menu_wizard.main()
    # Importação local: dependência menu_wizard só vive aqui (forbidden global).
    import os as _os

    PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    scripts_dir = str(PROJECT_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)

    prev_emit = _os.environ.get("NYX_MENU_EMIT")
    prev_first_run = _os.environ.get("NYX_MENU_FIRST_RUN")
    _os.environ["NYX_MENU_EMIT"] = "0"
    _os.environ["NYX_MENU_FIRST_RUN"] = "1"
    try:
        from scripts.menu_wizard import main as _wizard_main
        try:
            _wizard_main(existing_name=user_name)
        except (KeyboardInterrupt, EOFError):
            sys.stdout.write("\n  wizard cancelado; ajustes manuais via /config setup.\n")
            sys.stdout.flush()
    except Exception as exc:  # noqa: BLE001 -- wizard é best-effort
        logger.warning("menu_wizard falhou (%s); first-run segue só com nome.", exc)
    finally:
        if prev_emit is None:
            _os.environ.pop("NYX_MENU_EMIT", None)
        else:
            _os.environ["NYX_MENU_EMIT"] = prev_emit
        if prev_first_run is None:
            _os.environ.pop("NYX_MENU_FIRST_RUN", None)
        else:
            _os.environ["NYX_MENU_FIRST_RUN"] = prev_first_run

    mark_done()


def run_first_time_tutorial(user_name: str | None = None) -> None:
    """Roda tutorial de 5 steps com pausas timeoutadas. Marca .first_run_done ao fim.

    TUI-REDESIGN-25-04: aceita user_name opcional para personalizar a
    primeira tela. Se None, resolve via resolve_user_display_name().

    TUI-REDESIGN-26-05: se config.toml ainda não tem user_display_name,
    pergunta interativamente (git config como hint default) e persiste.
    """
    if not sys.stdin.isatty():
        mark_done()
        return

    if user_name is None:
        persisted = _read_persisted_user_name()
        if persisted:
            user_name = persisted
        else:
            git_hint = _git_user_name()
            default = git_hint or "visitante"
            sys.stdout.write("\n")
            sys.stdout.flush()
            response = _timed_input(
                f"  Como devo te chamar? [Enter = '{default}']: "
            )
            user_name = (response or "").strip() or default
            _persist_user_name(user_name)
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
