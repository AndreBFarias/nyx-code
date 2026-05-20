## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P11-B
  title: "Auth services -- oauth, claudeAiLimits, claudeAiLimitsHook, policyLimits"
  touches:
    - path: nyx/agent/services/oauth.py
    - path: nyx/agent/services/limits.py
    - path: nyx/agent/services/policy.py
  origin:
    primary: "openclaud/src/services/oauth/"
  tests:
    - cmd: "./run.sh --gauntlet --only p11_auth"
      timeout: 30
```

---

# Sprint P11-B -- Auth Services

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20)  **original:** PENDENTE  **Tipo:** Port  **Deps:** P10-A

## Services

| Service | OpenClaude | Adaptação local |
|---------|-----------|----------------|
| oauth | oauth/ | Token management local (~/.nyx/auth/) |
| limits | claudeAiLimits.ts + hook | Limites de uso local (tokens/hora) |
| policy | policyLimits/ | Políticas de uso configuráveis |

---

*"Confiança se constrói com limites." -- Brene Brown*
