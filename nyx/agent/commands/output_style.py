"""Slash commands de output-style (OUTPUT-STYLES-01)."""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command


@nyx_command(
    name="output-style",
    description="Lista, mostra ou troca o estilo de saída (default/concise/learning)",
    aliases=["style"],
    category="sistema",
    examples=["/output-style list", "/output-style get", "/output-style set concise"],
)
def cmd_output_style(args: str, _root: str) -> str:
    """Sentinelas processadas em cli.py para atualizar settings em runtime."""
    arg = args.strip()
    if not arg or arg == "list":
        return "__output_style_list__"
    parts = arg.split(maxsplit=1)
    sub = parts[0].lower()
    rest = parts[1].strip() if len(parts) > 1 else ""
    if sub == "get":
        return "__output_style_get__"
    if sub == "set":
        if not rest:
            return (
                "__error__/output-style set requer um nome."
                "||Use /output-style list para ver opções."
            )
        return f"__output_style_set__{rest}"
    return (
        f"__error__Subcomando '{sub}' desconhecido em /output-style."
        "||Use /output-style para ver opções."
    )
