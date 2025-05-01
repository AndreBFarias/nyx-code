## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P10-E
  title: "Plataforma commands -- chrome, desktop, ide, mobile, bridge, teleport, remote-env, remote-setup, voice"
  touches:
    - path: nyx/agent/commands.py
      reason: "9 novos commands de plataforma"
  origin:
    primary: "openclaud/src/commands/desktop/"
  tests:
    - cmd: "./run.sh --gauntlet --only p10_plataforma"
      timeout: 30
```

---

# Sprint P10-E -- Plataforma Commands

**Status:** PENDENTE  **Tipo:** Port  **Deps:** P10-A

## Commands

| Command | OpenClaude | Adaptação local-first |
|---------|-----------|----------------------|
| /chrome | chrome/ | Integração browser (via MCP ou headless) |
| /desktop | desktop/ | Info desktop / terminal |
| /ide | ide/ | Integração com editores (VSCode, etc.) |
| /mobile | mobile/ | Info plataforma mobile (stub) |
| /bridge | bridge/ | Bridge entre sessões |
| /teleport | teleport/ | Transferência de contexto entre sessões |
| /remote-env | remote-env/ | Variáveis de ambiente remotas -> locais |
| /remote-setup | remote-setup/ | Setup de ambiente remoto -> local |
| /voice | voice/ | Toggle input por voz (via whisper local) |

---

*"A plataforma é o terreno da batalha." -- Sun Tzu (adaptado)*
