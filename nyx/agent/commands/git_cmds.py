"""Comandos git/GitHub -- commit, diff, review, branch, issue, pr, pr-comments, commit-push-pr."""

from __future__ import annotations

import subprocess

from nyx.agent.commands._registry import nyx_command


@nyx_command(name="commit", description="Cria um commit git", category="git",
    examples=['/commit -m "fix: regex do parser"', '/commit --amend', '/commit'],
)
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
        "- Nunca commitar .env, credentials ou secrets\n" + (f"- Contexto adicional: {message}" if message else "")
    )


@nyx_command(name="diff", description="Mostra mudanças não commitadas", aliases=["d"], category="git",
    examples=['/diff', '/diff HEAD~1', '/diff nyx/cli.py'],
)
def cmd_diff(_args: str, project_root: str) -> str:
    from nyx.agent.git_ops import git_diff_full, git_status

    ok_status, status = git_status(project_root)
    ok_diff, diff = git_diff_full(project_root)

    if not ok_status and not ok_diff:
        return (
            "__error__Falha ao obter o diff do repositório."
            "||Confirme que está dentro de um repositório git com: git rev-parse --show-toplevel"
        )

    parts = []
    if status:
        parts.append(f"Status:\n{status}")
    if diff:
        parts.append(f"\nDiff:\n{diff}")
    else:
        parts.append("Nenhuma mudança pendente.")

    return "\n".join(parts)


@nyx_command(name="review", description="Review de pull request", aliases=["rv"], category="git",
    examples=['/review', '/review 123'],
)
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


@nyx_command(name="branch", description="Operações de branch", aliases=["br"], category="git",
    examples=['/branch', '/branch feature-x'],
)
def cmd_branch(args: str, project_root: str) -> str:
    from nyx.agent.git_ops import run_git

    args = args.strip()
    if not args:
        ok, out = run_git(["branch", "--list"], project_root)
        if ok:
            return f"Branches:\n{out}"
        return f"__error__Falha ao listar branches.||Detalhe: {out.strip()[:120]}"
    if args.startswith("-d "):
        branch = args[3:].strip()
        ok, out = run_git(["branch", "-d", branch], project_root)
        if ok:
            return out
        return f"__error__Falha ao remover a branch '{branch}'.||Detalhe: {out.strip()[:120]}"
    ok, out = run_git(["checkout", "-b", args], project_root)
    if ok:
        return out
    return f"__error__Falha ao criar a branch '{args}'.||Detalhe: {out.strip()[:120]}"


@nyx_command(name="issue", description="Cria/lista issues via gh CLI", category="git",
    examples=['/issue', '/issue 42'],
)
def cmd_issue(args: str, project_root: str) -> str:
    args = args.strip()
    try:
        if not args:
            r = subprocess.run(
                ["gh", "issue", "list", "--limit", "10"], capture_output=True, text=True, timeout=15, cwd=project_root
            )
            return r.stdout if r.stdout else "Nenhuma issue aberta."
        if args.isdigit():
            r = subprocess.run(
                ["gh", "issue", "view", args], capture_output=True, text=True, timeout=15, cwd=project_root
            )
            if r.stdout:
                return r.stdout
            return (
                f"__error__Issue #{args} não encontrada neste repositório."
                "||Liste issues abertas com /issue (sem argumento)."
            )
        return f'Crie uma issue sobre: {args}\nUse run_command(\'gh issue create --title "..." --body "..."\')'
    except FileNotFoundError:
        return (
            "__error__gh CLI não está instalado no sistema."
            "||Instale com: sudo apt install gh -- ou veja https://cli.github.com"
        )


@nyx_command(name="pr", description="Lista/mostra PRs via gh CLI", category="git",
    examples=['/pr', '/pr 123'],
)
def cmd_pr(args: str, project_root: str) -> str:
    args = args.strip()
    try:
        if not args:
            r = subprocess.run(
                ["gh", "pr", "list", "--limit", "10"], capture_output=True, text=True, timeout=15, cwd=project_root
            )
            return r.stdout if r.stdout else "Nenhuma PR aberta."
        if args.isdigit():
            r = subprocess.run(
                ["gh", "pr", "view", args, "--comments"], capture_output=True, text=True, timeout=15, cwd=project_root
            )
            if r.stdout:
                return r.stdout
            return (
                f"__error__PR #{args} não encontrada neste repositório."
                "||Liste PRs abertas com /pr (sem argumento)."
            )
        return (
            "__error__Argumento inválido para /pr."
            "||Uso correto: /pr [número] -- sem argumento lista as PRs abertas."
        )
    except FileNotFoundError:
        return (
            "__error__gh CLI não está instalado no sistema."
            "||Instale com: sudo apt install gh -- ou veja https://cli.github.com"
        )


@nyx_command(name="pr-comments", description="Mostra comentários de PR", category="avançado",
    examples=['/pr-comments', '/pr-comments 123'],
)
def cmd_pr_comments(args: str, project_root: str) -> str:
    pr_number = args.strip()
    if not pr_number or not pr_number.isdigit():
        return (
            "__error__Argumento inválido para /pr-comments."
            "||Uso correto: /pr-comments <número> -- ex: /pr-comments 123"
        )
    try:
        r = subprocess.run(
            [
                "gh",
                "pr",
                "view",
                pr_number,
                "--comments",
                "--json",
                "comments",
                "--jq",
                '.comments[] | "\\(.author.login): \\(.body[:100])"',
            ],
            capture_output=True,
            text=True,
            timeout=15,
            cwd=project_root,
        )
        if r.stdout.strip():
            return f"  Comentários da PR #{pr_number}:\n{r.stdout}"
        return (
            f"__error__PR #{pr_number} não possui comentários."
            "||Abra a PR para comentar: gh pr view {pr_number} --web"
        )
    except FileNotFoundError:
        return (
            "__error__gh CLI não está instalado no sistema."
            "||Instale com: sudo apt install gh -- ou veja https://cli.github.com"
        )


@nyx_command(name="commit-push-pr", description="Commit, push e PR", category="root",
    examples=['/commit-push-pr', '/commit-push-pr --draft'],
)
def cmd_commit_push_pr(args: str, project_root: str) -> str:
    return (
        "Execute o fluxo completo: commit, push e PR. Passos:\n"
        "1. Use run_command('git status --short') para ver mudanças\n"
        "2. Use run_command('git diff HEAD') para ver detalhes\n"
        "3. Use run_command('git log --oneline -5') para estilo de commits\n"
        "4. Analise e crie mensagem de commit PT-BR, sem emojis, sem IA\n"
        "5. Use run_command('git add <arquivos>')\n"
        "6. Use run_command('git commit -m \"tipo: descrição\"')\n"
        "7. Use run_command('git push -u origin <branch>')\n"
        '8. Use run_command(\'gh pr create --title "..." --body "..."\')\n'
        "9. Use done(summary='PR criada: <url>')\n" + (f"\nContexto: {args}" if args.strip() else "")
    )


# "Versionar é lembrar o que se quis esquecer." -- Linus Torvalds
