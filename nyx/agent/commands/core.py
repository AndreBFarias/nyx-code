"""Comandos core -- help, quit, clear, status, tools, memory, recall, paste."""

from __future__ import annotations

from pathlib import Path

from nyx.agent.commands._registry import format_help, nyx_command


@nyx_command(name="help", description="Mostra esta ajuda (/help <filtro>, /help all)", aliases=["h"])
def cmd_help(args: str, _root: str) -> str:
    arg = args.strip().lower()
    if arg in ("all", "todos", "*"):
        return format_help(show_all=True)
    if arg:
        return format_help(show_all=False, filter_query=arg)
    return format_help(show_all=False)


@nyx_command(name="quit", description="Sai do REPL", aliases=["q", "exit"])
def cmd_quit(_args: str, _root: str) -> str:
    return "__quit__"


@nyx_command(name="clear", description="Limpa a sessão")
def cmd_clear(_args: str, _root: str) -> str:
    return "__clear__"


@nyx_command(name="status", description="Mostra estado da sessão")
def cmd_status(_args: str, _root: str) -> str:
    return "__status__"


@nyx_command(name="tools", description="Lista ferramentas (tools) disponíveis no agent", category="contexto")
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


@nyx_command(name="memory", description="Lista memórias persistentes do projeto", category="contexto")
def cmd_memory(args: str, project_root: str) -> str:
    from nyx.agent.memory import NyxMemory

    mem = NyxMemory(project_root)
    arg = args.strip()
    if arg.startswith("show "):
        name = arg[5:].strip()
        target = mem.directory / (name if name.endswith(".md") else f"{name}.md")
        if not target.exists():
            return f"Memória '{name}' não existe. Use /memory pra listar."
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
)
def cmd_recall(args: str, project_root: str) -> str:
    from nyx.agent.memory import NyxMemory

    termo = args.strip()
    if not termo:
        return "uso: /recall <termo>"

    mem = NyxMemory(project_root)
    entries = mem.index()
    if not entries:
        return "Nenhuma memória gravada para buscar."

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
        return f"Nenhuma ocorrência de '{termo}' nas memórias."
    return "\n".join(resultados)


@nyx_command(name="paste", description="Lista imagens coladas na sessão (Ctrl+V)", category="contexto")
def cmd_paste(_args: str, _project_root: str) -> str:
    pastes = Path.home() / ".nyx" / "pastes"
    if not pastes.exists():
        return "Nenhuma imagem colada ainda. Use Ctrl+V com imagem no clipboard."
    files = sorted(pastes.glob("*.png"), key=lambda p: p.stat().st_mtime)[-20:]
    if not files:
        return "Nenhuma imagem em ~/.nyx/pastes/."
    lines = [f"  Últimas {len(files)} imagens em {pastes}:", ""]
    for n, f in enumerate(files, start=1):
        lines.append(f"  #{n} {f}")
    return "\n".join(lines)


# "Comece pelo simples -- o resto vem." -- Kernighan
