"""Comandos de código -- explain, plan, test, compact, brief-cmd."""

from __future__ import annotations

from pathlib import Path

from nyx.agent.commands._registry import nyx_command


@nyx_command(name="explain", description="Analisa e explica um arquivo", aliases=["exp"], category="código")
def cmd_explain(file_path: str, project_root: str) -> str:
    full = Path(project_root) / file_path.strip()
    if not full.exists():
        return (
            f"__error__Arquivo '{file_path}' não existe em {project_root}."
            "||Confira o caminho com: ls -la ou tab-completion."
        )

    return (
        f"Analise e explique o arquivo '{file_path}'. "
        "Passos:\n"
        f"1. Use read_file para ler '{file_path}'\n"
        "2. Identifique: propósito, classes/funções principais, dependências, "
        "padrões de design usados\n"
        "3. Use done(summary='explicação completa em português')"
    )


@nyx_command(name="plan", description="Cria plano de implementação", category="código")
def cmd_plan(description: str, _root: str) -> str:
    return (
        f"Crie um plano de implementação para: {description}\n"
        "Passos:\n"
        "1. Use list_files para entender a estrutura do projeto\n"
        "2. Use read_file nos arquivos relevantes\n"
        "3. Use search para encontrar código relacionado\n"
        "4. Use done(summary='plano detalhado') contendo:\n"
        "   - Arquivos a criar/modificar\n"
        "   - Ordem de implementação\n"
        "   - Riscos e dependências\n"
        "NÃO execute ações de escrita. Apenas planeje."
    )


@nyx_command(name="test", description="Gera testes para um arquivo", aliases=["tst"], category="código")
def cmd_test(file_path: str, project_root: str) -> str:
    full = Path(project_root) / file_path.strip()
    if not full.exists():
        return (
            f"__error__Arquivo '{file_path}' não existe em {project_root}."
            "||Confira o caminho com: ls -la ou tab-completion."
        )

    return (
        f"Gere testes para '{file_path}'. "
        "Passos:\n"
        f"1. Use read_file para ler '{file_path}'\n"
        "2. Identifique funções/métodos testáveis\n"
        "3. Use write_file para criar arquivo de teste com:\n"
        "   - Imports necessários\n"
        "   - Testes para casos normais e edge cases\n"
        "4. Use done(summary='lista dos testes criados')"
    )


@nyx_command(name="compact", description="Resume o que foi feito na sessão", category="sessão")
def cmd_compact(history_summary: str, _root: str) -> str:
    return (
        "Resuma o trabalho realizado até agora.\n"
        f"Histórico atual:\n{history_summary}\n\n"
        "Use done(summary='resumo') contendo:\n"
        "1. O que foi feito (arquivos lidos/editados)\n"
        "2. Decisões tomadas\n"
        "3. Próximos passos sugeridos"
    )


@nyx_command(name="brief-cmd", description="Resumo rápido da sessão", category="root")
def cmd_brief_cmd(_args: str, _root: str) -> str:
    return (
        "Gere um resumo em no máximo 3 linhas do trabalho realizado.\n"
        "Foque em: o que foi feito, resultado, e próximo passo.\n"
        "Use done(summary='resumo breve')"
    )


# "Escreva código como se o próximo leitor fosse um assassino psicopata." -- Kent Beck
