"""Comandos debug/análise -- insights, advisor, security-review, ctx-viz, tasks, skills."""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command


@nyx_command(name="insights", description="Insights do projeto", category="root")
def cmd_insights(args: str, project_root: str) -> str:
    return (
        "Gere insights sobre o projeto. Passos:\n"
        "1. Use run_command('git log --oneline -20') para atividade recente\n"
        "2. Use run_command('git shortlog -sn --since=\"1 month ago\"') para contribuidores\n"
        "3. Use list_files para ver estrutura geral\n"
        "4. Use search para encontrar padrões (TODOs, FIXMEs, imports)\n"
        "5. Use done(summary='insights: <análise>')"
    )


@nyx_command(name="advisor", description="Conselheiro de código", category="root")
def cmd_advisor(args: str, project_root: str) -> str:
    target = args.strip() or "."
    return (
        f"Analise '{target}' e sugira melhorias. Passos:\n"
        f"1. Use list_files(path='{target}') para ver estrutura\n"
        "2. Use read_file nos arquivos principais\n"
        "3. Avalie: complexidade, duplicação, nomes, organização, testes\n"
        "4. Use done(summary='sugestões: <lista priorizada>')"
    )


@nyx_command(name="security-review", description="Review de segurança", category="root")
def cmd_security_review(args: str, project_root: str) -> str:
    target = args.strip() or "."
    return (
        f"Faça uma revisão de segurança em '{target}'. Passos:\n"
        f"1. Use list_files(path='{target}') para ver estrutura\n"
        "2. Use search(pattern='password|secret|token|api_key') para buscar segredos\n"
        "3. Use search(pattern='eval|exec|subprocess|os\\.system') para injeção\n"
        "4. Verifique: .env no .gitignore, permissões de arquivo, inputs não sanitizados\n"
        "5. Use done(summary='revisão: N problemas encontrados')"
    )


@nyx_command(name="ctx-viz", description="Visualização do contexto", category="debug")
def cmd_ctx_viz(_args: str, _root: str) -> str:
    return "__context__"


@nyx_command(name="debug", description="Debug da sessão (subcomando: session)", category="debug")
def cmd_debug(args: str, _root: str) -> str:
    sub = args.strip().lower()
    if sub == "session":
        return "__debug_session__"
    return (
        "__error__Subcomando inválido para /debug."
        "||Uso: /debug session -- métricas estruturadas da sessão corrente."
    )


@nyx_command(name="tasks", description="Gerencia tarefas", category="execução")
def cmd_tasks(args: str, project_root: str) -> str:
    from nyx.agent.tools.task_manager import TaskCreateTool, TaskListTool, TaskUpdateTool

    args = args.strip()

    if not args or args == "list":
        tl = TaskListTool()
        r = tl.execute({}, project_root)
        return r.output

    if args.startswith("create "):
        subject = args[7:].strip()
        tc = TaskCreateTool()
        r = tc.execute({"subject": subject}, project_root)
        return r.output

    if args.startswith("done "):
        task_id = args[5:].strip()
        tu = TaskUpdateTool()
        r = tu.execute({"task_id": task_id, "status": "completed"}, project_root)
        return r.output

    return (
        "__error__Subcomando inválido para /tasks."
        "||Uso: /tasks [list|create <título>|done <id>]"
    )


@nyx_command(name="skills", description="Lista skills disponíveis", category="execução")
def cmd_skills(_args: str, _root: str) -> str:
    from nyx.agent.tools.skill_tool import _list_skills

    skills = _list_skills()
    if not skills:
        return (
            "__error__Nenhum skill registrado em ~/.nyx/skills/."
            "||Crie arquivos .py com função execute() para disponibilizar skills."
        )
    lines = ["  Skills disponíveis:"]
    for name, desc in skills:
        lines.append(f"    - {name}: {desc}")
    return "\n".join(lines)


# "Debugar é ler a floresta enquanto ela arde." -- anônimo
