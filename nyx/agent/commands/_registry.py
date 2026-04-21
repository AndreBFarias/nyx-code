"""Registry de slash commands -- infraestrutura.

Contém:
  - CommandDef: dataclass do comando
  - _COMMANDS: dict global
  - nyx_command: decorador de registro
  - get_command, list_commands: lookup
  - format_help: renderização do /help
  - ESSENTIAL_COMMANDS: subset exibido em /help sem args
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class CommandDef:
    name: str
    description: str
    handler: Any
    aliases: list[str] = field(default_factory=list)
    category: str = "geral"


_COMMANDS: dict[str, CommandDef] = {}


def nyx_command(name: str, description: str, aliases: list[str] | None = None, category: str = "geral"):
    """Decorador para registrar um comando."""

    def decorator(func: Any) -> Any:
        cmd = CommandDef(name=name, description=description, handler=func, aliases=aliases or [], category=category)
        _COMMANDS[name] = cmd
        for alias in cmd.aliases:
            _COMMANDS[alias] = cmd
        return func

    return decorator


def get_command(name: str) -> CommandDef | None:
    return _COMMANDS.get(name.lower())


def list_commands() -> list[CommandDef]:
    seen: set[str] = set()
    result: list[CommandDef] = []
    for cmd in _COMMANDS.values():
        if cmd.name not in seen:
            seen.add(cmd.name)
            result.append(cmd)
    return sorted(result, key=lambda c: c.name)


ESSENTIAL_COMMANDS = (
    "help",
    "status",
    "tools",
    "plan",
    "explain",
    "commit",
    "memory",
    "paste",
    "clear",
    "quit",
)


def format_help(show_all: bool = False, filter_query: str | None = None) -> str:
    commands = list_commands()
    if not commands:
        return "Nenhum comando registrado."

    if filter_query:
        fq = filter_query.strip().rstrip("*").lower()
        matched = [
            c for c in commands
            if c.name.startswith(fq) or c.category.lower() == fq
        ]
        if not matched:
            return f"Nenhum comando bate com '{filter_query}'."
        lines = ["", f"  Comandos para '{filter_query}':", ""]
        for cmd in matched:
            aliases = (
                f" ({', '.join('/' + a for a in cmd.aliases)})"
                if cmd.aliases else ""
            )
            lines.append(
                f"    /{cmd.name:<12s}{aliases:16s} -- {cmd.description}"
            )
        lines.append("")
        return "\n".join(lines)

    if not show_all:
        essentials = [c for c in commands if c.name in ESSENTIAL_COMMANDS]
        lines = ["", "  Comandos principais:", ""]
        for cmd in sorted(essentials, key=lambda c: ESSENTIAL_COMMANDS.index(c.name)):
            aliases = f" ({', '.join('/' + a for a in cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"    /{cmd.name:<10s}{aliases:14s} -- {cmd.description}")
        lines.append("")
        lines.append(f"  ({len(commands)} comandos no total. Use /help all pra ver todos.)")
        lines.append("")
        return "\n".join(lines)

    lines = ["", "  Todos os comandos:", ""]
    by_cat: dict[str, list[CommandDef]] = {}
    for cmd in commands:
        by_cat.setdefault(cmd.category, []).append(cmd)

    for cat, cmds in sorted(by_cat.items()):
        lines.append(f"  [{cat}]")
        for cmd in sorted(cmds, key=lambda c: c.name):
            aliases = f" ({', '.join('/' + a for a in cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"    /{cmd.name:<12s}{aliases:16s} -- {cmd.description}")
        lines.append("")
    return "\n".join(lines)


# "Estruturas simples sustentam sistemas complexos." -- Edsger Dijkstra
