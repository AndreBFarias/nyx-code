## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P10-B
  title: "Projeto commands -- add-dir, init, onboarding, version, rename"
  touches:
    - path: nyx/agent/commands.py
      reason: "5 novos commands de projeto"
  origin:
    primary: "openclaud/src/commands/init/"
  tests:
    - cmd: "./run.sh --gauntlet --only p10_projeto"
      timeout: 30
```

---

# Sprint P10-B -- Projeto Commands

**Status:** PENDENTE  **Tipo:** Port  **Deps:** P9-B

## Commands

| Command | OpenClaude | Descrição |
|---------|-----------|-----------|
| /add-dir | add-dir/ | Adiciona diretório ao contexto do agent |
| /init | init/ | Inicializa projeto Nyx (cria .nyx/, config) |
| /onboarding | onboarding/ | Tour guiado para novos usuários |
| /version | version.ts | Mostra versão do Nyx |
| /rename | rename/ | Renomeia sessão ou projeto |

---

*"Todo começo é difícil." -- Karl Marx*
