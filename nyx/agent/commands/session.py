"""Comandos de sessão -- session, resume, rewind, export, copy, summary, stats, usage, context, btw, files, trace."""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command


@nyx_command(name="context", description="Mostra uso do contexto", aliases=["ctx"], category="sessão")
def cmd_context(_args: str, _root: str) -> str:
    return "__context__"


@nyx_command(name="session", description="Gerencia sessões salvas", aliases=["sess"], category="sessão")
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
            return "__session_load__"
        return "  Nenhuma sessão para restaurar."

    if action == "save":
        return "__session_save__"

    return (
        "  Uso: /session <ação>\n"
        "    list    -- lista sessões salvas\n"
        "    save    -- salva sessão atual\n"
        "    load    -- restaura última sessão"
    )


@nyx_command(name="rewind", description="Desfaz últimas N ações do agent", category="sessão")
def cmd_rewind(args: str, _root: str) -> str:
    n = 1
    if args.strip().isdigit():
        n = int(args.strip())
    return f"__rewind__{n}"


@nyx_command(name="resume", description="Restaura sessão anterior", category="sessão")
def cmd_resume(_args: str, _root: str) -> str:
    return "__session_load__"


@nyx_command(name="export", description="Exporta sessão para arquivo", category="sessão")
def cmd_export(args: str, _root: str) -> str:
    return "__export__" + (args.strip() or "md")


@nyx_command(name="copy", description="Copia último output para clipboard", category="sessão")
def cmd_copy(_args: str, _root: str) -> str:
    return "__copy__"


@nyx_command(name="summary", description="Gera resumo da sessão", category="sessão")
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


@nyx_command(name="stats", description="Estatísticas detalhadas da sessão", category="sessão")
def cmd_stats(_args: str, _root: str) -> str:
    return "__stats__"


@nyx_command(name="usage", description="Uso de tokens e contexto", category="sessão")
def cmd_usage(_args: str, _root: str) -> str:
    return "__usage__"


@nyx_command(name="files", description="Mostra arquivos no contexto", category="execução")
def cmd_files(_args: str, _root: str) -> str:
    return "__files__"


@nyx_command(name="trace", description="Trace de execução do agent loop", category="debug")
def cmd_trace(_args: str, _root: str) -> str:
    return "__trace__"


@nyx_command(name="btw", description="Nota lateral para o agent", category="avançado")
def cmd_btw(args: str, _root: str) -> str:
    note = args.strip()
    if not note:
        return "  Uso: /btw <nota> -- injeta contexto sem gerar resposta"
    return f"__btw__{note}"


# "Quem não grava a sessão, repete a sessão." -- lema do shell
