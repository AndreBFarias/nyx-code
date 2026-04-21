"""Banner de boot do Nyx CLI (extraído de cli.py para respeitar 800 linhas).

Consome design_tokens (ADR-023) como fonte única de cores.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from nyx.__version__ import __version__ as NYX_VERSION
from nyx.themes.design_tokens import (
    ANSI_ACCENT_FG,
    ANSI_BOLD,
    ANSI_DIM,
    ANSI_RESET,
)

if TYPE_CHECKING:
    from nyx.config.settings import NyxSettings


def build_banner(
    model: str,
    tools_count: int,
    project: str,
    settings: "NyxSettings | None" = None,
) -> str:
    """Constrói banner de abertura com dados do modelo, projeto, tools e portas."""
    import shutil

    from nyx.config.settings import load_settings

    if settings is None:
        settings = load_settings()

    accent = ANSI_ACCENT_FG
    bold = ANSI_BOLD
    dim = ANSI_DIM
    nc = ANSI_RESET

    cols = shutil.get_terminal_size(fallback=(80, 24)).columns
    ollama_port = str(settings.ollama_port)
    proxy_port = str(settings.proxy_port)

    if cols < 60:
        return (
            f"\n  {accent}{bold}── Nyx v{NYX_VERSION} · {model} · "
            f"{tools_count} tools · 100% offline ──{nc}\n\n"
            f"  {dim}/help · Ctrl+D{nc}\n"
        )

    title = f"Nyx -- Code Agent Local v{NYX_VERSION}"
    tools_info = f"{tools_count} · 100% offline"
    proxy_info = f":{ollama_port} (ollama)  ·  :{proxy_port} (proxy)"
    lines = [
        "",
        f"  {accent}{bold}╭──────────────────────────────────────────────╮{nc}",
        f"  {accent}{bold}│{nc}  {bold}{title:<44s}{nc}{accent}{bold}│{nc}",
        f"  {accent}{bold}│{nc}  modelo   {model:<35s}{accent}{bold}│{nc}",
        f"  {accent}{bold}│{nc}  projeto  {project:<35s}{accent}{bold}│{nc}",
        f"  {accent}{bold}│{nc}  tools    {tools_info:<35s}{accent}{bold}│{nc}",
        f"  {accent}{bold}│{nc}  rede     {proxy_info:<35s}{accent}{bold}│{nc}",
        f"  {accent}{bold}╰──────────────────────────────────────────────╯{nc}",
        "",
        f"  {dim}/help para comandos. Ctrl+D para sair.{nc}",
        "",
    ]
    return "\n".join(lines)


# "Abertura minimalista: o que entra, justificado." -- anônimo
