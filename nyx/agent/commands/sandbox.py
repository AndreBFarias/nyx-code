"""Slash commands /sandbox e /cd -- PROJECT-ROOTS-MULTI-01.

Permite ao usuário gerenciar a lista de roots permitidos em runtime
(opt-in explícito) e trocar o project_root corrente da sessão.

Sentinelas devolvidos ao cli.py:
  __sandbox_list__               -> imprimir lista atual
  __sandbox_add__<path>          -> adicionar root e confirmar
  __sandbox_remove__<path>       -> remover root e confirmar
  __cd__<path>                   -> trocar project_root + reconfigurar agent
"""

from __future__ import annotations

from pathlib import Path

from nyx.agent.commands._registry import nyx_command


@nyx_command(
    name="sandbox",
    description="Lista, adiciona ou remove roots permitidos no sandbox",
    aliases=["roots"],
    category="projeto",
    examples=[
        "/sandbox list",
        "/sandbox add ~/Desenvolvimento/Outro-Projeto",
        "/sandbox remove /tmp",
    ],
)
def cmd_sandbox(args: str, _root: str) -> str:
    """Gerencia roots autorizados em runtime."""
    parts = args.strip().split(maxsplit=1)
    sub = (parts[0].lower() if parts else "list")
    target = parts[1].strip() if len(parts) > 1 else ""

    if sub in ("", "list", "ls"):
        return "__sandbox_list__"

    if sub == "add":
        if not target:
            return (
                "__error__/sandbox add exige um caminho."
                "||Exemplo: /sandbox add ~/Desenvolvimento/Outro-Projeto"
            )
        resolved = str(Path(target).expanduser())
        return f"__sandbox_add__{resolved}"

    if sub in ("remove", "rm", "del"):
        if not target:
            return (
                "__error__/sandbox remove exige um caminho."
                "||Liste com /sandbox list para ver os roots ativos."
            )
        resolved = str(Path(target).expanduser())
        return f"__sandbox_remove__{resolved}"

    return (
        f"__error__Subcomando '/sandbox {sub}' desconhecido."
        "||Use: /sandbox list | /sandbox add <path> | /sandbox remove <path>"
    )


@nyx_command(
    name="cd",
    description="Troca o project_root corrente; o root antigo vira extra autorizado",
    category="projeto",
    examples=[
        "/cd ~/Desenvolvimento/Outro-Projeto",
        "/cd /home/andrefarias/Desenvolvimento/Protocolo-Mob-Ouroboros",
    ],
)
def cmd_cd(args: str, _root: str) -> str:
    target = args.strip()
    if not target:
        return (
            "__error__/cd exige um caminho de destino."
            "||Exemplo: /cd ~/Desenvolvimento/Outro-Projeto"
        )
    resolved = str(Path(target).expanduser())
    return f"__cd__{resolved}"


# "Sandbox com chave não é gaiola; é casa com porta." -- PROJECT-ROOTS-MULTI-01
