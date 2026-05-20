## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P10-D
  title: "Debug commands -- ant-trace, autofix-pr, bughunter, ctx_viz, debug-tool-call, heapdump, perf-issue, good-claude, break-cache"
  touches:
    - path: nyx/agent/commands.py
      reason: "9 novos commands de debug"
  origin:
    primary: "openclaud/src/commands/debug-tool-call/"
  tests:
    - cmd: "./run.sh --gauntlet --only p10_debug"
      timeout: 30
```

---

# Sprint P10-D -- Debug Commands

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20)  **original:** PENDENTE  **Tipo:** Port  **Deps:** P10-A

## Commands

| Command | OpenClaude | Adaptação |
|---------|-----------|-----------|
| /trace | ant-trace/ | Trace de execução do agent loop |
| /autofix-pr | autofix-pr/ | Auto-fix de PRs via agent |
| /bughunter | bughunter/ | Busca automática de bugs |
| /ctx-viz | ctx_viz/ | Visualização do contexto |
| /debug-tool | debug-tool-call/ | Debug de chamadas de tool |
| /heapdump | heapdump/ | Dump do estado da memória |
| /perf-issue | perf-issue/ | Diagnóstico de performance |
| /kudos | good-claude/ | Feedback positivo (log local) |
| /break-cache | break-cache/ | Limpa caches internos |

---

*"Depurar é duas vezes mais difícil que programar." -- Brian Kernighan*
