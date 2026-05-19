"""Comando /sudo -- enable/disable/status do modo sudo (SUDO-MODE-01).

Slash command que controla o cache de senha sudo da sessão. Não toca
disco: senha vive apenas em memória até /sudo disable ou shutdown.

Atalhos disponíveis:
- /sudo enable  -> pede senha (getpass) e cacheia se válida
- /sudo disable -> apaga senha e marca modo inativo
- /sudo status  -> mostra ativo/inativo + se há senha cacheada

Em sessão interativa o usuário também pode entrar/sair via Shift+Tab
(SHIFT-TAB-CYCLE-01). Este comando é equivalente textual + útil para
automação em headless.
"""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command
from nyx.agent.tools import sudo_session


@nyx_command(
    name="sudo",
    description="Controla modo sudo (cache de senha apenas em memória)",
    category="sistema",
    examples=["/sudo enable", "/sudo disable", "/sudo status"],
)
def cmd_sudo(args: str, _root: str) -> str:
    """Handler do /sudo.

    Senha NUNCA é gravada em arquivo, log ou disco. Validação via
    `sudo -S -v` antes de aceitar (senha errada rejeitada).
    """
    sub = (args or "").strip().lower()

    if sub in ("", "status"):
        s = sudo_session.status()
        ativo = "ativo" if s["active"] else "inativo"
        cache = "sim" if s["has_password"] else "não"
        return (
            f"  sudo mode: {ativo}\n"
            f"  senha cacheada: {cache}\n"
            "  Use /sudo enable para ativar; /sudo disable para limpar."
        )

    if sub == "enable":
        ok, msg = sudo_session.prompt_and_cache()
        if ok:
            sudo_session.set_active(True)
            return f"  {msg}"
        # Falha não ativa modo (preserva estado seguro).
        return f"__error__{msg}||Use Shift+Tab para sair do modo sudo ou rode /sudo disable."

    if sub == "disable":
        sudo_session.wipe()
        return "  sudo desativado; cache limpo."

    return (
        f"__error__Subcomando '/sudo {sub}' não reconhecido."
        "||Use: /sudo enable, /sudo disable ou /sudo status."
    )


# "A senha é da sessão, não do disco." -- SUDO-MODE-01
