## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P9-B
  title: "Platform Tools -- Shell, Trigger, Schedule, Synthetic, Team"
  touches:
    - path: nyx/agent/tools/shell_tool.py
      reason: "ShellTool cross-platform (adapta PowerShellTool)"
    - path: nyx/agent/tools/trigger_tool.py
      reason: "RemoteTriggerTool adaptado local"
    - path: nyx/agent/tools/schedule_tool.py
      reason: "ScheduleCronTool"
    - path: nyx/agent/tools/synthetic_output.py
      reason: "SyntheticOutputTool"
    - path: nyx/agent/tools/team_tool.py
      reason: "TeamCreateTool, TeamDeleteTool"
    - path: nyx/agent/tools/run_command.py
      reason: "Expandir BashTool"
    - path: nyx/agent/tools/registry.py
      reason: "Registrar 7 novas tools"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "7 testes novos"
  origin:
    primary: "openclaud/src/tools/PowerShellTool/"
    secondary: "openclaud/src/tools/ScheduleCronTool/"
  tests:
    - cmd: "./run.sh --gauntlet --only p9_platform"
      timeout: 60
  acceptance_criteria:
    - "ShellTool funciona como bash no Linux"
    - "ScheduleCronTool agenda via crontab ou schedule"
    - "TeamCreate/Delete gerencia equipes locais"
    - "BashTool expandido com error handling avançado"
    - "Registry sobe para 46+ tools"
```

---

# Sprint P9-B -- Platform Tools

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** ALTA
**Tipo:** Port (TS -> Python, adaptado)
**Dependências:** P9-A
**Desbloqueia:** P10-A

---

## Implementação

### ShellTool (`nyx/agent/tools/shell_tool.py`)
- Adapta PowerShellTool do OpenClaude para cross-platform
- No Linux: usa bash; detecta shell do sistema
- Parâmetros: command, shell (auto/bash/zsh/fish)

### TriggerTool (`nyx/agent/tools/trigger_tool.py`)
- Adapta RemoteTriggerTool para local
- Dispara via subprocess ou webhook local
- Parâmetros: trigger_type (subprocess/webhook), target, payload

### ScheduleCronTool (`nyx/agent/tools/schedule_tool.py`)
- Agenda tarefas recorrentes
- Usa `crontab` no Linux
- Parâmetros: schedule (cron expression), command, name

### SyntheticOutputTool (`nyx/agent/tools/synthetic_output.py`)
- Gera output estruturado (JSON, Markdown, CSV)
- Parâmetros: format, template, data

### TeamCreate/DeleteTool (`nyx/agent/tools/team_tool.py`)
- Gestão de equipes local (arquivo JSON)
- Persiste em ~/.nyx/teams.json

### BashTool expandido (`nyx/agent/tools/run_command.py`)
- Adicionar: streaming de output, environment vars, working dir
- Adicionar: error handling avançado, kill por timeout

### Testes Gauntlet (fase: p9_platform)

| ID | Nome | Validação |
|----|------|-----------|
| P9P-01 | ShellTool executa | echo test, verifica output |
| P9P-02 | TriggerTool interface | Tool importa |
| P9P-03 | ScheduleCronTool interface | Tool importa |
| P9P-04 | SyntheticOutput gera JSON | Gera JSON válido |
| P9P-05 | TeamCreate cria equipe | Cria, verifica em arquivo |
| P9P-06 | TeamDelete remove equipe | Remove, verifica |
| P9P-07 | BashTool expandido | Timeout e error handling |

---

*"Adaptar é a essência da sobrevivência." -- Charles Darwin*
