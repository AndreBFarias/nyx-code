## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PLUGINS-03
  title: "PLUGINS integração ToolRegistry (fecha PLUGINS-02 CONCLUIDA_PARCIAL)"
  onda: 23
  bloco: "23.5 Feature parity"
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [PLUGINS-02]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
      reason: "Adicionar _load_plugin_tools() análogo ao _load_mcp_tools() (criado em MCP-SERVER-03 commit 5e1927e); descobre tools de plugins via plugin_manager e registra com prefix plugin_<plugin>_<tool>"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/plugin_manager.py
      reason: "Expor função discover_plugin_tools() que itera plugins instalados em ~/.nyx/plugins/ e retorna lista de tools para ToolRegistry"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar PL-03 (ToolRegistry integration) na fase plugins existente"

  creates: []
  removes: []

  forbidden:
    - "Bypassar PermissionChecker em tools de plugins"
    - "Bypassar AST check do plugin_manager (segurança)"
    - "Quebrar boot tolerante: sem ~/.nyx/plugins continua funcional"
    - "Quebrar PLUGINS-02 (AST rejeita print top-level)"
    - "Adicionar dependência nova"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
      assert: "PASS=14 FAIL=0"
    - cmd: "python3 -c 'from nyx.agent.tools.registry import ToolRegistry; r = ToolRegistry(\".\"); print(f\"tools={r.tool_count}\")'"
      timeout: 10
      deve_passar: true
      assert: "tool_count >= 35 (zero plugins se ~/.nyx/plugins ausente — boot tolerante)"
    - cmd: "./run.sh --gauntlet --only plugins"
      timeout: 60
      deve_passar: true
      assert: "100% APROVADO incluindo PL-03"

  acceptance_criteria:
    - "ToolRegistry chama _load_plugin_tools() no boot, similar ao _load_mcp_tools()"
    - "Tools de plugins ganham prefix plugin_<nome>_<tool> no registry"
    - "Boot sem ~/.nyx/plugins continua tolerante (tool_count nativas inalterado)"
    - "PermissionChecker valida tools de plugins igual às nativas"
    - "Gauntlet --only plugins inclui PL-03 e passa 100%"
    - "Smoke + invariantes 14/14 + ruff All checks passed + acentuação rc=0"
    - "MASTER linha 129 (PLUGINS-02) ganha nota de fechamento; nova linha para PLUGINS-03 CONCLUIDA"
```

---

# Sprint PLUGINS-03 — Integração ToolRegistry

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

PLUGINS-02 deixou ToolRegistry integration pendente. MCP-SERVER-03 (commit 5e1927e) já estabeleceu o padrão `_load_<source>_tools()` com adapter herdando RegisteredTool. Replicar para plugins.

## Solução

Em `nyx/agent/tools/registry.py`, adicionar `_load_plugin_tools()` análogo ao `_load_mcp_tools()`. Em `nyx/agent/services/plugin_manager.py`, expor `discover_plugin_tools()` que itera plugins instalados e retorna lista de tools.

Padrão da chamada (similar à MCP):
```python
def _load_plugin_tools(self) -> None:
    try:
        from nyx.agent.services.plugin_manager import discover_plugin_tools
        for plugin_name, tools_list in discover_plugin_tools().items():
            for tool_def in tools_list:
                tool_name = f"plugin_{plugin_name}_{tool_def['name']}"
                adapter = PluginToolAdapter(...)
                self._tools[tool_name] = adapter
    except Exception as e:
        logger.warning(f"_load_plugin_tools: falha não-fatal: {e}")
```

## Proof-of-work

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before_plugins.txt 2>&1

# IMPLEMENTAR

./run.sh --smoke
bash scripts/sprint_invariants.sh > /tmp/inv_after_plugins.txt 2>&1

python3 -c 'from nyx.agent.tools.registry import ToolRegistry
r = ToolRegistry(".")
print(f"tool_count={r.tool_count}")
assert r.tool_count >= 35'

./run.sh --gauntlet --only plugins 2>&1 | tail -10

python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/tools/registry.py nyx/agent/services/plugin_manager.py scripts/gauntlet/nyx_gauntlet.py
```

## Critério binário

- [ ] ToolRegistry tem `_load_plugin_tools()` chamado no boot
- [ ] Plugins discover via `discover_plugin_tools()` em plugin_manager
- [ ] Boot tolerante sem ~/.nyx/plugins (tool_count >= 35 nativas)
- [ ] Gauntlet --only plugins 100% APROVADO (PL-01, PL-02 preservadas + PL-03 nova)
- [ ] PluginToolAdapter herda RegisteredTool
- [ ] MASTER linha 129 (PLUGINS-02) + nova linha PLUGINS-03 CONCLUIDA
- [ ] Spec movida producao/ → concluidos/

---

*"Plugins são tools com endereço diferente."*
