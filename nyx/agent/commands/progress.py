"""Comando /progress -- mostra tail do progress.md da sessão corrente.

NYX-GSD-CHECKPOINTS-01: exibe ultimas N linhas do checkpoint write-through
da sessão Nyx. Default N=30, configuravel via /progress <N>.
"""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command


@nyx_command(
    name="progress",
    description="Mostra ultimas N linhas do progress.md da sessão",
    aliases=["gsd"],
    category="sessão",
    examples=["/progress", "/progress 50", "/gsd"],
)
def cmd_progress(args: str, _root: str) -> str:
    """Retorna sentinela __progress_tail__<N> para handler em cli.py."""
    arg = args.strip()
    n = 30
    if arg.isdigit():
        n = max(1, min(int(arg), 500))
    return f"__progress_tail__{n}"


# "Quem não registra o progresso, repete o passo." -- NYX-GSD-CHECKPOINTS-01
