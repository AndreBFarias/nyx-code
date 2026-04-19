"""PromptSuggestion -- Sugere próximos passos baseado no contexto."""

from __future__ import annotations

from nyx.agent.services.logging_service import get_logger
from nyx.agent.session import CodeSession

logger = get_logger("nyx.services.suggestions")

RULES: list[tuple[str, str, str]] = [
    ("read_file", "edit_file", "Editar o arquivo que acabou de ler"),
    ("edit_file", "run_command", "Testar as mudanças que acabou de fazer"),
    ("write_file", "run_command", "Executar ou testar o arquivo criado"),
    ("glob", "read_file", "Ler um dos arquivos encontrados"),
    ("search", "read_file", "Ler o arquivo com o resultado da busca"),
    ("run_command", "done", "Se o comando funcionou, finalizar a tarefa"),
]


def suggest(session: CodeSession) -> list[str]:
    """Sugere próximos passos baseado na última ação."""
    if not session.history:
        return ["Descreva o que gostaria de fazer."]

    last_tool = ""
    for entry in reversed(session.history):
        if entry.tool_name:
            last_tool = entry.tool_name
            break

    if not last_tool:
        return ["Use um comando como /explain, /plan ou /test para começar."]

    suggestions = []
    for trigger, _, description in RULES:
        if last_tool == trigger:
            suggestions.append(description)

    if not suggestions:
        suggestions = [
            "Continuar explorando o código com /explain",
            "Criar um plano com /plan",
            "Finalizar com done()",
        ]

    return suggestions[:3]


# "O próximo passo é sempre o mais importante." -- Séneca
