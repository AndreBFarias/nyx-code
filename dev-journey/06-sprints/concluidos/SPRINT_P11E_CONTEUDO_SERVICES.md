## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P11-E
  title: "Conteúdo services -- extractMemories, autoDream, awaySummary, AgentSummary expandido"
  touches:
    - path: nyx/agent/services/extract_memories.py
    - path: nyx/agent/services/auto_dream.py
    - path: nyx/agent/services/away_summary.py
    - path: nyx/agent/services/summary.py
      reason: "Expandir AgentSummary"
  origin:
    primary: "openclaud/src/services/extractMemories/"
  tests:
    - cmd: "./run.sh --gauntlet --only p11_conteudo"
      timeout: 30
```

---

# Sprint P11-E -- Conteúdo Services

**Status:** PENDENTE  **Tipo:** Port  **Deps:** P11-B

## Services

| Service | OpenClaude | Adaptação local |
|---------|-----------|----------------|
| extract_memories | extractMemories/ | Extrai memórias-chave da sessão automaticamente |
| auto_dream | autoDream/ | Processamento assíncrono de insights |
| away_summary | awaySummary.ts | Resumo do que aconteceu enquanto offline |
| summary (expandir) | AgentSummary/ | Expandir com métricas detalhadas |

---

*"A reflexão é a mãe da sabedoria." -- Demócrito*
