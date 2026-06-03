"""Despachador de sentinels de slash-command para a TUI Textual.

TUI-SENTINEL-DISPATCH-UNIFY-01: `handle_command()` devolve uma string
sentinel `__nome__[payload]` que o HOST interpreta. O REPL legado
(`nyx/cli_handlers.py`) tem um handler por sentinel; a migração Textual
(ONDA-32) portou só um subconjunto para `app.py:_dispatch_slash`, e os
demais caíam no fallback genérico `ChatMessage("tool", str(result))` --
o marcador cru vazava na tela (oposto do ADR-026: "o que vaza cru foi
nomeado errado").

Este módulo concentra o render dos sentinels de RENDER PURO e de
EFEITO-LEVE (mutam só `agent.session`/`agent._model` e devolvem texto),
espelhando byte-a-byte a semântica observável de `cli_handlers.py` mas
SEM `print()` (ADR-024: app.py renderiza via ChatMessage) e SEM códigos
ANSI (a TUI colore via CSS/Rich, não escape sequences).

Contrato:
  - `render_sync(result, agent, project_root)` devolve `(role, texto)`
    quando reconhece o sentinel síncrono, ou `None` caso contrário.
  - `render_mcp_async(result)` devolve `(role, texto)` para os 3
    sentinels MCP (que exigem await de rede), ou `None`.
  - `role` é sempre um de ChatMessage._VALID_ROLES ("tool"/"system").
    "tool" para listagens/inspeção; "system" para confirmações de estado.

Sentinels com efeito de estado que exigem APIs próprias da TUI
(`__cd__`, `__sandbox_*__`, `__error__`, `__quit__`, os `_select__`,
`__cancel_inflight__`) permanecem tratados no `app.py:_dispatch_slash`
-- NÃO são responsabilidade deste módulo (retornam None aqui).
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nyx.agent.loop import AgentLoop


def _split_error_sentinel(texto: str) -> str:
    """Converte um `__error__<msg>||<hint>` embutido em texto legível.

    Helpers como `render_replay` devolvem o protocolo de erro padrão
    (`__error__msg||hint`) em vez de texto puro quando falham. O REPL
    imprimia isso cru; na TUI normalizamos para `msg` + `hint` (nova
    linha), evitando que o marcador `__error__` vaze. Texto sem o
    prefixo passa intacto.
    """
    if not texto.startswith("__error__"):
        return texto
    payload = texto[len("__error__"):]
    if "||" in payload:
        msg, hint = payload.split("||", 1)
        return f"{msg}\n{hint}"
    return payload


def _render_status(agent: "AgentLoop") -> str:
    s = agent.session
    stats = agent.parser_stats
    info = agent.get_context_info()
    return (
        f"[sessão] Iterações: {s.iteration} | "
        f"Lidos: {s.files_read_count} | "
        f"Modificados: {s.files_modified_count} | "
        f"Parser: {stats['success_rate']:.0%} | "
        f"Tools: {agent.tools_count} | "
        f"Contexto: {info.get('pct', 0):.0%}"
    )


def _render_stats(agent: "AgentLoop") -> str:
    s = agent.session
    stats = agent.parser_stats
    return (
        f"Iterações: {s.iteration}\n"
        f"Arquivos lidos: {s.files_read_count}\n"
        f"Arquivos modificados: {s.files_modified_count}\n"
        f"Entradas no histórico: {len(s.history)}\n"
        f"Parser taxa sucesso: {stats['success_rate']:.0%}\n"
        f"Tools: {agent.tools_count}"
    )


def _render_usage(agent: "AgentLoop") -> str:
    info = agent.get_context_info()
    return (
        f"Contexto: {info.get('pct', 0):.0%} usado\n"
        f"Tokens sistema: {info.get('system_tokens', 0)}\n"
        f"Tokens usuário: {info.get('user_tokens', 0)}\n"
        f"Total: {info.get('total_tokens', 0)}/{info.get('max_tokens', 0)}"
    )


def _render_context(agent: "AgentLoop") -> str:
    from nyx.agent.context import render_context_bar

    info = agent.get_context_info()
    bar = render_context_bar(info)
    return (
        f"{bar}\n"
        f"System: {info.get('system_tokens', 0)} tok | "
        f"User: {info.get('user_tokens', 0)} tok | "
        f"Total: {info.get('total_tokens', 0)}/{info.get('max_tokens', 0)} tok"
    )


def _render_files(agent: "AgentLoop") -> str:
    ctx_text = agent.session.get_files_context()
    if ctx_text:
        return ctx_text
    return (
        "Nenhum arquivo no contexto da sessão.\n"
        "Peça à Nyx para ler um arquivo ou use /read <caminho>."
    )


def _render_trace(agent: "AgentLoop") -> str:
    entries = [e for e in agent.session.history if e.tool_name]
    if not entries:
        return (
            "Nenhuma tool call registrada nesta sessão.\n"
            "Faça uma pergunta à Nyx para gerar atividade antes de /trace."
        )
    linhas = ["Últimas tool calls:"]
    for e in entries[-10:]:
        args_short = str(e.tool_args)[:50]
        linhas.append(f"  {e.tool_name}({args_short})")
    return "\n".join(linhas)


def _render_aesthetic_list(agent: "AgentLoop") -> str:
    import os

    from nyx.themes.design_tokens_extended import list_aesthetics, list_entities

    cur = os.environ.get("NYX_AESTHETIC", "default")
    cur_ent = os.environ.get("NYX_ENTITY", "nyx")
    linhas = [f"Estéticos disponíveis (atual: {cur}):"]
    for a in list_aesthetics():
        marker = "* " if a["id"] == cur else "  "
        linhas.append(f"  {marker}{a['id']:<10} -- {a['tagline']}")
    linhas.append(f"Entidades disponíveis (atual: {cur_ent}):")
    for e in list_entities():
        marker = "* " if e["id"] == cur_ent else "  "
        linhas.append(f"  {marker}{e['id']:<6} {e['name']:<6} accent {e['accent']}")
    return "\n".join(linhas)


def _render_aesthetic_get() -> str:
    import os

    cur = os.environ.get("NYX_AESTHETIC", "default")
    cur_ent = os.environ.get("NYX_ENTITY", "nyx")
    return f"Estético atual: {cur} | Entidade: {cur_ent}"


def _render_aesthetic_set(result: str) -> str:
    import os

    from nyx.themes.design_tokens_extended import AESTHETICS, ENTITIES

    target = result[len("__aesthetic_set__"):].strip()
    if ":" in target:
        a_id, e_id = (p.strip() for p in target.split(":", 1))
    else:
        a_id, e_id = target.strip(), None
    if a_id and a_id not in AESTHETICS:
        return f"Estético '{a_id}' não existe.\nUse /aesthetic list para ver opções."
    if e_id and e_id not in ENTITIES:
        return f"Entidade '{e_id}' não existe.\nUse /aesthetic list para ver opções."
    if a_id:
        os.environ["NYX_AESTHETIC"] = a_id
    if e_id:
        os.environ["NYX_ENTITY"] = e_id
    final_a = os.environ.get("NYX_AESTHETIC", "default")
    final_e = os.environ.get("NYX_ENTITY", "nyx")
    return f"aesthetic: {final_a}:{final_e} (próxima invocação aplica)"


def _render_schema_list() -> str:
    import os

    from nyx.themes.design_tokens_extended import DEFAULT_SCHEMA, list_schemas

    cur = os.environ.get("NYX_SCHEMA", DEFAULT_SCHEMA)
    linhas = [f"Schemas disponíveis (atual: {cur}):"]
    for s in list_schemas():
        marker = "* " if s["id"] == cur else "  "
        linhas.append(
            f"  {marker}{s['id']:<10} -- case {s['heading_case']} "
            f"user {s['user_bubble']} nyx {s['nyx_bubble']}"
        )
    return "\n".join(linhas)


def _render_schema_get() -> str:
    import os

    from nyx.themes.design_tokens_extended import DEFAULT_SCHEMA

    return f"Schema atual: {os.environ.get('NYX_SCHEMA', DEFAULT_SCHEMA)}"


def _render_schema_set(result: str) -> str:
    import os

    from nyx.themes.design_tokens_extended import INTERFACE_SCHEMAS

    target = result[len("__schema_set__"):].strip()
    if target not in INTERFACE_SCHEMAS:
        return f"Schema '{target}' não existe.\nUse /schema list para ver opções."
    os.environ["NYX_SCHEMA"] = target
    return f"schema: {target} (próxima invocação aplica)"


def _render_output_style_list() -> str:
    from nyx.agent.output_style import list_styles

    linhas = ["Estilos de saída:"]
    for st in list_styles():
        linhas.append(f"  {st.name:<10} -- {st.description}")
    return "\n".join(linhas)


def _render_output_style_get() -> str:
    return "Estilo atual: default"


def _render_output_style_set(result: str) -> str:
    from nyx.agent.output_style import STYLES

    target = result[len("__output_style_set__"):].strip()
    if target not in STYLES:
        return f"Estilo '{target}' não existe.\nUse /output-style list para ver opções."
    return f"estilo trocado para {target} (próxima request usa)"


def _render_plugin_list() -> str:
    from nyx.agent.services.plugin_manager import PluginManager

    plugins = PluginManager().list()
    if not plugins:
        return (
            "Nenhum plugin em ~/.nyx/plugins/.\n"
            "Use /plugin install <path> para instalar um."
        )
    linhas = [f"Plugins ({len(plugins)}):"]
    for p in plugins:
        status = f"({p.error})" if p.error else "OK"
        linhas.append(
            f"  {p.name} v{p.version} [{status}] "
            f"-- tools={len(p.tools)} cmds={len(p.commands)}"
        )
        if p.description:
            linhas.append(f"    {p.description}")
    return "\n".join(linhas)


def _render_plugin_reload() -> str:
    from nyx.agent.services.plugin_manager import PluginManager

    results = PluginManager().reload()
    ok = sum(1 for v in results.values() if v)
    return f"plugins recarregados: {ok}/{len(results)} OK"


def _render_plugin_install(result: str) -> str:
    from nyx.agent.services.plugin_manager import PluginManager

    src = result[len("__plugin_install__"):].strip()
    name = PluginManager().install(src)
    if name:
        return f"plugin '{name}' instalado"
    return (
        f"Falha ao instalar plugin a partir de {src!r}.\n"
        "Confirme que o diretório existe e contém manifest.toml válido."
    )


def _render_plugin_uninstall(result: str) -> str:
    from nyx.agent.services.plugin_manager import PluginManager

    name = result[len("__plugin_uninstall__"):].strip()
    pm = PluginManager()
    pm.discover()
    if pm.uninstall(name):
        return f"plugin '{name}' removido"
    return f"Plugin '{name}' não encontrado.\nUse /plugin list para ver instalados."


def _render_session_save(agent: "AgentLoop", project_root: str) -> str:
    from nyx.agent.persistence import save_session

    saved = save_session(agent.session, Path(project_root).name)
    if saved:
        return f"sessão salva: {saved.name}"
    return (
        "Falha ao salvar a sessão atual.\n"
        "Verifique permissões de escrita em ~/.nyx/sessions/."
    )


def _render_session_load(agent: "AgentLoop", project_root: str) -> str:
    from nyx.agent.persistence import load_latest_session
    from nyx.agent.services.gsd_writer import load_progress_tail

    loaded = load_latest_session(Path(project_root).name)
    if not loaded:
        return (
            "Nenhuma sessão salva para restaurar.\n"
            "Use /quit para salvar esta sessão e rode novamente para carregá-la."
        )
    agent._session = loaded
    sid = getattr(agent, "_session_id", "") or ""
    extra = load_progress_tail(sid, n=50) if sid else ""
    if extra:
        loaded.add_user(f"[contexto-anterior]\n{extra}")
    return f"sessão restaurada ({len(loaded.history)} entradas)"


def _render_session_load_id(agent: "AgentLoop", result: str) -> str:
    from nyx.agent.persistence import load_session_by_id
    from nyx.agent.services.gsd_writer import load_progress_tail

    prefix = result[len("__session_load_id__"):]
    loaded = load_session_by_id(prefix)
    if not loaded:
        return (
            f"Nenhuma sessão única casa com '{prefix}'.\n"
            "Use /resume list para ver todas, depois /resume <prefixo único>."
        )
    agent._session = loaded
    extra = load_progress_tail(prefix, n=50)
    if extra:
        loaded.add_user(f"[contexto-anterior]\n{extra}")
    return f"Sessão {prefix} restaurada ({len(loaded.history)} entradas)"


def _render_session_index() -> str:
    from nyx.agent.persistence import load_index

    idx = load_index()
    if not idx:
        return (
            "Nenhuma sessão indexada.\n"
            "Saia com /quit para gerar a primeira entrada do índice."
        )
    linhas = [f"{len(idx)} sessões no índice (mais recentes embaixo):"]
    for entry in idx[-20:]:
        sid = entry.get("id", "?")
        prompt_preview = entry.get("primeiro_prompt", "")[:60]
        n = entry.get("n_turnos", 0)
        linhas.append(f"  {sid[:32]:<32}  {n:>2} turnos  {prompt_preview}")
    return "\n".join(linhas)


def _render_model(agent: "AgentLoop", result: str) -> str:
    new_model = result.replace("__model__", "")
    agent._model = new_model
    return f"Modelo trocado para: {new_model}"


def _render_rewind(agent: "AgentLoop", result: str) -> str:
    n = int(result.replace("__rewind__", "") or "1")
    removed = min(n, len(agent.session.history))
    for _ in range(removed):
        if agent.session.history:
            agent.session.history.pop()
    return f"Desfeitas {removed} entradas do histórico."


def _render_clear(agent: "AgentLoop") -> str:
    agent.reset()
    return "sessão limpa"


def _render_btw(agent: "AgentLoop", result: str) -> str:
    note = result[len("__btw__"):]
    agent.session.add_user(f"[nota lateral] {note}")
    return f"Nota registrada: {note[:60]}"


def _render_edit_last(agent: "AgentLoop") -> str:
    # No REPL o /edit prefilla o próximo prompt (input() reusável). Na TUI o
    # InputWidget não é reusado por este canal; reportamos o último input de
    # forma legível para o usuário re-enviar.
    last = ""
    for entry in reversed(agent.session.history):
        if entry.role == "user":
            last = entry.content or ""
            break
    if not last:
        return (
            "Nenhum input anterior para editar.\n"
            "Envie uma mensagem antes de usar /edit."
        )
    return f"Último input (copie, edite e reenvie):\n{last}"


def _render_export(agent: "AgentLoop", result: str) -> str:
    fmt = result.replace("__export__", "") or "md"
    export_dir = Path.home() / ".nyx" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    export_path = export_dir / f"session_{ts}.{fmt}"
    linhas = []
    for entry in agent.session.history:
        if entry.tool_name:
            linhas.append(f"[{entry.tool_name}] {str(entry.tool_args)[:80]}")
        else:
            linhas.append(f"[{entry.role}] {entry.content[:200]}")
    export_path.write_text("\n".join(linhas), encoding="utf-8")
    return f"Sessão exportada: {export_path}"


def _render_copy(agent: "AgentLoop") -> str:
    import subprocess as _sp

    last_content = ""
    for entry in reversed(agent.session.history):
        if entry.role == "assistant" or entry.tool_result:
            last_content = entry.content or entry.tool_result
            break
    if not last_content:
        return (
            "Nenhum output disponível para copiar.\n"
            "Aguarde uma resposta da Nyx ou execute um comando antes de /copy."
        )
    try:
        _sp.run(
            ["xclip", "-selection", "clipboard"],
            input=last_content.encode(),
            timeout=5,
        )
        return f"Copiado para clipboard ({len(last_content)} chars)"
    except FileNotFoundError:
        tmp = Path.home() / ".nyx" / "clipboard.txt"
        tmp.write_text(last_content, encoding="utf-8")
        return (
            f"xclip indisponível no sistema.\n"
            f"Conteúdo salvo em {tmp}. Instale com: sudo apt install xclip"
        )


def _render_debug_session(agent: "AgentLoop") -> str:
    from nyx.agent.commands._observability import render_debug_session

    return render_debug_session(agent)


def _render_replay(agent: "AgentLoop", result: str) -> str:
    from nyx.agent.commands._observability import render_replay

    return render_replay(
        Path(agent._project_root), result.replace("__replay__", "")
    )


def _render_progress_tail(agent: "AgentLoop", result: str) -> str:
    from nyx.agent.services.gsd_writer import load_progress_tail

    try:
        n = int(result.replace("__progress_tail__", "") or "30")
    except ValueError:
        n = 30
    sid = getattr(agent, "_session_id", "") or ""
    tail = load_progress_tail(sid, n=n) if sid else ""
    if tail:
        return tail
    return (
        "Nenhum progresso registrado ainda.\n"
        "O progress.md é criado no primeiro turno; faça uma pergunta primeiro."
    )


def render_sync(
    result: str, agent: "AgentLoop", project_root: str
) -> tuple[str, str] | None:
    """Renderiza um sentinel síncrono para a TUI.

    Devolve `(role, texto)` se reconhece, `None` caso contrário. `role` é
    "tool" (listagens/inspeção, com prefixo indentado no widget) ou
    "system" (confirmações de estado, sem prefixo).

    Sentinels com efeito de estado próprio da TUI (cd/sandbox/error/quit/
    selects/cancel) NÃO são tratados aqui -- ficam no app.py. Sem agent,
    nada é renderizado (a TUI só dispara slash com agent montado).
    """
    if agent is None:
        return None

    # Sentinels exatos de render puro (role "tool").
    exact_tool = {
        "__status__": lambda: _render_status(agent),
        "__stats__": lambda: _render_stats(agent),
        "__usage__": lambda: _render_usage(agent),
        "__context__": lambda: _render_context(agent),
        "__files__": lambda: _render_files(agent),
        "__trace__": lambda: _render_trace(agent),
        "__aesthetic_list__": lambda: _render_aesthetic_list(agent),
        "__aesthetic_get__": _render_aesthetic_get,
        "__schema_list__": _render_schema_list,
        "__schema_get__": _render_schema_get,
        "__output_style_list__": _render_output_style_list,
        "__output_style_get__": _render_output_style_get,
        "__plugin_list__": _render_plugin_list,
        "__plugin_reload__": _render_plugin_reload,
        "__session_index__": _render_session_index,
        "__debug_session__": lambda: _render_debug_session(agent),
    }
    if result in exact_tool:
        return ("tool", _split_error_sentinel(exact_tool[result]()))

    # Sentinels exatos de efeito-leve/confirmação (role "system").
    exact_system = {
        "__clear__": lambda: _render_clear(agent),
        "__copy__": lambda: _render_copy(agent),
        "__edit_last__": lambda: _render_edit_last(agent),
        "__session_save__": lambda: _render_session_save(agent, project_root),
        "__session_load__": lambda: _render_session_load(agent, project_root),
    }
    if result in exact_system:
        return ("system", _split_error_sentinel(exact_system[result]()))

    # Sentinels com payload (prefix-match). Render puro -> "tool";
    # efeito/confirmação -> "system".
    prefix_tool = {
        "__replay__": lambda: _render_replay(agent, result),
        "__progress_tail__": lambda: _render_progress_tail(agent, result),
    }
    for pref, fn in prefix_tool.items():
        if result.startswith(pref):
            return ("tool", _split_error_sentinel(fn()))

    prefix_system = {
        "__aesthetic_set__": lambda: _render_aesthetic_set(result),
        "__schema_set__": lambda: _render_schema_set(result),
        "__output_style_set__": lambda: _render_output_style_set(result),
        "__plugin_install__": lambda: _render_plugin_install(result),
        "__plugin_uninstall__": lambda: _render_plugin_uninstall(result),
        "__session_load_id__": lambda: _render_session_load_id(agent, result),
        "__model__": lambda: _render_model(agent, result),
        "__rewind__": lambda: _render_rewind(agent, result),
        "__btw__": lambda: _render_btw(agent, result),
        "__export__": lambda: _render_export(agent, result),
    }
    for pref, fn in prefix_system.items():
        if result.startswith(pref):
            return ("system", _split_error_sentinel(fn()))

    return None


async def render_mcp_async(result: str) -> tuple[str, str] | None:
    """Renderiza os sentinels MCP (exigem await de rede).

    Devolve `(role, texto)` para `__mcp_list__`/`__mcp_reload__`/
    `__mcp_test__`, ou `None` se não for sentinel MCP. Espelha
    `cli_handlers._handle_mcp_*` sem ANSI nem print.
    """
    from nyx.agent.services.mcp_client import McpClient

    if result == "__mcp_list__":
        client = McpClient.from_config()
        if not client.servers:
            return (
                "system",
                "Nenhum server MCP configurado.\n"
                'Crie ~/.nyx/mcp.json com {"servers": {...}}.',
            )
        await client.connect_all()
        linhas = [f"Servers MCP ({len(client.servers)}):"]
        for name, srv in client.servers.items():
            status = "OK" if srv.connected else (srv.error or "down")
            linhas.append(f"  {name} [{status}] -- {len(srv.tools)} tool(s)")
            for tool in srv.tools[:5]:
                tname = tool.get("name", "?")
                tdesc = (tool.get("description") or "").strip()[:60]
                linhas.append(f"    - {tname}: {tdesc}")
            if len(srv.tools) > 5:
                linhas.append(f"    ... (+{len(srv.tools) - 5} tools)")
        await client.close_all()
        return ("tool", "\n".join(linhas))

    if result == "__mcp_reload__":
        client = McpClient.from_config()
        if not client.servers:
            return ("system", "Nenhum server MCP em ~/.nyx/mcp.json.")
        results = await client.connect_all()
        ok = sum(1 for v in results.values() if v)
        await client.close_all()
        return (
            "system",
            f"MCP recarregado: {ok}/{len(results)} server(s) conectado(s)",
        )

    if result.startswith("__mcp_test__"):
        target = result[len("__mcp_test__"):].strip()
        client = McpClient.from_config()
        if target not in client.servers:
            return ("system", f"Server MCP '{target}' não encontrado.\nVeja /mcp list.")
        await client.connect_all()
        alive = await client.ping(target)
        await client.close_all()
        if alive:
            return ("system", f"MCP {target} responde (ping ok)")
        return (
            "system",
            f"MCP {target} não responde ao ping.\n"
            "Verifique o command/args em ~/.nyx/mcp.json.",
        )

    return None


def command_label(result: str) -> str:
    """Extrai um rótulo legível do sentinel para o fail-safe.

    `__output_style_list__` -> `output-style`; `__btw__oi` -> `btw`.
    Usado quando nenhum render reconhece o sentinel: a TUI informa
    "[comando não disponível nesta interface: <label>]" em vez de
    vazar o marcador cru.
    """
    core = result.strip("_")
    # corta payload colado (primeiro caractere não-identificador encerra o nome)
    nome = []
    for ch in core:
        if ch.isalnum() or ch == "_":
            nome.append(ch)
        else:
            break
    label = "".join(nome).replace("_", "-")
    return label or "?"


# "O que foi nomeado, aconteceu; o que vaza cru foi nomeado errado." -- ADR-026
