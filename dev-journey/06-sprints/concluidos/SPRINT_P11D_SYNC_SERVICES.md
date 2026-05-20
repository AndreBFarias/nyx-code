## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P11-D
  title: "Sync services -- settingsSync, remoteManagedSettings, teamMemorySync"
  touches:
    - path: nyx/agent/services/settings_sync.py
    - path: nyx/agent/services/remote_settings.py
    - path: nyx/agent/services/team_sync.py
  origin:
    primary: "openclaud/src/services/settingsSync/"
  tests:
    - cmd: "./run.sh --gauntlet --only p11_sync"
      timeout: 30
```

---

# Sprint P11-D -- Sync Services

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20)  **original:** PENDENTE  **Tipo:** Port  **Deps:** P11-A

## Services

| Service | OpenClaude | Adaptação local |
|---------|-----------|----------------|
| settings_sync | settingsSync/ | Sync de config entre máquinas (via git ou arquivo) |
| remote_settings | remoteManagedSettings/ | Settings gerenciados remotamente -> local |
| team_sync | teamMemorySync/ | Sync de memória entre membros da equipe (via git) |

---

*"Sincronizar é harmonizar." -- conceito musical*
