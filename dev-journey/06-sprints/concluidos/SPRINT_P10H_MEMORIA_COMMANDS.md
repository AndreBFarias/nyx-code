## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P10-H
  title: "Memória commands -- memory, plugin, reload-plugins, agents, share, tag"
  touches:
    - path: nyx/agent/commands.py
      reason: "6 novos commands de memória e plugins"
  origin:
    primary: "openclaud/src/commands/memory/"
  tests:
    - cmd: "./run.sh --gauntlet --only p10_memoria"
      timeout: 30
```

---

# Sprint P10-H -- Memória & Plugins Commands

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20)  **original:** PENDENTE  **Tipo:** Port  **Deps:** P10-C

## Commands

| Command | OpenClaude | Descrição |
|---------|-----------|-----------|
| /memory | memory/ | Gerencia memórias do SessionMemory |
| /plugin | plugin/ | Instala/remove plugins locais |
| /reload-plugins | reload-plugins/ | Recarrega plugins |
| /agents | agents/ | Lista/gerencia sub-agents |
| /share | share/ | Exporta sessão para compartilhamento |
| /tag | tag/ | Adiciona tags a sessões/arquivos |

---

*"A memória é a guardiã do conhecimento." -- Cícero*
