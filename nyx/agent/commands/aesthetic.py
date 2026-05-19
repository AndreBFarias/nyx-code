"""Slash command /aesthetic (VISUAL-LAYOUT-08).

Lista, mostra ou troca o aesthetic ativo em runtime. Para persistencia
entre sessoes, exporte NYX_AESTHETIC=<id> no .env ou shell.

Aesthetics validos: default, arcano, cyberpunk, brutalist, mecha, editorial.
Entities validas: nyx, eris, juno, lars, luna, mars, somn.
"""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command


@nyx_command(
    name="aesthetic",
    description="Lista, mostra ou troca o estético visual em runtime",
    aliases=["estetica", "skin"],
    category="visual",
    examples=[
        "/aesthetic list",
        "/aesthetic get",
        "/aesthetic set arcano",
        "/aesthetic set cyberpunk:luna",
    ],
)
def cmd_aesthetic(args: str, _root: str) -> str:
    """Sentinelas processadas em cli.py para atualizar runtime.

    set aceita 'aesthetic' ou 'aesthetic:entity' (ex: arcano:luna).
    """
    arg = args.strip()
    if not arg or arg == "list":
        return "__aesthetic_list__"
    parts = arg.split(maxsplit=1)
    sub = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""
    if sub == "get":
        return "__aesthetic_get__"
    if sub == "select":
        # TUI-REDESIGN-27-03: abre modal radiolist com setas + Enter.
        return "__aesthetic_select__"
    if sub == "set":
        if not rest:
            return (
                "__error__/aesthetic set requer um nome."
                "||Use /aesthetic list para ver opções."
            )
        return f"__aesthetic_set__{rest}"
    return (
        f"__error__Subcomando '{sub}' desconhecido em /aesthetic."
        "||Use /aesthetic para ver opções."
    )
