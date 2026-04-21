"""Dispatcher de slash commands -- roteia input do REPL para o handler.

ERROR-MSG-01: comando desconhecido devolve string sentinela
``__error__<linha pronta>`` para o cli.py imprimir via print_error,
com sugestão de comando próximo via difflib.get_close_matches
(cutoff 0.6, n=1). Argumentos válidos passam sem alteração.
"""

from __future__ import annotations

from difflib import get_close_matches

from nyx.agent.commands._registry import _COMMANDS, get_command

ERROR_SENTINEL = "__error__"


def _format_unknown_command(name: str) -> str:
    """Monta a mensagem sentinela para comando desconhecido.

    Formato: ``__error__<msg>||<hint>`` -- o dispatcher no cli.py
    decompõe em ``msg`` e ``hint`` para passar ao print_error.
    Se houver sugestão próxima (score >= 0.6), o hint vira
    ``Você quis dizer /<sug>?``, caso contrário ``Use /help para
    listar comandos disponíveis.``
    """
    names = sorted({cmd.name for cmd in _COMMANDS.values()})
    sugestoes = get_close_matches(name, names, n=1, cutoff=0.6)
    if sugestoes:
        hint = f"Você quis dizer /{sugestoes[0]}?"
    else:
        hint = "Use /help para listar comandos disponíveis."
    return f"{ERROR_SENTINEL}Comando desconhecido: /{name}.||{hint}"


def handle_command(cmd_input: str, project_root: str = ".") -> str | None:
    """Processa um slash command. Retorna None se não é comando."""
    if not cmd_input.startswith("/"):
        return None

    parts = cmd_input[1:].split(" ", 1)
    name = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    cmd = get_command(name)
    if not cmd:
        return _format_unknown_command(name)

    return cmd.handler(args, project_root)


# "O roteamento certo resolve metade dos problemas." -- adágio de engenharia
