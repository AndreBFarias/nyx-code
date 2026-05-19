"""Slash command /schema (TUI-REDESIGN-25-16).

Lista, mostra ou troca o schema de interface ativo em runtime.
Schema = camada de ESTRUTURA/LAYOUT (separada de aesthetic = cor e
entity = accent). Persistência via NYX_SCHEMA=<id> em .env ou shell.

Schemas validos: editorial, arcano, brutalist, hybrid (default).
"""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command


@nyx_command(
    name="schema",
    description="Lista, mostra ou troca o schema de interface (estrutura)",
    aliases=["esquema", "layout"],
    category="visual",
    examples=[
        "/schema list",
        "/schema get",
        "/schema set arcano",
    ],
)
def cmd_schema(args: str, _root: str) -> str:
    """Sentinelas processadas em cli.py para atualizar runtime."""
    arg = args.strip()
    if not arg or arg == "list":
        return "__schema_list__"
    parts = arg.split(maxsplit=1)
    sub = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""
    if sub == "get":
        return "__schema_get__"
    if sub == "select":
        # TUI-REDESIGN-27-03: abre modal radiolist com setas + Enter.
        return "__schema_select__"
    if sub == "set":
        if not rest:
            return (
                "__error__/schema set requer um nome."
                "||Use /schema list para ver opções."
            )
        return f"__schema_set__{rest}"
    return (
        f"__error__Subcomando '{sub}' desconhecido em /schema."
        "||Use /schema para ver opções."
    )
