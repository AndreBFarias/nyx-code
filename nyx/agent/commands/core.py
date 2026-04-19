"""Comandos core -- help, quit, clear, status, tools, memory, recall, paste."""

from __future__ import annotations

from pathlib import Path

from nyx.agent.commands._registry import format_help, nyx_command


@nyx_command(name="help", description="Mostra esta ajuda (/help all pra todos)", aliases=["h"])
def cmd_help(args: str, _root: str) -> str:
    show_all = args.strip().lower() in ("all", "todos", "*")
    return format_help(show_all=show_all)


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
            "Sem memórias gravadas pra este projeto. A Nyx grava via tool "
            "write_memory quando você pede pra lembrar algo estável."
        )
    lines = [f"  Memórias em {mem.directory}:", ""]
    for e in entries:
        reason = e.get("reason") or ""
        lines.append(f"    {e['file']:<24s} -- {reason}")
    lines.append("")
    lines.append("  (use /memory show <nome> para ver conteúdo)")
    return "\n".join(lines)


@nyx_command(
    name="recall",
    description="Busca em memória de sessões anteriores (SessionMemory JSON)",
    category="memória",
    aliases=["rec"],
)
def cmd_recall(args: str, _root: str) -> str:
    from nyx.agent.services.memory import SessionMemory

    mem = SessionMemory()
    action = args.strip().lower()

    if not action or action == "list":
        memories = mem.get_recent(n=20)
        if not memories:
            return "  Nenhuma memória salva."
        lines = ["  Memórias recentes:"]
        for m in memories:
            tags = f" [{', '.join(m.tags)}]" if m.tags else ""
            lines.append(f"    - {m.key}: {m.content[:60]}{tags}")
        return "\n".join(lines)

    if action.startswith("search "):
        query = action[7:].strip()
        results = mem.search(query)
        if not results:
            return f"  Nenhuma memória para '{query}'."
        lines = [f"  Resultados para '{query}':"]
        for m in results:
            lines.append(f"    - {m.key}: {m.content[:60]}")
        return "\n".join(lines)

    return (
        "  Uso: /recall [ação]\n"
        "    list              -- lista memórias recentes\n"
        "    search <termo>    -- busca nas memórias"
    )


@nyx_command(name="paste", description="Lista imagens coladas na sessão (Ctrl+V)", category="contexto")
def cmd_paste(_args: str, _project_root: str) -> str:
    pastes = Path.home() / ".nyx" / "pastes"
    if not pastes.exists():
        return "Nenhuma imagem colada ainda. Use Ctrl+V com imagem no clipboard."
    files = sorted(pastes.glob("*.png"))[-20:]
    if not files:
        return "Nenhuma imagem em ~/.nyx/pastes/."
    lines = [f"  Últimas {len(files)} imagens em {pastes}:", ""]
    for f in files:
        size_kb = f.stat().st_size / 1024
        lines.append(f"    {f.name:<32s} {size_kb:>7.1f} KB")
    return "\n".join(lines)


# "Comece pelo simples -- o resto vem." -- Kernighan
