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
    examples: list[str] = field(default_factory=list)  # HELP-EXAMPLES-01


_COMMANDS: dict[str, CommandDef] = {}


def nyx_command(
    name: str,
    description: str,
    aliases: list[str] | None = None,
    category: str = "geral",
    examples: list[str] | None = None,
):
    """Decorador para registrar um comando.

    HELP-EXAMPLES-01: ``examples`` armazena 2-3 exemplos de uso reais,
    consumidos por ``cmd_help <nome>``.
    """

    def decorator(func: Any) -> Any:
        cmd = CommandDef(
            name=name,
            description=description,
            handler=func,
            aliases=aliases or [],
            category=category,
            examples=examples or [],
        )
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


# TUI-REDESIGN-25-13: agrupamento canônico em 3 colunas (Sessão, Contexto, Modelo).
# Comandos não-existentes são filtrados silenciosamente em format_help_3_cols.
HELP_COLUMN_GROUPS: dict[str, tuple[str, ...]] = {
    "Sessão": ("resume", "compact", "context", "clear", "quit", "stats", "cancel", "status"),
    "Contexto": ("memory", "add-dir", "init", "sandbox", "cd", "skills", "files", "paste", "recall"),
    "Modelo": ("model", "aesthetic", "schema", "output-style", "permissions", "hooks", "theme", "config", "env", "doctor"),
}


def _shorten_desc(desc: str, max_len: int) -> str:
    """Trunca descrição preservando palavras curtas (TUI-REDESIGN-25-13)."""
    if len(desc) <= max_len:
        return desc
    return desc[: max_len - 1].rstrip() + "…"


def format_help_3_cols(width: int = 96) -> str:
    """Renderiza /help em 3 colunas categorizadas (TUI-REDESIGN-25-13).

    Comandos fora dos grupos canônicos viram "outros" (4ª linha). Em
    terminais <80 cols, caller deve cair para format_help() default.
    """
    available = {c.name for c in list_commands()}
    cols = []
    for col_name, names in HELP_COLUMN_GROUPS.items():
        items = [get_command(n) for n in names if n in available]
        cols.append((col_name, [c for c in items if c is not None]))

    col_w = max(20, width // 3)
    lines: list[str] = ["", "  " + "".join(f"{name:<{col_w}}" for name, _ in cols)]
    max_rows = max(len(items) for _, items in cols)
    for i in range(max_rows):
        parts: list[str] = []
        for _, items in cols:
            if i < len(items):
                cmd = items[i]
                line = f"/{cmd.name} — {_shorten_desc(cmd.description, col_w - len(cmd.name) - 4)}"
                parts.append(f"{line:<{col_w}}")
            else:
                parts.append(" " * col_w)
        lines.append("  " + "".join(parts).rstrip())
    # Outros (commands fora dos grupos).
    grouped = {name for names in HELP_COLUMN_GROUPS.values() for name in names}
    extras = sorted(c for c in available if c not in grouped)
    if extras:
        lines.append("")
        lines.append(f"  Outros: {', '.join('/' + n for n in extras)}")
    lines.append("")
    lines.append(f"  ({len(available)} comandos no total. /help <nome> mostra exemplos; /help all lista todos.)")
    lines.append("")
    return "\n".join(lines)


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
        # TUI-REDESIGN-25-13: layout 3 colunas em terminais >= 80 cols.
        import shutil
        cols_width = shutil.get_terminal_size(fallback=(80, 24)).columns
        if cols_width >= 80:
            return format_help_3_cols(width=min(cols_width - 2, 102))
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
