"""Slash commands de plugins (PLUGINS-01)."""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command


@nyx_command(
    name="plugin",
    description="Gerencia plugins instalados em ~/.nyx/plugins (/plugin list|reload|install|uninstall)",
    category="sistema",
    examples=["/plugin list", "/plugin reload", "/plugin install /tmp/meu-plugin"],
)
def cmd_plugin(args: str, _root: str) -> str:
    """Sentinelas processadas em cli.py."""
    arg = args.strip()
    if not arg:
        return (
            "  Uso: /plugin <subcomando>\n"
            "    list                   -- lista plugins instalados\n"
            "    reload                 -- re-descobre e re-carrega\n"
            "    install <path>         -- copia <path> para ~/.nyx/plugins/\n"
            "    uninstall <name>       -- remove plugin pelo nome"
        )
    parts = arg.split(maxsplit=1)
    sub = parts[0].lower()
    rest = parts[1] if len(parts) > 1 else ""
    if sub == "list":
        return "__plugin_list__"
    if sub == "reload":
        return "__plugin_reload__"
    if sub == "install":
        if not rest:
            return (
                "__error__/plugin install requer um caminho."
                "||Use: /plugin install /caminho/para/plugin"
            )
        return f"__plugin_install__{rest.strip()}"
    if sub == "uninstall":
        if not rest:
            return (
                "__error__/plugin uninstall requer o nome do plugin."
                "||Use /plugin list para ver os instalados."
            )
        return f"__plugin_uninstall__{rest.strip()}"
    return (
        f"__error__Subcomando '{sub}' desconhecido em /plugin."
        "||Use /plugin para ver opções."
    )
