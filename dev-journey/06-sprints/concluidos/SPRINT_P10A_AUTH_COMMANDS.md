## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P10-A
  title: "Auth commands -- login, logout, oauth-refresh, install-github-app, install-slack-app"
  touches:
    - path: nyx/agent/commands.py
      reason: "5 novos commands de autenticação"
  origin:
    primary: "openclaud/src/commands/login/"
  tests:
    - cmd: "./run.sh --gauntlet --only p10_auth"
      timeout: 30
  acceptance_criteria:
    - "/login gerencia autenticação local"
    - "/logout limpa credenciais"
    - "5 commands registrados"
```

---

# Sprint P10-A -- Auth Commands

**Status:** PENDENTE  **Tipo:** Port  **Deps:** P9-B

## Commands

| Command | OpenClaude | Adaptação local-first |
|---------|-----------|----------------------|
| /login | login/ | Gerencia tokens em ~/.nyx/auth.json |
| /logout | logout/ | Remove tokens locais |
| /oauth-refresh | oauth-refresh/ | Refresh token local |
| /install-github | install-github-app/ | Configura gh CLI integration |
| /install-slack | install-slack-app/ | Configura webhook Slack local |

---

*"Segurança é um processo, não um produto." -- Bruce Schneier*
