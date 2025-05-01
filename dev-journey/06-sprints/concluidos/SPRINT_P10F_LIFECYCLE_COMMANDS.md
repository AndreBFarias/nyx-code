## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P10-F
  title: "Lifecycle commands -- upgrade, release-notes, feedback, privacy-settings, sandbox-toggle, terminalSetup"
  touches:
    - path: nyx/agent/commands.py
      reason: "6 novos commands de ciclo de vida"
  origin:
    primary: "openclaud/src/commands/upgrade/"
  tests:
    - cmd: "./run.sh --gauntlet --only p10_lifecycle"
      timeout: 30
```

---

# Sprint P10-F -- Lifecycle Commands

**Status:** PENDENTE  **Tipo:** Port  **Deps:** P10-B

## Commands

| Command | OpenClaude | Descrição |
|---------|-----------|-----------|
| /upgrade | upgrade/ | Verifica e aplica atualizações do Nyx |
| /release-notes | release-notes/ | Mostra notas da versão |
| /feedback | feedback/ | Envia feedback (salva local) |
| /privacy | privacy-settings/ | Configurações de privacidade |
| /sandbox | sandbox-toggle/ | Toggle modo sandbox |
| /terminal-setup | terminalSetup/ | Configura terminal (cores, encoding) |

---

*"A mudança é a única constante." -- Heráclito*
