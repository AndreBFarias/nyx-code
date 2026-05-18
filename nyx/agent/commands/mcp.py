"""Slash commands de MCP (MCP-SERVER-01): /mcp list, /mcp reload, /mcp test."""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command


@nyx_command(
    name="mcp",
    description="Lista, recarrega ou testa servers MCP (/mcp list|reload|test <name>)",
    category="contexto",
    examples=["/mcp list", "/mcp reload", "/mcp test filesystem"],
)
def cmd_mcp(args: str, _root: str) -> str:
    """Sentinelas processadas em cli.py (precisa do asyncio loop ativo)."""
    arg = args.strip()
    if not arg:
        return (
            "  Uso: /mcp <subcomando>\n"
            "    list             -- lista servers configurados\n"
            "    reload           -- re-conecta todos servers\n"
            "    test <name>      -- ping em um server"
        )
    parts = arg.split(maxsplit=1)
    sub = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""
    if sub == "list":
        return "__mcp_list__"
    if sub == "reload":
        return "__mcp_reload__"
    if sub == "test":
        if not rest:
            return (
                "__error__/mcp test requer nome do server."
                "||Use /mcp list para ver nomes disponíveis."
            )
        return f"__mcp_test__{rest.strip()}"
    return (
        f"__error__Subcomando '{sub}' desconhecido em /mcp."
        "||Use /mcp para ver opções."
    )
