## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P4-C
  title: "Tasks expandido -- TaskGet, TaskOutput, TaskStop"
  touches:
    - path: nyx/agent/tools/task_manager.py
      reason: "Adicionar 3 tools ao módulo existente"
    - path: nyx/agent/tools/registry.py
      reason: "Registrar 3 novas tools"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "3 testes novos"
  origin:
    primary: "openclaud/src/tools/TaskGetTool/"
    secondary: "openclaud/src/tools/TaskOutputTool/"
    tertiary: "openclaud/src/tools/TaskStopTool/"
  tests:
    - cmd: "./run.sh --gauntlet --only p4_tasks"
      timeout: 30
  acceptance_criteria:
    - "TaskGetTool retorna detalhes de task por ID"
    - "TaskOutputTool retorna output de task em execução"
    - "TaskStopTool marca task como cancelled"
    - "Registry sobe para 25 tools (após P4-A + P4-B + P4-C)"
```

---

# Sprint P4-C -- Tasks expandido

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Port (TS -> Python)
**Dependências:** P4-A
**Desbloqueia:** P4-D

---

## Implementação

Expandir `nyx/agent/tools/task_manager.py` existente com 3 novas classes:

### 1. TaskGetTool
- Parâmetro: `task_id` (str)
- Retorna: subject, description, status, timestamps, output
- Erro se task não encontrada

### 2. TaskOutputTool
- Parâmetro: `task_id` (str)
- Retorna: output da task (log de execução)
- Se task ainda running, retorna output parcial

### 3. TaskStopTool
- Parâmetro: `task_id` (str)
- Muda status para "cancelled"
- Adiciona cancelled_at timestamp
- Retorna confirmação

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P4T-01 | TaskGet retorna detalhes | Cria task, get por ID, verifica subject |
| P4T-02 | TaskOutput retorna output | Cria task, adiciona output, verifica conteúdo |
| P4T-03 | TaskStop cancela | Cria task, stop, verifica status == cancelled |

## Verificação

- [ ] 3 novas tools importam sem erro
- [ ] TaskGet retorna todos os campos
- [ ] TaskStop muda status corretamente
- [ ] 3 testes Gauntlet passando

---

*"Dividir cada dificuldade em tantas partes quanto possível." -- Descartes*
