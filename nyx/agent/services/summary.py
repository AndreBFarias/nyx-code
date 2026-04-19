"""AgentSummary -- Gera resumos de ações do agent."""

from __future__ import annotations

from nyx.agent.services.logging_service import get_logger
from nyx.agent.session import CodeSession

logger = get_logger("nyx.services.summary")


def summarize(session: CodeSession) -> str:
    """Gera resumo em PT-BR do trabalho realizado."""
    if not session.history:
        return "Nenhuma ação registrada."

    actions = summarize_by_type(session)
    key = get_key_actions(session)

    lines = ["Resumo da sessão:"]

    if key:
        lines.append(f"\nDecisões-chave ({len(key)}):")
        for k in key[:10]:
            lines.append(f"  - {k}")

    for atype, entries in sorted(actions.items()):
        lines.append(f"\n{atype} ({len(entries)}):")
        for e in entries[:5]:
            lines.append(f"  - {e}")

    lines.append(f"\nTotal: {len(session.history)} entradas")
    lines.append(f"Arquivos lidos: {session.files_read_count}")
    lines.append(f"Arquivos modificados: {session.files_modified_count}")

    return "\n".join(lines)


def summarize_by_type(session: CodeSession) -> dict[str, list[str]]:
    """Agrupa ações por tipo."""
    groups: dict[str, list[str]] = {}
    for entry in session.history:
        if entry.tool_name:
            category = _categorize(entry.tool_name)
            desc = f"{entry.tool_name}({str(entry.tool_args)[:60]})"
            groups.setdefault(category, []).append(desc)
        elif entry.role == "user":
            groups.setdefault("input", []).append(entry.content[:80])
        elif entry.role == "assistant":
            groups.setdefault("resposta", []).append(entry.content[:80])
    return groups


def get_key_actions(session: CodeSession) -> list[str]:
    """Extrai ações-chave (decisões de escrita)."""
    key_tools = {"write_file", "edit_file", "run_command", "create_file"}
    return [f"{e.tool_name}: {str(e.tool_args)[:80]}" for e in session.history if e.tool_name in key_tools]


def _categorize(tool_name: str) -> str:
    """Categoriza tool por tipo."""
    read_tools = {"read_file", "glob", "search", "list_files", "tool_search", "brief"}
    write_tools = {"write_file", "edit_file", "create_file", "notebook_edit"}
    exec_tools = {"run_command", "repl"}
    web_tools = {"web_fetch", "web_search"}
    task_tools = {"task_create", "task_update", "task_list", "task_get", "task_stop", "todo_write"}

    if tool_name in read_tools:
        return "leitura"
    if tool_name in write_tools:
        return "escrita"
    if tool_name in exec_tools:
        return "execução"
    if tool_name in web_tools:
        return "web"
    if tool_name in task_tools:
        return "tarefas"
    return "outro"


# "Resumir é a arte de dizer o essencial." -- Voltaire
