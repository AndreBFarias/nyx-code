## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P11-C
  title: "Plugins services -- plugins, MagicDocs, tips, toolUseSummary"
  touches:
    - path: nyx/agent/services/plugins.py
    - path: nyx/agent/services/magic_docs.py
    - path: nyx/agent/services/tips.py
    - path: nyx/agent/services/tool_use_summary.py
  origin:
    primary: "openclaud/src/services/plugins/"
  tests:
    - cmd: "./run.sh --gauntlet --only p11_plugins"
      timeout: 30
```

---

# Sprint P11-C -- Plugins & Content Services

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20)  **original:** PENDENTE  **Tipo:** Port  **Deps:** P11-A

## Services

| Service | OpenClaude | Adaptação local |
|---------|-----------|----------------|
| plugins | plugins/ | Sistema de plugins local (~/.nyx/plugins/) |
| magic_docs | MagicDocs/ | Geração automática de docs |
| tips | tips/ | Dicas contextuais para o usuário |
| tool_use_summary | toolUseSummary/ | Resumo de uso de tools na sessão |

---

*"Extensibilidade é a marca de boa arquitetura." -- Robert Martin*
