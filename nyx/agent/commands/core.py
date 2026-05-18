"""Comandos core -- help, quit, clear, status, tools, memory, recall, paste."""

from __future__ import annotations

from pathlib import Path

from nyx.agent.commands._registry import format_help, get_command, nyx_command


@nyx_command(
    name="?",
    description="Ajuda contextual (UX-AGENCY-01): mostra 3 ações relevantes ao estado atual",
    category="contexto",
    examples=["/?", "/? sugere próximo passo dado o estado neutro"],
)
def cmd_contextual_help(_args: str, _root: str) -> str:
    """ADR-026 §affordances: /? imprime as 3 ações principais do estado neutro."""
    return (
        "  Ações disponíveis agora:\n"
        f"    /help                 -- catálogo completo de comandos\n"
        f"    /memory               -- memória persistente do projeto\n"
        f"    /resume               -- retomar sessão anterior\n"
        f"  (Em tool call ativa: Ctrl+C cancela; /cancel pausa fluxo)"
    )


@nyx_command(
    name="cancel",
    description="Cancela tool em curso (UX-AGENCY-01)",
    category="execução",
    examples=["/cancel", "/cancel forçar"],
)
def cmd_cancel(_args: str, _root: str) -> str:
    return "__cancel_inflight__"


@nyx_command(
    name="help",
    description="Mostra esta ajuda (/help <cmd> mostra exemplos; /help all lista tudo)",
    aliases=["h"],
    examples=["/help", "/help commit", "/help all"],
)
def cmd_help(args: str, _root: str) -> str:
    arg = args.strip().lstrip("/").lower()
    if arg in ("all", "todos", "*"):
        return format_help(show_all=True)
    if arg:
        # HELP-EXAMPLES-01: nome exato -> descrição + exemplos; fallback fuzzy.
        cmd = get_command(arg)
        if cmd is not None:
            lines = [f"  /{cmd.name} -- {cmd.description}"]
            if cmd.aliases:
                lines.append(f"    aliases: {', '.join('/' + a for a in cmd.aliases)}")
            if cmd.examples:
                lines.append("")
                lines.append("  Exemplos:")
                for ex in cmd.examples:
                    lines.append(f"    {ex}")
            else:
                lines.append("    (sem exemplos cadastrados)")
            return "\n".join(lines)
        return format_help(show_all=False, filter_query=arg)
    return format_help(show_all=False)


@nyx_command(
    name="quit",
    description="Sai do REPL salvando a sessão atual",
    aliases=["q", "exit"],
    examples=["/quit", "/q"],
)
def cmd_quit(_args: str, _root: str) -> str:
    return "__quit__"


@nyx_command(
    name="clear",
    description="Limpa a sessão (histórico, tela)",
    examples=["/clear", "/clear all"],
)
def cmd_clear(_args: str, _root: str) -> str:
    return "__clear__"


@nyx_command(
    name="status",
    description="Mostra estado da sessão (iterações, tokens, contexto)",
    examples=["/status", "/status verbose"],
)
def cmd_status(_args: str, _root: str) -> str:
    return "__status__"


@nyx_command(
    name="tools",
    description="Lista ferramentas (tools) disponíveis no agent",
    category="contexto",
    examples=["/tools", "/tools git", "/tools read"],
)
def cmd_tools(args: str, project_root: str) -> str:
    from nyx.agent.tools.registry import ToolRegistry

    reg = ToolRegistry(project_root)
    arg = args.strip().lower()
    lines = [f"  Tools registradas ({reg.tool_count}):", ""]
    for tool_def in sorted(reg.tool_defs, key=lambda t: t["function"]["name"]):
        fn = tool_def["function"]
        name = fn["name"]
        desc = fn.get("description", "")
        if arg and arg not in name.lower():
            continue
        lines.append(f"    {name:<18s} -- {desc[:70]}")
    if arg:
        lines.append("")
        lines.append(f"  (filtro: '{arg}')")
    return "\n".join(lines)


@nyx_command(
    name="memory",
    description="Lista memórias persistentes do projeto",
    category="contexto",
    examples=["/memory", "/memory show nyx_overview"],
)
def cmd_memory(args: str, project_root: str) -> str:
    from nyx.agent.memory import NyxMemory

    mem = NyxMemory(project_root)
    arg = args.strip()
    if arg.startswith("show "):
        name = arg[5:].strip()
        target = mem.directory / (name if name.endswith(".md") else f"{name}.md")
        if not target.exists():
            return (
                f"__error__Memória '{name}' não foi encontrada em {mem.directory}."
                "||Liste as memórias disponíveis com /memory."
            )
        return target.read_text(encoding="utf-8", errors="replace")
    entries = mem.index()
    if not entries:
        return (
            "Sem memórias gravadas. A Nyx grava via tool "
            "write_memory quando você pede pra lembrar algo estável."
        )
    lines = [f"  Memórias em {mem.directory}:", ""]
    for e in entries:
        reason = e.get("reason") or ""
        lines.append(f"- {e['file']}: {reason}")
    lines.append("")
    lines.append("  (use /memory show <nome> para ver conteúdo)")
    return "\n".join(lines)


@nyx_command(
    name="recall",
    description="Busca textual nas memórias do projeto (/recall <termo>)",
    category="memória",
    aliases=["rec"],
    examples=["/recall pyenv", "/recall sessão", "/recall ADR"],
)
def cmd_recall(args: str, project_root: str) -> str:
    from nyx.agent.memory import NyxMemory

    termo = args.strip()
    if not termo:
        return (
            "__error__Argumento obrigatório ausente em /recall."
            "||Use: /recall <termo> -- busca textual nas memórias do projeto."
        )

    mem = NyxMemory(project_root)
    entries = mem.index()
    if not entries:
        return (
            "__error__Nenhuma memória gravada neste projeto."
            "||Peça à Nyx para lembrar algo estável e rode /recall depois."
        )

    termo_lower = termo.lower()
    resultados: list[str] = []
    for entry in entries:
        fname = entry["file"]
        target = mem.directory / entry.get("href", f"{fname}.md")
        try:
            conteudo = target.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            resultados.append(f"  [erro ao ler {fname}: {exc}]")
            continue
        for n, linha in enumerate(conteudo.splitlines(), start=1):
            if termo_lower in linha.lower():
                resultados.append(f"  {fname}:{n}: {linha.strip()}")

    if not resultados:
        return (
            f"__error__Nenhuma ocorrência de '{termo}' nas memórias do projeto."
            "||Tente um termo mais curto ou liste as memórias com /memory."
        )
    return "\n".join(resultados)


@nyx_command(
    name="paste",
    description="Lista imagens coladas na sessão (Ctrl+V)",
    category="contexto",
    examples=["/paste", "/paste limpar"],
)
def cmd_paste(_args: str, _project_root: str) -> str:
    pastes = Path.home() / ".nyx" / "pastes"
    if not pastes.exists():
        return (
            "__error__Nenhuma imagem colada ainda nesta sessão."
            "||Use Ctrl+V com uma imagem no clipboard para colar."
        )
    files = sorted(pastes.glob("*.png"), key=lambda p: p.stat().st_mtime)[-20:]
    if not files:
        return (
            "__error__Diretório ~/.nyx/pastes/ está vazio."
            "||Cole uma imagem com Ctrl+V antes de usar /paste."
        )
    lines = [f"  Últimas {len(files)} imagens em {pastes}:", ""]
    for n, f in enumerate(files, start=1):
        lines.append(f"  #{n} {f}")
    return "\n".join(lines)


# "Comece pelo simples -- o resto vem." -- Kernighan
