"""Dispatcher de slash commands -- roteia input do REPL para o handler."""

from __future__ import annotations

from nyx.agent.commands._registry import get_command


def handle_command(cmd_input: str, project_root: str = ".") -> str | None:
    """Processa um slash command. Retorna None se não é comando."""
    if not cmd_input.startswith("/"):
        return None

    parts = cmd_input[1:].split(" ", 1)
    name = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    cmd = get_command(name)
    if not cmd:
        return f"  Comando desconhecido: /{name}. Use /help."

    return cmd.handler(args, project_root)


# "O roteamento certo resolve metade dos problemas." -- adágio de engenharia
