"""Constantes internas do loop do agent."""

from __future__ import annotations

from nyx.agent.models import ActionType

LLM_TIMEOUT = 600

ACTION_TO_TOOL: dict[ActionType, str] = {
    ActionType.READ_FILE: "read_file",
    ActionType.CREATE_FILE: "write_file",
    ActionType.WRITE_FILE: "write_file",
    ActionType.EDIT_FILE: "edit_file",
    ActionType.RUN_COMMAND: "run_command",
    ActionType.GLOB: "glob",
    ActionType.SEARCH: "search",
    ActionType.LIST_FILES: "list_files",
    ActionType.ANALYZE: "analyze",
    ActionType.PATCH: "patch",
    ActionType.REPL: "repl",
    ActionType.TODO_WRITE: "todo_write",
    ActionType.WEB_FETCH: "web_fetch",
    ActionType.WEB_SEARCH: "web_search",
    ActionType.WRITE_MEMORY: "write_memory",
    ActionType.DONE: "done",
}

PARAM_REMAP: dict[str, dict[str, str]] = {
    "read_file": {"path": "file_path"},
    "write_file": {"path": "file_path"},
    "edit_file": {"path": "file_path"},
    "run_command": {"cmd": "command"},
    "search": {"pattern": "pattern"},
    "glob": {"pattern": "pattern"},
    "list_files": {"path": "path"},
}


def _remap_params(tool_name: str, params: dict[str, str]) -> dict[str, str]:
    """Remapeia nomes de parâmetros do parser para os esperados pela tool."""
    mapping = PARAM_REMAP.get(tool_name, {})
    result: dict[str, str] = {}
    for k, v in params.items():
        new_key = mapping.get(k, k)
        result[new_key] = v
    return result


# Tools core: sempre enviadas (essenciais para qualquer tarefa)
CORE_TOOLS = {
    "read_file",
    "write_file",
    "edit_file",
    "run_command",
    "search",
    "glob",
    "list_files",
    "done",
}

# Keywords que ativam tools condicionais
TOOL_KEYWORDS: dict[str, set[str]] = {
    # MEMORY-INTENT-CLASSIFY-01: sem write_memory aqui, intent=tool-needed de
    # memória ("lembra que X") não disponibiliza a tool ao modelo e a memória
    # nunca grava (achado do estresse ONDA-44).
    "write_memory": {"lembra", "lembre", "anota", "anote", "guarda", "guarde",
                     "memoriza", "memorize", "registra", "registre",
                     "memória", "memoria", "não esquece", "nao esquece"},  # noqa-acento
    "notebook_edit": {"notebook", "ipynb", "jupyter"},
    "web_fetch": {"url", "http", "fetch", "download", "site", "web"},
    "web_search": {"pesquis", "web", "google", "search"},
    "todo_write": {"todo", "tarefa", "task", "lista"},
    "agent": {"agent", "subagent", "delegar"},
    "enter_plan_mode": {"plano", "plan", "planej"},
    "exit_plan_mode": {"plano", "plan"},
    "ask_user": {"perguntar", "confirmar", "ask"},
    "analyze": {"analis", "analyz", "complex"},
    "patch": {"patch", "diff", "aplicar"},
    "multi_edit": {"multi", "vários arquivos", "batch"},
    "enter_worktree": {"worktree", "isolar"},
    "exit_worktree": {"worktree"},
    "repl": {"repl", "executar python", "python -c"},
    "tool_search": {"tool_search", "buscar tool"},
    "skill": {"skill", "habilidade"},
    "send_message": {"mensagem", "message"},
    "brief": {"resumo", "brief"},
    "config": {"config", "configurar"},
    "sleep": {"esperar", "aguardar", "sleep"},
    "task_create": {"tarefa", "task"},
    "task_update": {"tarefa", "task"},
    "task_list": {"tarefa", "task"},
    "task_get": {"tarefa", "task"},
    "task_output": {"tarefa", "task"},
    "task_stop": {"tarefa", "task"},
}


# "Constantes são o contrato silencioso do programa." -- anônimo
