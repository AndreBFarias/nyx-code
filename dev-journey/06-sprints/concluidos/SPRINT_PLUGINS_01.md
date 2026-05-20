# SPRINT PLUGINS-01 — Sistema de plugins instaláveis

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PLUGINS-01
  title: "Plugins Python instaláveis em ~/.nyx/plugins/ com manifest, tools e commands próprios"
  onda: 23
  bloco: 23.5 Feature parity Claude Code
  prioridade: MÉDIA
  tipo: Feature+Infra
  dependencias: [MCP-SERVER-01]
  desbloqueia: []
  origem: "Auditoria estratégica 2026-05-16 — gap real vs Claude Code: zero ocorrências de 'plugin' em nyx/. Permite usuários estenderem o Nyx sem PR no fonte."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
      reason: "Auto-load de plugins no boot via plugin_manager"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_registry.py
      reason: "Auto-load de commands de plugins"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "NYX_PLUGINS_DIR = ~/.nyx/plugins (fonte única)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/plugin_manager.py
      reason: "Descobre, valida (manifest), carrega e reload de plugins"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/plugin.py
      reason: "Slash commands: /plugin list, /plugin install <path>, /plugin reload, /plugin uninstall <name>"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/PLUGIN_API.md
      reason: "Documentação para criadores de plugins: schema do manifest.toml, hooks de registro"

  removes: []

  n_to_n_pairs:
    - descricao: "Schema do manifest.toml definido em plugin_manager.py + documentado em PLUGIN_API.md"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/plugin_manager.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/PLUGIN_API.md

  forbidden:
    - "Plugin executa código arbitrário no import (sandbox AST-check no manifest validate)"
    - "Plugin com tool homônima a tool nativa sem prefixo de namespace"
    - "Plugin sem manifest.toml é carregado mesmo assim"
    - "Recursão: plugin que instala outro plugin no boot (não-determinístico)"
    - "Emoji"

  tests:
    - cmd: "./venv/bin/python -c 'from nyx.agent.services.plugin_manager import PluginManager; pm = PluginManager(); print(pm.list())'"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "~/.nyx/plugins/<name>/manifest.toml define: name, version, description, tools[], commands[]"
    - "PluginManager.discover() escaneia plugins/ e valida manifests"
    - "Tools de plugin entram no ToolRegistry com namespace 'plug_<name>_<tool>'"
    - "Commands de plugin entram no command registry com namespace '/plug:<name>:<cmd>'"
    - "/plugin list mostra plugins ativos (name, version, tools_count, commands_count)"
    - "/plugin install <path> copia para ~/.nyx/plugins/ e valida"
    - "/plugin reload re-importa sem restart do Nyx (importlib.reload)"
    - "/plugin uninstall <name> remove diretório do plugin"
    - "PLUGIN_API.md tem exemplo completo de plugin (tool + command + manifest)"
    - "Boot tolera plugin malformado (warning + skip, não crasha)"
    - "PT-BR; zero emoji; zero menção a IA"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-16
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint PLUGINS-01

## Contexto

Claude Code tem `claude plugin install/list/reload`. Sem isso, Nyx exige PR no fonte para qualquer extensão — barreira que impede comunidade.

## Schema do manifest

```toml
# ~/.nyx/plugins/meu_plugin/manifest.toml
name = "meu_plugin"
version = "0.1.0"
description = "Plugin de exemplo"
author = "Andre"

[[tools]]
name = "minha_tool"
module = "meu_plugin.tools.minha_tool"
function = "execute"

[[commands]]
name = "minha-cmd"
module = "meu_plugin.commands.minha_cmd"
function = "handle"
```

## Estrutura de pastas de um plugin

```
~/.nyx/plugins/meu_plugin/
├── manifest.toml
├── __init__.py
├── tools/
│   ├── __init__.py
│   └── minha_tool.py
└── commands/
    ├── __init__.py
    └── minha_cmd.py
```

## Verificação

```bash
mkdir -p ~/.nyx/plugins/exemplo
cat > ~/.nyx/plugins/exemplo/manifest.toml <<EOF
name = "exemplo"
version = "0.1.0"
description = "Plugin de teste"
[[commands]]
name = "ping"
module = "exemplo.commands.ping"
function = "handle"
EOF
# criar exemplo/commands/ping.py
./run.sh
# nyx> /plugin list
# nyx> /plug:exemplo:ping
```

---

*"O ecossistema cresce ou morre dependendo da barreira para contribuir." -- princípio de plataforma*
