## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P10-C
  title: "UI commands -- color, output-style, keybindings, stickers, fast, effort, vim"
  touches:
    - path: nyx/agent/commands.py
      reason: "7 novos commands de interface"
  origin:
    primary: "openclaud/src/commands/color/"
  tests:
    - cmd: "./run.sh --gauntlet --only p10_ui"
      timeout: 30
```

---

# Sprint P10-C -- UI Commands

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20)  **original:** PENDENTE  **Tipo:** Port  **Deps:** P9-B

## Commands

| Command | OpenClaude | Descrição |
|---------|-----------|-----------|
| /color | color/ | Configura cores do terminal |
| /output-style | output-style/ | Estilo de output (verbose/compact/minimal) |
| /keybindings | keybindings/ | Configura atalhos de teclado |
| /stickers | stickers/ | Marcadores visuais para sessões |
| /fast | fast/ | Toggle modo rápido (menos contexto) |
| /effort | effort/ | Define nível de esforço do agent |
| /vim | vim/ | Toggle modo vim |

---

*"Design é como as coisas funcionam." -- Steve Jobs*
