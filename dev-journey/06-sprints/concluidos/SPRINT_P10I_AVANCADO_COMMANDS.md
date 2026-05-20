## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P10-I
  title: "Avançado commands -- btw, bridge-kick, backfill-sessions, thinkback, thinkback-play, pr_comments"
  touches:
    - path: nyx/agent/commands.py
      reason: "6 novos commands avançados"
  origin:
    primary: "openclaud/src/commands/thinkback/"
  tests:
    - cmd: "./run.sh --gauntlet --only p10_avancado"
      timeout: 30
```

---

# Sprint P10-I -- Avançado Commands

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20)  **original:** PENDENTE  **Tipo:** Port  **Deps:** P10-C

## Commands

| Command | OpenClaude | Descrição |
|---------|-----------|-----------|
| /btw | btw/ | Nota lateral (salva contexto adicional) |
| /bridge-kick | bridge-kick.ts | Reinicia bridge entre sessões |
| /backfill | backfill-sessions/ | Preenche sessões antigas com metadados |
| /thinkback | thinkback/ | Revisita raciocínio anterior |
| /thinkback-play | thinkback-play/ | Replay de raciocínio |
| /pr-comments | pr_comments/ | Mostra comentários de PR inline |

---

*"Revisitar é aprender duas vezes." -- Joseph Joubert*
