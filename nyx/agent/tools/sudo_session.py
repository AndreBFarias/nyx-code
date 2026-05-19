"""SudoSession -- Cache de senha sudo na sessão (SUDO-MODE-01).

Singleton module-level que guarda a senha sudo APENAS em memória da
sessão do REPL. NUNCA persiste em disco, log ou arquivo.

Contratos de segurança (acceptance_criteria do spec):
- Senha lida via getpass (input mascarado).
- Validada com `sudo -S -v` antes de cachear (rejeita inválida).
- Armazenada em variável de módulo (`_password`), nunca em app_state
  nem em disco.
- Limpa em `wipe()` ao sair do modo sudo, no /sudo disable e no
  shutdown do REPL.
- run_command em modo sudo prefixa `sudo -S -p ''` lendo a senha de
  stdin (não ecoa no terminal).

Fallback opcional via env `NYX_SUDO_PASSWORD` apenas em headless/CI
(quando stdin não é tty). NUNCA é o caminho preferido; em REPL
interativo o getpass sempre é tentado primeiro.

Blacklist de comandos destrutivos preservada mesmo em modo sudo:
`rm -rf /`, `rm -rf ~`, `dd of=/dev/`, `mkfs`.
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Callable

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.tools.sudo_session")


# Estado interno do módulo. NUNCA exportado diretamente; o acesso é
# via get_password() (read-only) e wipe() (apaga). is_active() reflete
# o booleano _active controlado pelo handler de cycle de modo.
_password: str | None = None
_active: bool = False

# Lista negra de patterns destrutivos absolutos. Mesmo com sudo elevado
# o agente NÃO deve poder executar essas instruções; bloqueio explícito.
DANGER_PATTERNS: tuple[str, ...] = (
    "rm -rf /",
    "rm -rf /*",
    "rm -rf ~",
    "rm -rf ${HOME}",
    "dd of=/dev/",
    "mkfs",
    ":(){ :|:& };:",
    "> /dev/sda",
)


def is_active() -> bool:
    """True se modo sudo está ativo (cycle Shift+Tab posicionado em sudo)."""
    return _active


def has_password() -> bool:
    """True se há senha cacheada (em memória da sessão)."""
    return _password is not None


def get_password() -> str | None:
    """Retorna a senha cacheada (interna; apenas run_command usa)."""
    return _password


def is_destructive(command: str) -> str | None:
    """Retorna o pattern destrutivo encontrado ou None.

    Bloqueio aplicado em qualquer modo, mas a checagem é centralizada
    aqui para que run_command em sudo mode possa rejeitar antes de
    invocar `sudo -S` (senão a sandbox passaria por cima do preflight).
    """
    if not command:
        return None
    cmd = command.strip()
    for pattern in DANGER_PATTERNS:
        if pattern in cmd:
            return pattern
    return None


def _validate_password(pwd: str) -> bool:
    """Valida senha rodando `sudo -S -v` (não executa comando real).

    -S lê senha do stdin sem ecoar. -v faz refresh do timestamp do sudo
    sem rodar comando externo. Se a senha estiver errada retorna != 0.
    Logs registram apenas o exit code; NUNCA a senha.
    """
    try:
        result = subprocess.run(
            ["sudo", "-S", "-v"],
            input=(pwd + "\n").encode("utf-8"),
            capture_output=True,
            timeout=10,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        logger.warning("sudo validate falhou: %s", type(exc).__name__)
        return False
    ok = result.returncode == 0
    logger.info("sudo validate: exit=%s", result.returncode)
    return ok


def prompt_and_cache(
    *,
    getpass_fn: Callable[[str], str] | None = None,
    env_fallback: bool = True,
) -> tuple[bool, str]:
    """Pede senha via getpass e cacheia em memória se válida.

    Retorna ``(ok, mensagem)``:
    - ok=True: senha cacheada com sucesso (ou já estava cacheada).
    - ok=False: usuário cancelou (Ctrl+C/D), senha inválida, ou sudo
      indisponível. ``mensagem`` é texto PT-BR pronto para exibir.

    ``getpass_fn`` é injetável para testes (default = ``getpass.getpass``).
    ``env_fallback`` consulta NYX_SUDO_PASSWORD apenas quando stdin não
    é tty (headless/cockpit/CI). Em REPL interativo o env é ignorado
    deliberadamente -- usuário deve digitar.
    """
    global _password

    if _password is not None:
        return True, "sudo já cacheado nesta sessão"

    # Headless / cockpit / CI: stdin não é tty. Aceita env fallback.
    if env_fallback and not sys.stdin.isatty():
        env_pwd = os.environ.get("NYX_SUDO_PASSWORD")
        if env_pwd:
            if _validate_password(env_pwd):
                _password = env_pwd
                logger.info("sudo cacheado via NYX_SUDO_PASSWORD (headless)")
                return True, "sudo cacheado (env headless)"
            logger.warning("NYX_SUDO_PASSWORD inválida (headless)")
            return False, "NYX_SUDO_PASSWORD inválida"

    # REPL interativo: getpass mascarado.
    if getpass_fn is None:
        import getpass as _gp

        getpass_fn = _gp.getpass

    try:
        pwd = getpass_fn("  [sudo] senha: ")
    except (KeyboardInterrupt, EOFError):
        return False, "sudo cancelado pelo usuário"

    pwd = (pwd or "").strip()
    if not pwd:
        return False, "senha vazia; sudo não ativado"

    if not _validate_password(pwd):
        # Best-effort: zera buffer local antes de descartar.
        pwd = "0" * len(pwd)
        del pwd
        return False, "senha inválida; sudo não ativado"

    _password = pwd
    logger.info("sudo cacheado via getpass (sessão interativa)")
    return True, "sudo cacheado"


def set_active(active: bool) -> None:
    """Marca modo sudo ativo/inativo. Não toca o cache de senha.

    O wipe explícito da senha acontece em wipe() (chamado pelo cycle
    handler ao sair de sudo e pelo shutdown do REPL).
    """
    global _active
    _active = bool(active)
    logger.info("sudo mode: %s", "ATIVO" if _active else "DESATIVADO")


def wipe() -> None:
    """Apaga senha cacheada e marca modo inativo.

    Best-effort: sobrescreve o buffer com zeros antes de remover a
    referência. Python strings são imutáveis, então o "zero-out" não
    afeta o objeto original na memória, mas garante que a próxima
    leitura de ``_password`` não retorne mais a senha real.
    """
    global _password, _active
    if _password is not None:
        try:
            _ = "0" * len(_password)  # noqa: F841 -- best-effort overwrite
        except Exception as _exc:  # noqa: BLE001 -- wipe é defensivo
            logger.debug("wipe overwrite best-effort falhou: %s", _exc)
    _password = None
    _active = False
    logger.info("sudo cache limpo (wipe)")


def status() -> dict[str, bool]:
    """Snapshot do estado (para /sudo status, sem expor a senha)."""
    return {
        "active": _active,
        "has_password": _password is not None,
    }


# "Sudo na sessão, não no disco." -- SUDO-MODE-01
