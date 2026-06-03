"""Handlers de sentinelas de slash commands extraídos de nyx/cli.py.

INFRA-CLI-SPLIT-02: cada bloco `if result == "__X__"` do REPL vira
um handler aqui (síncrono ou async). Mantém a mesma semântica observável
do REPL — texto impresso é idêntico, byte a byte, salvo onde a paleta
ANSI exige passagem do ref atual (DIM/ACCENT/etc são parâmetros).

Convenção:
  - Cada handler recebe `ctx: HandlerCtx` com refs ao agente + app_state.
  - Retorna True quando o sentinel é tratado (REPL faz `continue`),
    False quando não casa (REPL prossegue para o próximo bloco).
  - Handlers que retornam novo `project_root` mutam `ctx.agent` e
    sinalizam via `ctx.app_state` (não há retorno extra).

`__quit__` permanece em cli.py porque encadeia shutdown (proxy admin
endpoint, save_session, gather de tasks pendentes).
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from nyx.agent.loop import AgentLoop


@dataclass
class HandlerCtx:
    """Contexto compartilhado entre handlers de sentinela.

    Refs mutáveis (agent, app_state, last_input_state) permitem
    handlers atualizarem estado sem precisarem retornar valores.

    Cores ANSI são strings prontas (ACCENT, DIM, etc.) — handlers
    não importam design_tokens diretamente.
    """

    result: str
    agent: "AgentLoop"
    app_state: dict[str, Any]
    project_root_path: Path
    last_input_state: dict[str, str]
    use_rich: bool
    output: Any
    print_error: Any
    accent: str
    primary: str
    dim: str
    success: str
    nc: str


def _handle_clear(ctx: HandlerCtx) -> bool:
    if ctx.result != "__clear__":
        return False
    ctx.agent.reset()
    if ctx.use_rich and ctx.output:
        ctx.output("ok", " sessão limpa")
    else:
        print(f"  {ctx.success} sessão limpa{ctx.nc}")
    return True


def _handle_status(ctx: HandlerCtx) -> bool:
    if ctx.result != "__status__":
        return False
    s = ctx.agent.session
    stats = ctx.agent.parser_stats
    info = ctx.agent.get_context_info()
    status_msg = (
        f"Iterações: {s.iteration} | "
        f"Lidos: {s.files_read_count} | "
        f"Modificados: {s.files_modified_count} | "
        f"Parser: {stats['success_rate']:.0%} | "
        f"Tools: {ctx.agent.tools_count} | "
        f"Contexto: {info.get('pct', 0):.0%}"
    )
    if ctx.use_rich and ctx.output:
        ctx.output("sessão", status_msg)
    else:
        print(f"  {ctx.accent}[sessão]{ctx.nc} {status_msg}")
    return True


def _handle_context(ctx: HandlerCtx) -> bool:
    if ctx.result != "__context__":
        return False
    from nyx.agent.context import render_context_bar

    info = ctx.agent.get_context_info()
    bar = render_context_bar(info)
    ctx_msg = (
        f"{bar}\n"
        f"  System: {info.get('system_tokens', 0)} tok | "
        f"User: {info.get('user_tokens', 0)} tok | "
        f"Total: {info.get('total_tokens', 0)}/{info.get('max_tokens', 0)} tok"
    )
    print(f"  {ctx_msg}")
    return True


def _handle_session_save(ctx: HandlerCtx) -> bool:
    if ctx.result != "__session_save__":
        return False
    from nyx.agent.persistence import save_session

    saved = save_session(ctx.agent.session, ctx.project_root_path.name)
    if saved:
        print(f"  {ctx.success} sessão salva{ctx.nc}: {saved.name}")
    else:
        ctx.print_error(
            "Falha ao salvar a sessão atual.",
            hint="Verifique permissões de escrita em ~/.nyx/sessions/.",
        )
    return True


def _handle_session_load(ctx: HandlerCtx) -> bool:
    if ctx.result != "__session_load__":
        return False
    from nyx.agent.persistence import load_latest_session
    from nyx.agent.services.gsd_writer import load_progress_tail

    loaded = load_latest_session(ctx.project_root_path.name)
    if loaded:
        ctx.agent._session = loaded
        sid = getattr(ctx.agent, "_session_id", "") or ""
        extra = load_progress_tail(sid, n=50) if sid else ""
        if extra:
            loaded.add_user(f"[contexto-anterior]\n{extra}")
        print(f"  {ctx.success} sessão restaurada{ctx.nc} ({len(loaded.history)} entradas)")
    else:
        ctx.print_error(
            "Nenhuma sessão salva para restaurar.",
            hint="Use /quit para salvar esta sessão e rode novamente para carregá-la.",
        )
    return True


def _handle_session_load_id(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__session_load_id__")):
        return False
    prefix = ctx.result[len("__session_load_id__"):]
    from nyx.agent.persistence import load_session_by_id
    from nyx.agent.services.gsd_writer import load_progress_tail

    loaded = load_session_by_id(prefix)
    if loaded:
        ctx.agent._session = loaded
        extra = load_progress_tail(prefix, n=50)
        if extra:
            loaded.add_user(f"[contexto-anterior]\n{extra}")
        print(
            f"  {ctx.accent}[ok]{ctx.nc} Sessão {prefix} restaurada "
            f"({len(loaded.history)} entradas)"
        )
    else:
        ctx.print_error(
            f"Nenhuma sessão única casa com '{prefix}'.",
            hint="Use /resume list para ver todas, depois /resume <prefixo único>.",
        )
    return True


def _handle_sandbox_list(ctx: HandlerCtx) -> bool:
    if ctx.result != "__sandbox_list__":
        return False
    from nyx.agent.tools.base import (
        get_active_project_root,
        list_extra_roots,
    )

    active = get_active_project_root() or ctx.project_root_path
    extras = list_extra_roots()
    lines = ["  Roots autorizados:"]
    lines.append(f"    [ativo] {active}")
    if extras:
        for r in extras:
            lines.append(f"    [extra] {r}")
    else:
        lines.append(
            "    (nenhum extra; use /sandbox add <path> para autorizar)"
        )
    print("\n".join(lines))
    return True


def _handle_sandbox_add(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__sandbox_add__")):
        return False
    from nyx.agent.tools.base import add_extra_root

    raw_path = ctx.result[len("__sandbox_add__"):]
    cand = Path(raw_path).expanduser()
    if not cand.exists():
        ctx.print_error(
            f"Caminho '{raw_path}' não existe.",
            hint="Confira com: ls -la ou tab-completion.",
        )
        return True
    if not cand.is_dir():
        ctx.print_error(
            f"Caminho '{raw_path}' não é diretório.",
            hint="Use /sandbox add <diretório>, não arquivo.",
        )
        return True
    added = add_extra_root(cand)
    print(f"  {ctx.success} root autorizado{ctx.nc}: {added}")
    return True


def _handle_sandbox_remove(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__sandbox_remove__")):
        return False
    from nyx.agent.tools.base import (
        get_active_project_root,
        remove_extra_root,
    )

    raw_path = ctx.result[len("__sandbox_remove__"):]
    cand = Path(raw_path).expanduser().resolve()
    active = get_active_project_root() or ctx.project_root_path
    if cand == Path(active).resolve():
        ctx.print_error(
            f"O project_root ativo ({active}) não pode ser removido.",
            hint="Use /cd <outro> antes para trocar de root ativo.",
        )
        return True
    if remove_extra_root(cand):
        print(f"  {ctx.success} root removido{ctx.nc}: {cand}")
    else:
        ctx.print_error(
            f"Root '{cand}' não estava na lista de extras.",
            hint="Liste os ativos com /sandbox list.",
        )
    return True


def _handle_cd(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__cd__")):
        return False
    from nyx.agent.tools.base import (
        add_extra_root,
        get_active_project_root,
        set_active_project_root,
    )

    raw_path = ctx.result[len("__cd__"):]
    cand = Path(raw_path).expanduser()
    if not cand.exists() or not cand.is_dir():
        ctx.print_error(
            f"Caminho '{raw_path}' inválido para /cd.",
            hint="Diretório precisa existir; confira com ls.",
        )
        return True
    old_root = get_active_project_root() or ctx.project_root_path
    # Troca o active ANTES de adicionar o antigo como extra,
    # senão o guard de add_extra_root (que rejeita == active)
    # impede a preservação.
    new_root = set_active_project_root(cand)
    add_extra_root(old_root)
    # Reconfigura agent + ToolRegistry para usar novo root nas tools (cwd em
    # run_command, validate_path em file ops) E reconstrói o system prompt --
    # sem isso o bloco "Diretório:" mantém o root antigo e o modelo escreve no
    # diretório anterior (TUI-CD-CONTEXT-REBUILD-01).
    project_root_str = str(new_root)
    ctx.agent.set_project_root(project_root_str)
    ctx.app_state["__cd_new_root__"] = project_root_str
    print(
        f"  {ctx.success} project_root trocado para{ctx.nc} {new_root}\n"
        f"  {ctx.dim}(root anterior {old_root} preservado como extra){ctx.nc}"
    )
    return True


def _handle_cancel_inflight(ctx: HandlerCtx) -> bool:
    if ctx.result != "__cancel_inflight__":
        return False
    inflight = ctx.app_state.get("inflight_task")
    if inflight is not None and not inflight.done():
        inflight.cancel()
        print(f"  {ctx.success} cancel sinalizado{ctx.nc} (asyncio.CancelledError despachado)")
    else:
        print(
            f"  {ctx.dim}/cancel: nenhuma tool em curso. "
            f"Use Ctrl+C durante execução para interromper.{ctx.nc}"
        )
    return True


def _handle_aesthetic_list(ctx: HandlerCtx) -> bool:
    if ctx.result != "__aesthetic_list__":
        return False
    from nyx.themes.design_tokens_extended import list_aesthetics, list_entities

    cur = ctx.app_state.get(
        "aesthetic_id",
        os.environ.get("NYX_AESTHETIC", "default"),
    )
    cur_ent = ctx.app_state.get(
        "entity_id",
        os.environ.get("NYX_ENTITY", "nyx"),
    )
    print(f"  Estéticos disponíveis (atual: {ctx.accent}{cur}{ctx.nc}):")
    for a in list_aesthetics():
        marker = f"{ctx.accent}* {ctx.nc}" if a["id"] == cur else "  "
        print(f"    {marker}{ctx.accent}{a['id']:<10}{ctx.nc} -- {a['tagline']}")
    print(f"  Entidades disponíveis (atual: {ctx.success}{cur_ent}{ctx.nc}):")
    for e in list_entities():
        marker = f"{ctx.success}* {ctx.nc}" if e["id"] == cur_ent else "  "
        print(f"    {marker}{ctx.success}{e['id']:<6}{ctx.nc} {e['name']:<6} accent {e['accent']}")
    return True


def _handle_aesthetic_get(ctx: HandlerCtx) -> bool:
    if ctx.result != "__aesthetic_get__":
        return False
    cur = ctx.app_state.get(
        "aesthetic_id",
        os.environ.get("NYX_AESTHETIC", "default"),
    )
    cur_ent = ctx.app_state.get(
        "entity_id",
        os.environ.get("NYX_ENTITY", "nyx"),
    )
    print(f"  Estético atual: {ctx.accent}{cur}{ctx.nc} | Entidade: {ctx.success}{cur_ent}{ctx.nc}")
    return True


def _handle_aesthetic_set(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__aesthetic_set__")):
        return False
    from nyx.themes.design_tokens_extended import AESTHETICS, ENTITIES

    target = ctx.result[len("__aesthetic_set__"):].strip()
    # Aceita 'aesthetic' ou 'aesthetic:entity'
    if ":" in target:
        a_id, e_id = target.split(":", 1)
        a_id, e_id = a_id.strip(), e_id.strip()
    else:
        a_id, e_id = target.strip(), None
    if a_id and a_id not in AESTHETICS:
        ctx.print_error(
            f"Estético '{a_id}' não existe.",
            hint="Use /aesthetic list para ver opções.",
        )
        return True
    if e_id and e_id not in ENTITIES:
        ctx.print_error(
            f"Entidade '{e_id}' não existe.",
            hint="Use /aesthetic list para ver opções.",
        )
        return True
    if a_id:
        ctx.app_state["aesthetic_id"] = a_id
        os.environ["NYX_AESTHETIC"] = a_id
    if e_id:
        ctx.app_state["entity_id"] = e_id
        os.environ["NYX_ENTITY"] = e_id
    final_a = ctx.app_state.get("aesthetic_id", "default")
    final_e = ctx.app_state.get("entity_id", "nyx")
    print(f"  {ctx.success} aesthetic{ctx.nc}: {final_a}:{final_e} (próxima invocação aplica)")
    return True


def _handle_schema_list(ctx: HandlerCtx) -> bool:
    if ctx.result != "__schema_list__":
        return False
    from nyx.themes.design_tokens_extended import (
        DEFAULT_SCHEMA,
        list_schemas,
    )

    cur = ctx.app_state.get(
        "schema_id",
        os.environ.get("NYX_SCHEMA", DEFAULT_SCHEMA),
    )
    print(f"  Schemas disponíveis (atual: {ctx.accent}{cur}{ctx.nc}):")
    for s in list_schemas():
        marker = f"{ctx.accent}* {ctx.nc}" if s["id"] == cur else "  "
        print(
            f"    {marker}{ctx.accent}{s['id']:<10}{ctx.nc} -- "
            f"case {s['heading_case']} · user {s['user_bubble']} · nyx {s['nyx_bubble']}"
        )
    return True


def _handle_schema_get(ctx: HandlerCtx) -> bool:
    if ctx.result != "__schema_get__":
        return False
    from nyx.themes.design_tokens_extended import DEFAULT_SCHEMA

    cur = ctx.app_state.get(
        "schema_id",
        os.environ.get("NYX_SCHEMA", DEFAULT_SCHEMA),
    )
    print(f"  Schema atual: {ctx.accent}{cur}{ctx.nc}")
    return True


def _handle_schema_set(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__schema_set__")):
        return False
    from nyx.themes.design_tokens_extended import INTERFACE_SCHEMAS

    target = ctx.result[len("__schema_set__"):].strip()
    if target not in INTERFACE_SCHEMAS:
        ctx.print_error(
            f"Schema '{target}' não existe.",
            hint="Use /schema list para ver opções.",
        )
        return True
    ctx.app_state["schema_id"] = target
    os.environ["NYX_SCHEMA"] = target
    print(
        f"  {ctx.success} schema{ctx.nc}: {target} (próxima invocação aplica)"
    )
    return True


def _handle_output_style_list(ctx: HandlerCtx) -> bool:
    if ctx.result != "__output_style_list__":
        return False
    from nyx.agent.output_style import list_styles

    current = str(ctx.app_state.get("output_style", "default"))
    print("  Estilos de saída:")
    for st in list_styles():
        marker = f"{ctx.accent}* {ctx.nc}" if st.name == current else "  "
        print(f"    {marker}{ctx.accent}{st.name:<10}{ctx.nc} -- {st.description}")
    return True


def _handle_output_style_get(ctx: HandlerCtx) -> bool:
    if ctx.result != "__output_style_get__":
        return False
    current = str(ctx.app_state.get("output_style", "default"))
    print(f"  Estilo atual: {ctx.accent}{current}{ctx.nc}")
    return True


def _handle_output_style_set(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__output_style_set__")):
        return False
    from nyx.agent.output_style import STYLES

    target = ctx.result[len("__output_style_set__"):].strip()
    if target not in STYLES:
        ctx.print_error(
            f"Estilo '{target}' não existe.",
            hint="Use /output-style list para ver opções.",
        )
        return True
    ctx.app_state["output_style"] = target
    print(f"  {ctx.accent}[ok]{ctx.nc} estilo trocado para {target} (próxima request usa)")
    return True


def _handle_plugin_list(ctx: HandlerCtx) -> bool:
    if ctx.result != "__plugin_list__":
        return False
    from nyx.agent.services.plugin_manager import PluginManager

    pm = PluginManager()
    plugins = pm.list()
    if not plugins:
        ctx.print_error(
            "Nenhum plugin em ~/.nyx/plugins/.",
            hint="Use /plugin install <path> para instalar um.",
        )
        return True
    print(f"  Plugins ({len(plugins)}):")
    for p in plugins:
        status = f"{ctx.dim}({p.error}){ctx.nc}" if p.error else f"{ctx.accent}OK{ctx.nc}"
        print(
            f"    {ctx.accent}{p.name}{ctx.nc} v{p.version} [{status}] "
            f"-- tools={len(p.tools)} cmds={len(p.commands)}"
        )
        if p.description:
            print(f"      {ctx.dim}{p.description}{ctx.nc}")
    return True


def _handle_plugin_reload(ctx: HandlerCtx) -> bool:
    if ctx.result != "__plugin_reload__":
        return False
    from nyx.agent.services.plugin_manager import PluginManager

    pm = PluginManager()
    results = pm.reload()
    ok = sum(1 for v in results.values() if v)
    print(
        f"  {ctx.accent}[ok]{ctx.nc} plugins recarregados: "
        f"{ok}/{len(results)} OK"
    )
    return True


def _handle_plugin_install(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__plugin_install__")):
        return False
    src = ctx.result[len("__plugin_install__"):].strip()
    from nyx.agent.services.plugin_manager import PluginManager

    pm = PluginManager()
    name = pm.install(src)
    if name:
        print(f"  {ctx.accent}[ok]{ctx.nc} plugin '{name}' instalado")
    else:
        ctx.print_error(
            f"Falha ao instalar plugin a partir de {src!r}.",
            hint="Confirme que o diretório existe e contém manifest.toml válido.",
        )
    return True


def _handle_plugin_uninstall(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__plugin_uninstall__")):
        return False
    name = ctx.result[len("__plugin_uninstall__"):].strip()
    from nyx.agent.services.plugin_manager import PluginManager

    pm = PluginManager()
    pm.discover()
    if pm.uninstall(name):
        print(f"  {ctx.accent}[ok]{ctx.nc} plugin '{name}' removido")
    else:
        ctx.print_error(
            f"Plugin '{name}' não encontrado.",
            hint="Use /plugin list para ver instalados.",
        )
    return True


async def _handle_mcp_list(ctx: HandlerCtx) -> bool:
    if ctx.result != "__mcp_list__":
        return False
    from nyx.agent.services.mcp_client import McpClient

    client = McpClient.from_config()
    if not client.servers:
        ctx.print_error(
            "Nenhum server MCP configurado.",
            hint="Crie ~/.nyx/mcp.json com {\"servers\": {...}}.",
        )
        return True
    await client.connect_all()
    print(f"  Servers MCP ({len(client.servers)}):")
    for name, srv in client.servers.items():
        status = (
            f"{ctx.accent}OK{ctx.nc}" if srv.connected else f"{ctx.dim}{srv.error or 'down'}{ctx.nc}"
        )
        print(f"    {ctx.accent}{name}{ctx.nc} [{status}] -- {len(srv.tools)} tool(s)")
        for tool in srv.tools[:5]:
            tname = tool.get("name", "?")
            tdesc = (tool.get("description") or "").strip()[:60]
            print(f"      {ctx.dim}- {tname}: {tdesc}{ctx.nc}")
        if len(srv.tools) > 5:
            print(f"      {ctx.dim}... (+{len(srv.tools) - 5} tools){ctx.nc}")
    await client.close_all()
    return True


async def _handle_mcp_reload(ctx: HandlerCtx) -> bool:
    if ctx.result != "__mcp_reload__":
        return False
    from nyx.agent.services.mcp_client import McpClient

    client = McpClient.from_config()
    if not client.servers:
        ctx.print_error("Nenhum server MCP em ~/.nyx/mcp.json.", hint=None)
        return True
    results = await client.connect_all()
    ok = sum(1 for v in results.values() if v)
    print(f"  {ctx.accent}[ok]{ctx.nc} MCP recarregado: {ok}/{len(results)} server(s) conectado(s)")
    await client.close_all()
    return True


async def _handle_mcp_test(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__mcp_test__")):
        return False
    target = ctx.result[len("__mcp_test__"):].strip()
    from nyx.agent.services.mcp_client import McpClient

    client = McpClient.from_config()
    if target not in client.servers:
        ctx.print_error(
            f"Server MCP '{target}' não encontrado.",
            hint="Veja /mcp list.",
        )
        return True
    await client.connect_all()
    alive = await client.ping(target)
    if alive:
        print(f"  {ctx.accent}[ok]{ctx.nc} MCP {target} responde (ping ok)")
    else:
        ctx.print_error(
            f"MCP {target} não responde ao ping.",
            hint="Verifique o command/args em ~/.nyx/mcp.json.",
        )
    await client.close_all()
    return True


def _handle_edit_last(ctx: HandlerCtx) -> bool:
    if ctx.result != "__edit_last__":
        return False
    last = ctx.last_input_state.get("text", "")
    if not last:
        ctx.print_error(
            "Nenhum input anterior para editar.",
            hint="Envie uma mensagem antes de usar /edit.",
        )
        return True
    ctx.app_state["prefill"] = last
    print(f"  {ctx.dim}último input prefillado no próximo prompt; edite e Enter.{ctx.nc}")
    return True


def _handle_config_setup(ctx: HandlerCtx) -> bool:
    if ctx.result != "__config_setup__":
        return False
    # ONBOARDING-01: wizard interativo grava ~/.nyx/config.toml.
    config_path = Path.home() / ".nyx" / "config.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    if config_path.exists():
        backup = config_path.with_suffix(".toml.bak")
        backup.write_bytes(config_path.read_bytes())
        print(f"  {ctx.dim}backup salvo em {backup}{ctx.nc}")
    try:
        from nyx.config.defaults import DEFAULT_MODEL as _DM

        modelo = input(f"  modelo preferido [{_DM}]: ").strip() or _DM
        tema = input("  tema [paleta_d]: ").strip() or "paleta_d"
        bypass = input(
            "  bypass default (cauteloso/moderado/ousado) [cauteloso]: "
        ).strip() or "cauteloso"
        ctx_raw = input("  limite de contexto em turnos [40]: ").strip() or "40"
        try:
            ctx_limit = int(ctx_raw)
        except ValueError:
            print(f"  {ctx.dim}valor inválido, usando 40{ctx.nc}")
            ctx_limit = 40
    except (EOFError, KeyboardInterrupt):
        print(f"\n  {ctx.dim}/config setup cancelado{ctx.nc}")
        return True

    content = (
        "# Configuração Nyx gerada via /config setup (ONBOARDING-01)\n"
        f'modelo = "{modelo}"\n'
        f'tema = "{tema}"\n'
        f'bypass = "{bypass}"\n'
        f"ctx_limit = {ctx_limit}\n"
    )
    tmp = config_path.with_suffix(".toml.tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(config_path)
    print(f"  {ctx.accent}[ok]{ctx.nc} configuração salva em {config_path}")
    return True


def _handle_session_index(ctx: HandlerCtx) -> bool:
    if ctx.result != "__session_index__":
        return False
    from nyx.agent.persistence import load_index

    idx = load_index()
    if not idx:
        ctx.print_error(
            "Nenhuma sessão indexada.",
            hint="Saia com /quit para gerar a primeira entrada do índice.",
        )
        return True
    print(f"  {len(idx)} sessões no índice (mais recentes embaixo):")
    for entry in idx[-20:]:
        sid = entry.get("id", "?")
        prompt_preview = entry.get("primeiro_prompt", "")[:60]
        n = entry.get("n_turnos", 0)
        print(f"    {ctx.accent}{sid[:32]:<32}{ctx.nc}  {n:>2} turnos  {ctx.dim}{prompt_preview}{ctx.nc}")
    return True


def _handle_model(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__model__")):
        return False
    new_model = ctx.result.replace("__model__", "")
    ctx.agent._model = new_model
    print(f"  {ctx.accent}[ok]{ctx.nc} Modelo trocado para: {new_model}")
    return True


def _handle_rewind(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__rewind__")):
        return False
    n = int(ctx.result.replace("__rewind__", "") or "1")
    removed = min(n, len(ctx.agent.session.history))
    for _ in range(removed):
        if ctx.agent.session.history:
            ctx.agent.session.history.pop()
    print(f"  {ctx.accent}[ok]{ctx.nc} Desfeitas {removed} entradas do histórico.")
    return True


def _handle_stats(ctx: HandlerCtx) -> bool:
    if ctx.result != "__stats__":
        return False
    s = ctx.agent.session
    stats = ctx.agent.parser_stats
    status_msg = (
        f"  Iterações: {s.iteration}\n"
        f"  Arquivos lidos: {s.files_read_count}\n"
        f"  Arquivos modificados: {s.files_modified_count}\n"
        f"  Entradas no histórico: {len(s.history)}\n"
        f"  Parser taxa sucesso: {stats['success_rate']:.0%}\n"
        f"  Tools: {ctx.agent.tools_count}"
    )
    print(status_msg)
    return True


def _handle_usage(ctx: HandlerCtx) -> bool:
    if ctx.result != "__usage__":
        return False
    info = ctx.agent.get_context_info()
    usage_msg = (
        f"  Contexto: {info.get('pct', 0):.0%} usado\n"
        f"  Tokens sistema: {info.get('system_tokens', 0)}\n"
        f"  Tokens usuário: {info.get('user_tokens', 0)}\n"
        f"  Total: {info.get('total_tokens', 0)}/{info.get('max_tokens', 0)}"
    )
    print(usage_msg)
    return True


def _handle_files(ctx: HandlerCtx) -> bool:
    if ctx.result != "__files__":
        return False
    ctx_text = ctx.agent.session.get_files_context()
    if ctx_text:
        print(f"  {ctx_text}")
    else:
        ctx.print_error(
            "Nenhum arquivo no contexto da sessão.",
            hint="Peça a Nyx para ler um arquivo ou use /read <caminho>.",
        )
    return True


def _handle_debug_session(ctx: HandlerCtx) -> bool:
    if ctx.result != "__debug_session__":
        return False
    from nyx.agent.commands._observability import render_debug_session
    print(render_debug_session(ctx.agent))
    return True


def _handle_replay(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__replay__")):
        return False
    from nyx.agent.commands._observability import render_replay
    rendered = render_replay(Path(ctx.agent._project_root), ctx.result.replace("__replay__", ""))
    if isinstance(rendered, str) and rendered.startswith("__error__"):
        _print_sentinel_error(ctx, rendered)
    else:
        print(rendered)
    return True


def _handle_progress_tail(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__progress_tail__")):
        return False
    from nyx.agent.services.gsd_writer import load_progress_tail

    try:
        n = int(ctx.result.replace("__progress_tail__", "") or "30")
    except ValueError:
        n = 30
    sid = getattr(ctx.agent, "_session_id", "") or ""
    tail = load_progress_tail(sid, n=n) if sid else ""
    if tail:
        print(tail)
    else:
        ctx.print_error(
            "Nenhum progresso registrado ainda.",
            hint="O progress.md e criado no primeiro turno; faça uma pergunta primeiro.",
        )
    return True


def _handle_trace(ctx: HandlerCtx) -> bool:
    if ctx.result != "__trace__":
        return False
    entries = [e for e in ctx.agent.session.history if e.tool_name]
    if not entries:
        ctx.print_error(
            "Nenhuma tool call registrada nesta sessão.",
            hint="Faça uma pergunta à Nyx para gerar atividade antes de inspecionar /trace.",
        )
    else:
        print("  Últimas tool calls:")
        for e in entries[-10:]:
            args_short = str(e.tool_args)[:50]
            print(f"    {ctx.accent}{e.tool_name}{ctx.nc}({args_short})")
    return True


def _handle_btw(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__btw__")):
        return False
    note = ctx.result[7:]
    ctx.agent.session.add_user(f"[nota lateral] {note}")
    print(f"  {ctx.dim}Nota registrada: {note[:60]}{ctx.nc}")
    return True


def _handle_export(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__export__")):
        return False
    fmt = ctx.result.replace("__export__", "") or "md"
    export_dir = Path.home() / ".nyx" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    export_path = export_dir / f"session_{ts}.{fmt}"
    lines = []
    for entry in ctx.agent.session.history:
        if entry.tool_name:
            lines.append(f"[{entry.tool_name}] {str(entry.tool_args)[:80]}")
        else:
            lines.append(f"[{entry.role}] {entry.content[:200]}")
    export_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  {ctx.accent}[ok]{ctx.nc} Sessão exportada: {export_path}")
    return True


def _handle_copy(ctx: HandlerCtx) -> bool:
    if ctx.result != "__copy__":
        return False
    import subprocess as _sp

    last_content = ""
    for entry in reversed(ctx.agent.session.history):
        if entry.role == "assistant" or entry.tool_result:
            last_content = entry.content or entry.tool_result
            break
    if last_content:
        try:
            _sp.run(["xclip", "-selection", "clipboard"], input=last_content.encode(), timeout=5)
            print(f"  {ctx.accent}[ok]{ctx.nc} Copiado para clipboard ({len(last_content)} chars)")
        except FileNotFoundError as exc:
            tmp = Path.home() / ".nyx" / "clipboard.txt"
            tmp.write_text(last_content, encoding="utf-8")
            ctx.print_error(
                "xclip indisponível no sistema.",
                hint=f"Conteúdo salvo em {tmp}. Instale com: sudo apt install xclip",
                debug_detail=str(exc),
            )
    else:
        ctx.print_error(
            "Nenhum output disponível para copiar.",
            hint="Aguarde uma resposta da Nyx ou execute um comando antes de /copy.",
        )
    return True


def _split_error_sentinel(value: str) -> tuple[str, str | None]:
    """Normaliza o sentinel `__error__<msg>||<hint>` em `(msg, hint)`.

    Espelha `_split_error_sentinel` da TUI Textual (sprint 357,
    nyx/agent/tui/app.py): remove o prefixo `__error__` e quebra em `||`.
    Sem `||`, devolve a mensagem inteira e `hint=None`.
    """
    payload = value[len("__error__"):]
    if "||" in payload:
        msg, hint = payload.split("||", 1)
        return msg, hint
    return payload, None


def _print_sentinel_error(ctx: HandlerCtx, value: str) -> None:
    """Imprime via print_error um retorno de helper que veio como sentinel.

    CLI-REPL-REPLAY-ERROR-SENTINEL-LEAK-01: handlers que imprimem o retorno
    de render_* (ex.: render_replay) podem receber `__error__<msg>||<hint>`
    quando o helper falha. Em vez de `print()` cru do marcador, normaliza
    pela mesma rota do _handle_error legado.
    """
    msg, hint = _split_error_sentinel(value)
    ctx.print_error(msg, hint=hint)


def _handle_error(ctx: HandlerCtx) -> bool:
    if not (isinstance(ctx.result, str) and ctx.result.startswith("__error__")):
        return False
    _print_sentinel_error(ctx, ctx.result)
    return True


# --- Handlers síncronos (ordenação importa: prefix-match no fim) ---
_SYNC_HANDLERS = [
    _handle_clear,
    _handle_status,
    _handle_context,
    _handle_session_save,
    _handle_session_load,
    _handle_session_load_id,
    _handle_sandbox_list,
    _handle_sandbox_add,
    _handle_sandbox_remove,
    _handle_cd,
    _handle_cancel_inflight,
    _handle_aesthetic_list,
    _handle_aesthetic_get,
    _handle_aesthetic_set,
    _handle_schema_list,
    _handle_schema_get,
    _handle_schema_set,
    _handle_output_style_list,
    _handle_output_style_get,
    _handle_output_style_set,
    _handle_plugin_list,
    _handle_plugin_reload,
    _handle_plugin_install,
    _handle_plugin_uninstall,
    _handle_edit_last,
    _handle_config_setup,
    _handle_session_index,
    _handle_model,
    _handle_rewind,
    _handle_stats,
    _handle_usage,
    _handle_files,
    _handle_debug_session,
    _handle_replay,
    _handle_progress_tail,
    _handle_trace,
    _handle_btw,
    _handle_export,
    _handle_copy,
    _handle_error,
]


def dispatch_sync(ctx: HandlerCtx) -> bool:
    """Tenta resolver `ctx.result` via handlers síncronos.

    Retorna True se algum handler casou (REPL deve fazer `continue`),
    False se nenhum reconheceu o sentinel (REPL continua).
    """
    for h in _SYNC_HANDLERS:
        if h(ctx):
            return True
    return False


# --- Handlers async (precisam de await) ---
_ASYNC_HANDLERS = [
    _handle_mcp_list,
    _handle_mcp_reload,
    _handle_mcp_test,
]


async def dispatch_async(ctx: HandlerCtx) -> bool:
    """Tenta resolver `ctx.result` via handlers async (MCP).

    Retorna True se algum handler casou. False caso contrário.
    """
    for h in _ASYNC_HANDLERS:
        if await h(ctx):
            return True
    return False
