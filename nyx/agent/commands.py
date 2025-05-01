"""Commands -- Slash commands para o Nyx CLI.

Port de Luna src/skills/code_agent/commands.py + command_registry.py.
Cada command molda um prompt que é passado ao AgentLoop.run().

Comandos:
  /help     -- lista comandos
  /quit     -- sai do REPL
  /clear    -- limpa sessão
  /status   -- mostra estado
  /explain  -- analisa e explica arquivo
  /plan     -- cria plano de implementação
  /test     -- gera testes
  /compact  -- resume sessão
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("nyx.commands")


@dataclass
class CommandDef:
    name: str
    description: str
    handler: Any
    aliases: list[str] = field(default_factory=list)
    category: str = "geral"


_COMMANDS: dict[str, CommandDef] = {}


def nyx_command(name: str, description: str, aliases: list[str] | None = None, category: str = "geral"):
    """Decorador para registrar um comando."""
    def decorator(func: Any) -> Any:
        cmd = CommandDef(name=name, description=description, handler=func,
                         aliases=aliases or [], category=category)
        _COMMANDS[name] = cmd
        for alias in cmd.aliases:
            _COMMANDS[alias] = cmd
        return func
    return decorator


def get_command(name: str) -> CommandDef | None:
    return _COMMANDS.get(name.lower())


def list_commands() -> list[CommandDef]:
    seen: set[str] = set()
    result: list[CommandDef] = []
    for cmd in _COMMANDS.values():
        if cmd.name not in seen:
            seen.add(cmd.name)
            result.append(cmd)
    return sorted(result, key=lambda c: c.name)


def format_help() -> str:
    commands = list_commands()
    if not commands:
        return "Nenhum comando registrado."

    lines = ["", "  Comandos disponíveis:", ""]
    by_cat: dict[str, list[CommandDef]] = {}
    for cmd in commands:
        by_cat.setdefault(cmd.category, []).append(cmd)

    for cat, cmds in sorted(by_cat.items()):
        for cmd in cmds:
            aliases = f" ({', '.join('/' + a for a in cmd.aliases)})" if cmd.aliases else ""
            lines.append(f"    /{cmd.name:<12s}{aliases:16s} -- {cmd.description}")

    lines.append("")
    return "\n".join(lines)


# ── Comandos registrados ─────────────────────────────────────────


@nyx_command(name="help", description="Mostra esta ajuda", aliases=["h"])
def cmd_help(_args: str, _root: str) -> str:
    return format_help()


@nyx_command(name="quit", description="Sai do REPL", aliases=["q", "exit"])
def cmd_quit(_args: str, _root: str) -> str:
    return "__quit__"


@nyx_command(name="clear", description="Limpa a sessão")
def cmd_clear(_args: str, _root: str) -> str:
    return "__clear__"


@nyx_command(name="status", description="Mostra estado da sessão")
def cmd_status(_args: str, _root: str) -> str:
    return "__status__"


@nyx_command(name="explain", description="Analisa e explica um arquivo", aliases=["exp"],
             category="código")
def cmd_explain(file_path: str, project_root: str) -> str:
    full = Path(project_root) / file_path.strip()
    if not full.exists():
        return f"Arquivo '{file_path}' não encontrado. Verifique o caminho."

    return (
        f"Analise e explique o arquivo '{file_path}'. "
        "Passos:\n"
        f"1. Use read_file para ler '{file_path}'\n"
        "2. Identifique: propósito, classes/funções principais, dependências, "
        "padrões de design usados\n"
        "3. Use done(summary='explicação completa em português')"
    )


@nyx_command(name="plan", description="Cria plano de implementação",
             category="código")
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


@nyx_command(name="test", description="Gera testes para um arquivo", aliases=["tst"],
             category="código")
def cmd_test(file_path: str, project_root: str) -> str:
    full = Path(project_root) / file_path.strip()
    if not full.exists():
        return f"Arquivo '{file_path}' não encontrado."

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


@nyx_command(name="compact", description="Resume o que foi feito na sessão",
             category="sessão")
def cmd_compact(history_summary: str, _root: str) -> str:
    return (
        "Resuma o trabalho realizado até agora.\n"
        f"Histórico atual:\n{history_summary}\n\n"
        "Use done(summary='resumo') contendo:\n"
        "1. O que foi feito (arquivos lidos/editados)\n"
        "2. Decisões tomadas\n"
        "3. Próximos passos sugeridos"
    )


@nyx_command(name="commit", description="Cria um commit git", category="git")
def cmd_commit(message: str, project_root: str) -> str:
    return (
        "Crie um commit git com as mudanças atuais. Passos:\n"
        "1. Use run_command('git status --short') para ver mudanças\n"
        "2. Use run_command('git diff HEAD') para ver detalhes\n"
        "3. Use run_command('git log --oneline -5') para ver estilo de commits\n"
        "4. Analise as mudanças e crie mensagem de commit em PT-BR\n"
        "5. Use run_command('git add <arquivos relevantes>')\n"
        "6. Use run_command('git commit -m \"tipo: descrição\"')\n"
        "7. Use done(summary='commit criado: <hash> <mensagem>')\n\n"
        "Regras:\n"
        "- Mensagem em PT-BR, sem emojis, sem menção a IA\n"
        "- Nunca --force, --amend ou --no-verify sem autorização\n"
        "- Nunca commitar .env, credentials ou secrets\n"
        + (f"- Contexto adicional: {message}" if message else "")
    )


@nyx_command(name="diff", description="Mostra mudanças não commitadas", aliases=["d"],
             category="git")
def cmd_diff(_args: str, project_root: str) -> str:
    from nyx.agent.git_ops import git_diff_full, git_status
    ok_status, status = git_status(project_root)
    ok_diff, diff = git_diff_full(project_root)

    if not ok_status and not ok_diff:
        return "Erro ao obter diff. Verifique se é um repositório git."

    parts = []
    if status:
        parts.append(f"Status:\n{status}")
    if diff:
        parts.append(f"\nDiff:\n{diff}")
    else:
        parts.append("Nenhuma mudança pendente.")

    return "\n".join(parts)


@nyx_command(name="doctor", description="Diagnóstico do sistema", aliases=["dr"],
             category="sistema")
def cmd_doctor(_args: str, project_root: str) -> str:
    import subprocess
    from pathlib import Path as _Path

    checks: list[str] = []

    ollama_ok = False
    try:
        import httpx
        r = httpx.get("http://127.0.0.1:11435/api/version", timeout=5)
        ver = r.json().get("version", "?")
        checks.append(f"[OK] Ollama: v{ver} (porta 11435)")
        ollama_ok = True
    except Exception:
        checks.append("[ERRO] Ollama: não responde na porta 11435")

    try:
        import httpx
        r = httpx.get("http://127.0.0.1:11436/v1/models", timeout=5)
        models = r.json().get("data", [])
        checks.append(f"[OK] Proxy: {len(models)} modelo(s) (porta 11436)")
    except Exception:
        checks.append("[ERRO] Proxy: não responde na porta 11436")

    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total",
             "--format=csv,noheader,nounits"], text=True, timeout=5,
        ).strip()
        parts = out.split(",")
        gpu = parts[0].strip()
        used = parts[1].strip()
        total = parts[2].strip()
        checks.append(f"[OK] GPU: {gpu} ({used}/{total} MiB)")
    except Exception:
        checks.append("[AVISO] GPU: nvidia-smi indisponível")

    root = _Path(project_root)
    checks.append(f"[OK] Projeto: {root.name}" if root.exists() else f"[ERRO] Projeto: {root} não existe")

    venv = root / "venv"
    checks.append(f"[OK] Venv: {venv}" if venv.exists() else "[AVISO] Venv: não encontrado")

    env = root / ".env"
    checks.append(f"[OK] .env: presente" if env.exists() else "[AVISO] .env: não encontrado")

    return "Diagnóstico Nyx:\n" + "\n".join(f"  {c}" for c in checks)


@nyx_command(name="review", description="Review de pull request", aliases=["rv"],
             category="git")
def cmd_review(pr_number: str, project_root: str) -> str:
    if not pr_number.strip():
        return (
            "Use run_command('gh pr list') para ver PRs abertos.\n"
            "Depois use /review <número> para revisar uma PR específica."
        )

    return (
        f"Revise a PR #{pr_number}. Passos:\n"
        f"1. Use run_command('gh pr view {pr_number}') para detalhes\n"
        f"2. Use run_command('gh pr diff {pr_number}') para o diff\n"
        "3. Analise as mudanças focando em:\n"
        "   - Correção do código\n"
        "   - Conformidade com convenções do projeto\n"
        "   - Performance\n"
        "   - Cobertura de testes\n"
        "   - Segurança\n"
        "4. Use done(summary='review: <resumo>')\n\n"
        "Formato: seções claras com bullet points."
    )


@nyx_command(name="model", description="Mostra ou troca o modelo", aliases=["m"],
             category="sistema")
def cmd_model(model_name: str, _root: str) -> str:
    if not model_name.strip():
        import os
        current = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", "qwen3:4b"))
        return f"  Modelo atual: {current}\n  Use /model <nome> para trocar."
    return f"__model__{model_name.strip()}"


@nyx_command(name="context", description="Mostra uso do contexto", aliases=["ctx"],
             category="sessão")
def cmd_context(_args: str, _root: str) -> str:
    return "__context__"


@nyx_command(name="session", description="Gerencia sessões salvas", aliases=["sess"],
             category="sessão")
def cmd_session(action: str, _root: str) -> str:
    from nyx.agent.persistence import SESSIONS_DIR, load_latest_session

    action = action.strip().lower()

    if action == "list":
        if not SESSIONS_DIR.exists():
            return "  Nenhuma sessão salva."
        files = sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True)[:10]
        if not files:
            return "  Nenhuma sessão salva."
        lines = ["  Sessões recentes:"]
        for f in files:
            lines.append(f"    {f.name}")
        return "\n".join(lines)

    if action == "load" or action == "restore":
        session = load_latest_session()
        if session:
            return f"__session_load__"
        return "  Nenhuma sessão para restaurar."

    if action == "save":
        return "__session_save__"

    return (
        "  Uso: /session <ação>\n"
        "    list    -- lista sessões salvas\n"
        "    save    -- salva sessão atual\n"
        "    load    -- restaura última sessão"
    )


# ── P5-A: Git & GitHub ──────────────────────────────────────────


@nyx_command(name="branch", description="Operações de branch", aliases=["br"],
             category="git")
def cmd_branch(args: str, project_root: str) -> str:
    from nyx.agent.git_ops import run_git
    args = args.strip()
    if not args:
        ok, out = run_git(["branch", "--list"], project_root)
        return f"Branches:\n{out}" if ok else f"Erro: {out}"
    if args.startswith("-d "):
        branch = args[3:].strip()
        ok, out = run_git(["branch", "-d", branch], project_root)
        return out if ok else f"Erro: {out}"
    ok, out = run_git(["checkout", "-b", args], project_root)
    return out if ok else f"Erro ao criar branch: {out}"


@nyx_command(name="issue", description="Cria/lista issues via gh CLI",
             category="git")
def cmd_issue(args: str, project_root: str) -> str:
    import subprocess
    args = args.strip()
    try:
        if not args:
            r = subprocess.run(["gh", "issue", "list", "--limit", "10"],
                               capture_output=True, text=True, timeout=15, cwd=project_root)
            return r.stdout if r.stdout else "Nenhuma issue aberta."
        if args.isdigit():
            r = subprocess.run(["gh", "issue", "view", args],
                               capture_output=True, text=True, timeout=15, cwd=project_root)
            return r.stdout if r.stdout else f"Issue #{args} não encontrada."
        return (
            f"Crie uma issue sobre: {args}\n"
            "Use run_command('gh issue create --title \"...\" --body \"...\"')"
        )
    except FileNotFoundError:
        return "gh CLI não instalado. Instale: https://cli.github.com"


@nyx_command(name="pr", description="Lista/mostra PRs via gh CLI",
             category="git")
def cmd_pr(args: str, project_root: str) -> str:
    import subprocess
    args = args.strip()
    try:
        if not args:
            r = subprocess.run(["gh", "pr", "list", "--limit", "10"],
                               capture_output=True, text=True, timeout=15, cwd=project_root)
            return r.stdout if r.stdout else "Nenhuma PR aberta."
        if args.isdigit():
            r = subprocess.run(["gh", "pr", "view", args, "--comments"],
                               capture_output=True, text=True, timeout=15, cwd=project_root)
            return r.stdout if r.stdout else f"PR #{args} não encontrada."
        return f"Uso: /pr [número]"
    except FileNotFoundError:
        return "gh CLI não instalado. Instale: https://cli.github.com"


@nyx_command(name="rewind", description="Desfaz últimas N ações do agent",
             category="sessão")
def cmd_rewind(args: str, _root: str) -> str:
    n = 1
    if args.strip().isdigit():
        n = int(args.strip())
    return f"__rewind__{n}"


# ── P5-B: Configuração ────────────────────────────────────────


@nyx_command(name="config", description="Mostra ou edita configuração",
             category="sistema")
def cmd_config(args: str, project_root: str) -> str:
    import os
    args = args.strip()
    if not args:
        proxy = os.environ.get("OPENAI_BASE_URL", "http://127.0.0.1:11436/v1")
        model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", "qwen3:4b"))
        ollama = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11435")
        return (
            "  Configuração atual:\n"
            f"    modelo: {model}\n"
            f"    proxy: {proxy}\n"
            f"    ollama: {ollama}\n"
            f"    projeto: {project_root}"
        )
    parts = args.split(" ", 1)
    if len(parts) == 1:
        val = os.environ.get(parts[0].upper(), None)
        return f"  {parts[0]}: {val}" if val else f"  Chave '{parts[0]}' não definida."
    return f"  Configuração via env: export {parts[0].upper()}={parts[1]}"


@nyx_command(name="env", description="Mostra variáveis de ambiente relevantes",
             category="sistema")
def cmd_env(_args: str, _root: str) -> str:
    import os
    prefixes = ("OPENAI_", "NYX_", "OLLAMA_", "ANTHROPIC_API")
    lines = ["  Variáveis de ambiente:"]
    for key, val in sorted(os.environ.items()):
        if any(key.startswith(p) for p in prefixes):
            display = val[:40] + "..." if len(val) > 40 else val
            lines.append(f"    {key}={display}")
    if len(lines) == 1:
        lines.append("    (nenhuma variável NYX/OPENAI/OLLAMA definida)")
    return "\n".join(lines)


@nyx_command(name="permissions", description="Mostra permissões por tool", aliases=["perms"],
             category="sistema")
def cmd_permissions(_args: str, _root: str) -> str:
    from nyx.agent.permissions import PermissionChecker
    pc = PermissionChecker()
    tools_by_level: dict[str, list[str]] = {}
    for tool in ["read_file", "write_file", "edit_file", "run_command",
                 "glob", "search", "list_files", "done", "agent",
                 "todo_write", "web_fetch", "web_search", "notebook_edit"]:
        level = str(pc.check(tool))
        tools_by_level.setdefault(level, []).append(tool)

    lines = ["  Permissões por nível:"]
    for level, tools in sorted(tools_by_level.items()):
        lines.append(f"    [{level}]")
        for t in tools:
            lines.append(f"      - {t}")
    return "\n".join(lines)


@nyx_command(name="hooks", description="Lista hooks registrados",
             category="sistema")
def cmd_hooks(_args: str, _root: str) -> str:
    return (
        "  Hooks são registrados via ToolRegistry.\n"
        "  Tipos: pre (antes da tool), post (depois da tool)\n"
        "  Exemplo: path_guard bloqueia acesso a .env\n"
        "  Use /doctor para verificar estado do sistema."
    )


@nyx_command(name="theme", description="Lista ou troca tema de cores",
             category="sistema")
def cmd_theme(args: str, _root: str) -> str:
    try:
        from nyx.themes import ThemeManager
        tm = ThemeManager()
        args = args.strip()
        if not args or args == "list":
            temas = tm.list_themes()
            lines = ["  Temas disponíveis:"]
            for t in temas:
                lines.append(f"    - {t}")
            return "\n".join(lines)
        theme = tm.load_theme(args)
        if theme:
            return f"  Tema '{args}' carregado. Primary: {theme.get('primary', '?')}"
        return f"  Tema '{args}' não encontrado."
    except ImportError:
        return "  Módulo de temas não disponível."


# ── P5-C: Sessão & Métricas ──────────────────────────────────


@nyx_command(name="resume", description="Restaura sessão anterior",
             category="sessão")
def cmd_resume(_args: str, _root: str) -> str:
    return "__session_load__"


@nyx_command(name="export", description="Exporta sessão para arquivo",
             category="sessão")
def cmd_export(args: str, _root: str) -> str:
    return "__export__" + (args.strip() or "md")


@nyx_command(name="copy", description="Copia último output para clipboard",
             category="sessão")
def cmd_copy(_args: str, _root: str) -> str:
    return "__copy__"


@nyx_command(name="summary", description="Gera resumo da sessão",
             category="sessão")
def cmd_summary(_args: str, _root: str) -> str:
    return (
        "Gere um resumo do trabalho realizado nesta sessão.\n"
        "Inclua:\n"
        "1. Ações tomadas (leituras, edições, comandos)\n"
        "2. Arquivos modificados\n"
        "3. Decisões-chave\n"
        "4. Próximos passos sugeridos\n"
        "Use done(summary='resumo completo em PT-BR')"
    )


@nyx_command(name="stats", description="Estatísticas detalhadas da sessão",
             category="sessão")
def cmd_stats(_args: str, _root: str) -> str:
    return "__stats__"


@nyx_command(name="usage", description="Uso de tokens e contexto",
             category="sessão")
def cmd_usage(_args: str, _root: str) -> str:
    return "__usage__"


# ── P5-D: Execução ──────────────────────────────────────────


@nyx_command(name="tasks", description="Gerencia tarefas",
             category="execução")
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

    return "  Uso: /tasks [list|create <título>|done <id>]"


@nyx_command(name="skills", description="Lista skills disponíveis",
             category="execução")
def cmd_skills(_args: str, _root: str) -> str:
    from nyx.agent.tools.skill_tool import _list_skills
    skills = _list_skills()
    if not skills:
        return "  Nenhum skill em ~/.nyx/skills/. Crie arquivos .py com função execute()."
    lines = ["  Skills disponíveis:"]
    for name, desc in skills:
        lines.append(f"    - {name}: {desc}")
    return "\n".join(lines)


@nyx_command(name="files", description="Mostra arquivos no contexto",
             category="execução")
def cmd_files(_args: str, _root: str) -> str:
    return "__files__"



@nyx_command(name="add-dir", description="Adiciona diretório ao contexto do agent",
             category="projeto")
def cmd_add_dir(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Adiciona diretório ao contexto do agent. "
        "Use /help para mais informações."
    )


@nyx_command(name="init", description="Inicializa projeto Nyx",
             category="projeto")
def cmd_init(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Inicializa projeto Nyx. "
        "Use /help para mais informações."
    )


@nyx_command(name="onboarding", description="Tour guiado para novos usuários",
             category="projeto")
def cmd_onboarding(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Tour guiado para novos usuários. "
        "Use /help para mais informações."
    )


@nyx_command(name="version", description="Mostra versão do Nyx",
             category="projeto", aliases=['v'])
def cmd_version(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Mostra versão do Nyx. "
        "Use /help para mais informações."
    )


@nyx_command(name="rename", description="Renomeia sessão ou projeto",
             category="projeto")
def cmd_rename(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Renomeia sessão ou projeto. "
        "Use /help para mais informações."
    )


@nyx_command(name="color", description="Configura cores do terminal",
             category="ui")
def cmd_color(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Configura cores do terminal. "
        "Use /help para mais informações."
    )


@nyx_command(name="output-style", description="Estilo de output",
             category="ui")
def cmd_output_style(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Estilo de output. "
        "Use /help para mais informações."
    )


@nyx_command(name="keybindings", description="Configura atalhos de teclado",
             category="ui", aliases=['kb'])
def cmd_keybindings(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Configura atalhos de teclado. "
        "Use /help para mais informações."
    )


@nyx_command(name="stickers", description="Marcadores visuais para sessões",
             category="ui")
def cmd_stickers(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Marcadores visuais para sessões. "
        "Use /help para mais informações."
    )


@nyx_command(name="fast", description="Toggle modo rápido",
             category="ui")
def cmd_fast(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Toggle modo rápido. "
        "Use /help para mais informações."
    )


@nyx_command(name="effort", description="Define nível de esforço do agent",
             category="ui")
def cmd_effort(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Define nível de esforço do agent. "
        "Use /help para mais informações."
    )


@nyx_command(name="vim", description="Toggle modo vim",
             category="ui")
def cmd_vim(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Toggle modo vim. "
        "Use /help para mais informações."
    )


@nyx_command(name="trace", description="Trace de execução do agent loop",
             category="debug")
def cmd_trace(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Trace de execução do agent loop. "
        "Use /help para mais informações."
    )


@nyx_command(name="autofix-pr", description="Auto-fix de PRs via agent",
             category="debug")
def cmd_autofix_pr(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Auto-fix de PRs via agent. "
        "Use /help para mais informações."
    )


@nyx_command(name="bughunter", description="Busca automática de bugs",
             category="debug")
def cmd_bughunter(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Busca automática de bugs. "
        "Use /help para mais informações."
    )


@nyx_command(name="ctx-viz", description="Visualização do contexto",
             category="debug")
def cmd_ctx_viz(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Visualização do contexto. "
        "Use /help para mais informações."
    )


@nyx_command(name="debug-tool", description="Debug de chamadas de tool",
             category="debug")
def cmd_debug_tool(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Debug de chamadas de tool. "
        "Use /help para mais informações."
    )


@nyx_command(name="heapdump", description="Dump do estado da memória",
             category="debug")
def cmd_heapdump(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Dump do estado da memória. "
        "Use /help para mais informações."
    )


@nyx_command(name="perf-issue", description="Diagnóstico de performance",
             category="debug")
def cmd_perf_issue(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Diagnóstico de performance. "
        "Use /help para mais informações."
    )


@nyx_command(name="kudos", description="Feedback positivo registrado localmente",
             category="debug")
def cmd_kudos(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Feedback positivo registrado localmente. "
        "Use /help para mais informações."
    )


@nyx_command(name="break-cache", description="Limpa caches internos",
             category="debug")
def cmd_break_cache(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Limpa caches internos. "
        "Use /help para mais informações."
    )


@nyx_command(name="upgrade", description="Atualiza versão do Nyx",
             category="lifecycle")
def cmd_upgrade(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Atualiza versão do Nyx. "
        "Use /help para mais informações."
    )


@nyx_command(name="sandbox", description="Modo sandbox isolado",
             category="lifecycle")
def cmd_sandbox(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Modo sandbox isolado. "
        "Use /help para mais informações."
    )


@nyx_command(name="terminal-setup", description="Setup do terminal",
             category="lifecycle")
def cmd_terminal_setup(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Setup do terminal. "
        "Use /help para mais informações."
    )


@nyx_command(name="rate-limit", description="Mostra rate limits",
             category="limites")
def cmd_rate_limit(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Mostra rate limits. "
        "Use /help para mais informações."
    )


@nyx_command(name="reset-limits", description="Reseta limites locais",
             category="limites")
def cmd_reset_limits(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Reseta limites locais. "
        "Use /help para mais informações."
    )


@nyx_command(name="memory", description="Gerencia memória do agent",
             category="memória", aliases=['mem'])
def cmd_memory(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Gerencia memória do agent. "
        "Use /help para mais informações."
    )


@nyx_command(name="plugin", description="Gerencia plugins",
             category="memória")
def cmd_plugin(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Gerencia plugins. "
        "Use /help para mais informações."
    )


@nyx_command(name="reload-plugins", description="Recarrega plugins",
             category="memória")
def cmd_reload_plugins(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Recarrega plugins. "
        "Use /help para mais informações."
    )


@nyx_command(name="agents", description="Lista agents disponíveis",
             category="memória")
def cmd_agents(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Lista agents disponíveis. "
        "Use /help para mais informações."
    )


@nyx_command(name="tag", description="Tags para organização",
             category="memória")
def cmd_tag(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Tags para organização. "
        "Use /help para mais informações."
    )


@nyx_command(name="btw", description="Nota lateral para o agent",
             category="avançado")
def cmd_btw(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Nota lateral para o agent. "
        "Use /help para mais informações."
    )


@nyx_command(name="backfill", description="Preenche contexto retroativo",
             category="avançado")
def cmd_backfill(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Preenche contexto retroativo. "
        "Use /help para mais informações."
    )


@nyx_command(name="thinkback", description="Revisão de raciocínio",
             category="avançado")
def cmd_thinkback(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Revisão de raciocínio. "
        "Use /help para mais informações."
    )


@nyx_command(name="thinkback-play", description="Replay de raciocínio",
             category="avançado")
def cmd_thinkback_play(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Replay de raciocínio. "
        "Use /help para mais informações."
    )


@nyx_command(name="pr-comments", description="Mostra comentários de PR",
             category="avançado")
def cmd_pr_comments(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Mostra comentários de PR. "
        "Use /help para mais informações."
    )


@nyx_command(name="advisor", description="Conselheiro de código",
             category="root")
def cmd_advisor(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Conselheiro de código. "
        "Use /help para mais informações."
    )


@nyx_command(name="brief-cmd", description="Resumo rápido",
             category="root")
def cmd_brief_cmd(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Resumo rápido. "
        "Use /help para mais informações."
    )


@nyx_command(name="commit-push-pr", description="Commit, push e PR",
             category="root")
def cmd_commit_push_pr(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Commit, push e PR. "
        "Use /help para mais informações."
    )


@nyx_command(name="insights", description="Insights do projeto",
             category="root")
def cmd_insights(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Insights do projeto. "
        "Use /help para mais informações."
    )


@nyx_command(name="security-review", description="Review de segurança",
             category="root")
def cmd_security_review(args: str, project_root: str) -> str:
    args = args.strip()
    return (
        "Review de segurança. "
        "Use /help para mais informações."
    )

def handle_command(cmd_input: str, project_root: str = ".") -> str | None:
    """Processa um slash command. Retorna None se não é comando."""
    if not cmd_input.startswith("/"):
        return None

    parts = cmd_input[1:].split(" ", 1)
    name = parts[0].lower()
    args = parts[1].strip() if len(parts) > 1 else ""

    cmd = get_command(name)
    if not cmd:
        return f"  Comando desconhecido: /{name}. Use /help."

    return cmd.handler(args, project_root)


# "O terminal é o lar do programador." -- Ken Thompson
