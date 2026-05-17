"""Comandos de sessão -- session, resume, rewind, export, copy, summary, stats, usage, context, btw, files, trace."""

from __future__ import annotations

from nyx.agent.commands._registry import nyx_command


@nyx_command(name="context", description="Mostra uso do contexto", aliases=["ctx"], category="sessão",
    examples=['/context', '/ctx'],
)
def cmd_context(_args: str, _root: str) -> str:
    return "__context__"


@nyx_command(name="session", description="Gerencia sessões salvas", aliases=["sess"], category="sessão",
    examples=['/session list', '/session save', '/session load'],
)
def cmd_session(action: str, _root: str) -> str:
    from nyx.agent.persistence import SESSIONS_DIR, load_latest_session

    action = action.strip().lower()

    if action == "list":
        if not SESSIONS_DIR.exists():
            return (
                "__error__Diretório de sessões ainda não existe."
                "||Rode /init para criar ~/.nyx/sessions/."
            )
        files = sorted(SESSIONS_DIR.glob("session_*.json"), reverse=True)[:10]
        if not files:
            return (
                "__error__Nenhuma sessão salva encontrada."
                "||Saia do REPL com /quit para salvar a sessão atual."
            )
        lines = ["  Sessões recentes:"]
        for f in files:
            lines.append(f"    {f.name}")
        return "\n".join(lines)

    if action == "load" or action == "restore":
        session = load_latest_session()
        if session:
            return "__session_load__"
        return (
            "__error__Nenhuma sessão salva para restaurar."
            "||Saia do REPL com /quit para salvar a sessão atual."
        )

    if action == "save":
        return "__session_save__"

    return (
        "  Uso: /session <ação>\n"
        "    list    -- lista sessões salvas\n"
        "    save    -- salva sessão atual\n"
        "    load    -- restaura última sessão"
    )


@nyx_command(name="rewind", description="Desfaz últimas N ações do agent", category="sessão",
    examples=['/rewind 1', '/rewind 5'],
)
def cmd_rewind(args: str, _root: str) -> str:
    n = 1
    if args.strip().isdigit():
        n = int(args.strip())
    return f"__rewind__{n}"


@nyx_command(
    name="resume",
    description="Retoma sessão (sem arg = última, /resume list, /resume <prefixo>)",
    category="sessão",
    examples=["/resume", "/resume list", "/resume a3f2"],
)
def cmd_resume(args: str, _root: str) -> str:
    """SESSION-RESUME-01: três modos.

    Sentinelas:
      __session_load__              - última sessão (comportamento original)
      __session_load_id__<id>       - sessão por prefixo de id
      __session_index__             - imprime índice tabular
    """
    arg = args.strip()
    if not arg:
        return "__session_load__"
    if arg == "list":
        return "__session_index__"
    return f"__session_load_id__{arg}"


@nyx_command(
    name="replay",
    description="Re-renderiza sessão salva (read-only, sem chamar modelo)",
    category="sessão",
    examples=["/replay session_2026-05-17_123", "/replay last"],
)
def cmd_replay(args: str, _root: str) -> str:
    args = args.strip()
    if not args:
        return (
            "__error__Argumento obrigatório ausente em /replay."
            "||Uso: /replay <session_id> -- ex: session_Nyx-Code_1776736000"
        )
    return f"__replay__{args}"


@nyx_command(name="export", description="Exporta sessão para arquivo", category="sessão",
    examples=['/export md', '/export txt'],
)
def cmd_export(args: str, _root: str) -> str:
    return "__export__" + (args.strip() or "md")


@nyx_command(name="copy", description="Copia último output para clipboard", category="sessão",
    examples=['/copy', '/copy last'],
)
def cmd_copy(_args: str, _root: str) -> str:
    return "__copy__"


@nyx_command(name="summary", description="Gera resumo da sessão", category="sessão",
    examples=['/summary', '/summary detalhado'],
)
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


@nyx_command(name="stats", description="Estatísticas detalhadas da sessão", category="sessão",
    examples=['/stats', '/stats verbose'],
)
def cmd_stats(_args: str, _root: str) -> str:
    return "__stats__"


@nyx_command(name="usage", description="Uso de tokens e contexto", category="sessão",
    examples=['/usage', '/usage tokens'],
)
def cmd_usage(_args: str, _root: str) -> str:
    return "__usage__"


@nyx_command(name="files", description="Mostra arquivos no contexto", category="execução",
    examples=['/files', '/files diff'],
)
def cmd_files(_args: str, _root: str) -> str:
    return "__files__"


@nyx_command(name="trace", description="Trace de execução do agent loop", category="debug",
    examples=['/trace', '/trace 10'],
)
def cmd_trace(_args: str, _root: str) -> str:
    return "__trace__"


@nyx_command(name="btw", description="Nota lateral para o agent", category="avançado",
    examples=['/btw lembrar de revisar este teste', '/btw decisão sobre cache'],
)
def cmd_btw(args: str, _root: str) -> str:
    note = args.strip()
    if not note:
        return (
            "__error__Argumento obrigatório ausente em /btw."
            "||Uso: /btw <nota> -- injeta contexto sem gerar resposta."
        )
    return f"__btw__{note}"


# "Quem não grava a sessão, repete a sessão." -- lema do shell
