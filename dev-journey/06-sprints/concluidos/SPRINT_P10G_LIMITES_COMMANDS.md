## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P10-G
  title: "Limites commands -- cost, extra-usage, mock-limits, passes, rate-limit-options, reset-limits"
  touches:
    - path: nyx/agent/commands.py
      reason: "6 novos commands de limites"
  origin:
    primary: "openclaud/src/commands/cost/"
  tests:
    - cmd: "./run.sh --gauntlet --only p10_limites"
      timeout: 30
```

---

# Sprint P10-G -- Limites Commands

**Status:** PENDENTE  **Tipo:** Port  **Deps:** P10-B

## Commands

| Command | OpenClaude | Adaptação local-first |
|---------|-----------|----------------------|
| /cost | cost/ | Estimativa de custo em tokens/VRAM |
| /extra-usage | extra-usage/ | Uso extra de recursos |
| /mock-limits | mock-limits/ | Simula limites para teste |
| /passes | passes/ | Gerencia passes de execução |
| /rate-limit | rate-limit-options/ | Configura rate limiting local |
| /reset-limits | reset-limits/ | Reseta limites para defaults |

---

*"Limites são o que dá forma ao infinito." -- platão (adaptado)*
