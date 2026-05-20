## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P11-A
  title: "Infra services -- analytics, diagnosticTracking, internalLogging, notifier, preventSleep"
  touches:
    - path: nyx/agent/services/analytics.py
    - path: nyx/agent/services/diagnostics.py
    - path: nyx/agent/services/logging_service.py
    - path: nyx/agent/services/notifier.py
    - path: nyx/agent/services/prevent_sleep.py
  origin:
    primary: "openclaud/src/services/analytics/"
  tests:
    - cmd: "./run.sh --gauntlet --only p11_infra"
      timeout: 30
```

---

# Sprint P11-A -- Infra Services

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20)  **original:** PENDENTE  **Tipo:** Port  **Deps:** P10-J

## Services

| Service | OpenClaude | Adaptação local |
|---------|-----------|----------------|
| analytics | analytics/ | Métricas locais em ~/.nyx/analytics.json |
| diagnostics | diagnosticTracking.ts | Tracking de erros/warnings |
| logging_service | internalLogging.ts | Logging estruturado rotacionado |
| notifier | notifier.ts | Notificações desktop (notify-send) |
| prevent_sleep | preventSleep.ts | Previne sleep durante operações longas |

---

*"O que não se mede não se gerencia." -- Peter Drucker*
