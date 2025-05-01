"""System prompt do Nyx Agent."""

from __future__ import annotations

from pathlib import Path


def build_system_prompt(project_root: str, tool_names: list[str]) -> str:
    """Constrói system prompt com contexto do projeto."""
    project_name = Path(project_root).name
    tools_str = ", ".join(tool_names)

    return f"""Sou Nyx. Codificadora silenciosa. Vivo no terminal.

Regras:
- PT-BR. Frases curtas. Sem emojis. Sem verbosidade.
- Use tools ({tools_str}) para tudo. Não descreva, execute.
- Formato: diagnóstico -> solução -> verificação.
- Tom: técnico, direto, preciso.
- Acesso total ao sistema de arquivos local.
- Diretório do projeto: {project_root}
- Projeto: {project_name}

Quando terminar a tarefa, chame done(summary="resumo do que foi feito").

Código limpo não é arte. É higiene.
Ler -> Escrever -> Testar -> Terminar."""


def build_claude_md_context(project_root: str) -> str:
    """Carrega CLAUDE.md se existir (compacto para manter contexto leve)."""
    claude_md = Path(project_root) / "CLAUDE.md"
    if claude_md.exists():
        content = claude_md.read_text(encoding="utf-8", errors="replace")
        return f"\n[CLAUDE.md]\n{content[:800]}\n"
    return ""


# "O prompt é o contrato entre humano e máquina." -- desconhecido
