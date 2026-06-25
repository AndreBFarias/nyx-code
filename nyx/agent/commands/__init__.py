"""Pacote de slash commands do Nyx.

API pública (re-exportada):
  - CommandDef
  - nyx_command (decorador)
  - get_command, list_commands, format_help
  - handle_command (dispatcher)

O import dos submódulos abaixo é necessário para que os decoradores
@nyx_command executem e populem _COMMANDS no registry (side-effect).
"""

from nyx.agent.commands import (  # noqa: F401  -- side-effect: registra @nyx_command
    aesthetic,
    code,
    core,
    debug_cmds,
    git_cmds,
    mcp,
    output_style,
    plan,
    plugin,
    progress,
    sandbox,
    schema,
    session,
    stats,
    sudo_mode,
    system,
)
from nyx.agent.commands._dispatcher import (
    SLASH_CHAT,
    SLASH_COMMAND,
    SLASH_UNKNOWN,
    classify_slash_input,
    handle_command,
)
from nyx.agent.commands._registry import (
    CommandDef,
    format_help,
    get_command,
    list_commands,
    nyx_command,
)

__all__ = [
    "CommandDef",
    "nyx_command",
    "get_command",
    "list_commands",
    "format_help",
    "handle_command",
    "classify_slash_input",
    "SLASH_COMMAND",
    "SLASH_CHAT",
    "SLASH_UNKNOWN",
]


# "Um pacote bem dividido é uma casa com cômodos." -- Aristóteles (paráfrase)
