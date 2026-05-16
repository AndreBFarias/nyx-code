"""Handlers de sentinelas de observabilidade (OBSERVABILITY-01).

Extraído de cli.py para manter-lo abaixo de 800 linhas (GUIDE.md §6).

Cada função recebe o que precisa (agent ou project_root) e retorna a
string pronta para impressão. O cli.py apenas roteia a sentinela.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

from nyx.agent.services.logging_service import get_logger

if TYPE_CHECKING:
    from nyx.agent.loop._core import AgentLoop

logger = get_logger("nyx.commands.observability")


def on_model_state_log(state: str) -> None:
    """Callback que registra transições cold → warming → warm no log.

    Este stub ativa o contrato de on_model_state no AgentLoop enquanto
    o render visual não chega. UX-BUG-02B (toolbar warm/cold) substituirá
    por indicador visual no bottom_toolbar. Enquanto isso, segue como log
    estruturado para debug de boot lento.
    """
    logger.debug("model state -> %s", state)


def render_debug_session(agent: "AgentLoop") -> str:
    """Formata saída de /debug session a partir de agent.session_state()."""
    state = agent.session_state()
    lines = [
        "  sessão atual:",
        f"    iterações: {state['iter']}",
        f"    tokens acumulados: {state['tokens_total']}",
        f"    compactações: {state['compactions']}",
        f"    estado do modelo: {state['model_state']}",
        "  tools (duração média em ms):",
    ]
    td = state.get("tool_durations") or {}
    if not td:
        lines.append("    (nenhuma tool chamada nesta sessão)")
    else:
        for tool_name, durations in td.items():
            avg = sum(durations) / len(durations) if durations else 0.0
            lines.append(
                f"    {tool_name}: {avg:.1f}ms (chamadas: {len(durations)})"
            )
    return "\n".join(lines)


def render_replay(project_root: Path, session_id: str) -> str:
    """Lê sessão salva e devolve rendering read-only."""
    session_id = session_id.strip()
    if not session_id:
        return (
            "__error__Argumento obrigatório ausente em /replay."
            "||Uso: /replay <session_id>"
        )

    candidates = [
        Path.home() / ".nyx" / "sessions" / f"{session_id}.json",
        project_root / "logs" / "sessions" / f"{session_id}.json",
        Path.home() / ".nyx" / "sessions" / session_id,
    ]
    session_path = next((p for p in candidates if p.exists()), None)
    if session_path is None:
        return (
            f"__error__Sessão '{session_id}' não encontrada em ~/.nyx/sessions/ nem em {project_root}/logs/sessions/."
            "||Liste sessões disponíveis com /session list."
        )

    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        logger.error("replay falhou ao parsear %s: %s", session_path, exc)
        return (
            f"__error__Sessão {session_path.name} está corrompida (JSON inválido)."
            f"||Inspecione o arquivo ou remova com: rm {session_path}"
        )

    lines = [f"  [replay read-only de {session_path.name}]"]
    history = data.get("history", [])
    if not history:
        lines.append("    (sessão sem histórico)")
    for entry in history:
        role = entry.get("role", "?")
        content = (entry.get("content") or "")[:300]
        tool = entry.get("tool_name")
        if tool:
            lines.append(f"    [tool] {tool}({entry.get('tool_args', {})})")
        elif role == "user":
            lines.append(f"    > {content}")
        else:
            lines.append(f"    {content}")
    return "\n".join(lines)


# "Observar é o primeiro passo do conhecer." -- Aristóteles
