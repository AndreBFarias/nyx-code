# SPRINT PLUGINS-02 — Integração automática + fase Gauntlet (anti-débito)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: PLUGINS-02
  title: "Auto-registro de tools/commands de plugins no boot + fase Gauntlet 'plugins'"
  onda: 23
  bloco: 23.5 Feature parity
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [PLUGINS-01]
  desbloqueia: []
  origem: "Anti-débito de PLUGINS-01 — MVP entregue (PluginManager + slash commands + AST check) mas integração automática no ToolRegistry e CommandRegistry ficou fora do escopo."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/registry.py
      reason: "ToolRegistry consome PluginManager.load_all no boot; tools de plugins ganham prefixo plugin_<name>_<tool>"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/_registry.py
      reason: "PluginManager carrega commands via side-effect do @nyx_command"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Fase 'plugins' com plugin de exemplo testando descoberta+load+command"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/plugin_example/manifest.toml
      reason: "Plugin de exemplo usado pelo Gauntlet"

  forbidden:
    - "Plugin tool com nome igual a tool nativa sem prefixo"
    - "Plugin que falha import bloqueia boot"

  acceptance_criteria:
    - "Plugin com tool aparece em ToolRegistry no boot (com prefixo plugin_<name>_<tool>)"
    - "Plugin com command aparece em /help (registrado via @nyx_command)"
    - "Fase Gauntlet 'plugins' com 3 testes: discovery, load OK, command callable"
    - "Smoke + invariants passam"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-17
**Origem:** anti-débito de PLUGINS-01.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
