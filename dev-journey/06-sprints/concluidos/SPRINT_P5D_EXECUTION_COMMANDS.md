## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P5-D
  title: "Execução -- /tasks, /skills, /files, /plan expandido"
  touches:
    - path: nyx/agent/commands.py
      reason: "4 novos commands de execução"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "4 testes novos"
  origin:
    primary: "openclaud/src/commands/tasks/"
    secondary: "openclaud/src/commands/files/"
  tests:
    - cmd: "./run.sh --gauntlet --only p5_execution"
      timeout: 30
  acceptance_criteria:
    - "/tasks lista e gerencia tasks via command"
    - "/skills lista skills disponíveis"
    - "/files lista arquivos no contexto do agent"
    - "/plan expandido com execução real"
```

---

# Sprint P5-D -- Commands de Execução

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Port (TS -> Python)
**Dependências:** P5-B
**Desbloqueia:** --

---

## Implementação

### /tasks
- `/tasks` -- lista tasks pendentes (via TaskListTool)
- `/tasks create assunto` -- cria task (via TaskCreateTool)
- `/tasks done ID` -- marca task como concluída (via TaskUpdateTool)
- Atalho command para as tools de task

### /skills
- `/skills` -- lista skills em `~/.nyx/skills/`
- `/skills nome` -- executa skill (via SkillTool)
- Mostra nome + descrição de cada skill

### /files
- `/files` -- lista arquivos lidos e modificados na sessão
- `/files context` -- mostra arquivos no contexto do LLM
- Usa Session.get_files_context()

### /plan (expandir)
- Manter: `/plan feature X` gera prompt para o agent
- Adicionar: `/plan execute` -- executa o plano pendente
- Adicionar: `/plan show` -- mostra plano atual
- Integrar com PlanMode tools

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P5E-01 | /tasks lista | Retorna lista ou "Nenhuma" |
| P5E-02 | /skills registrado | Command existe |
| P5E-03 | /files mostra contexto | Contém "lidos" ou "modificados" |
| P5E-04 | /plan expandido | /plan show retorna algo |

## Verificação

- [ ] 4 commands registrados (3 novos + 1 expandido)
- [ ] /tasks usa tools existentes
- [ ] /files usa Session real
- [ ] /plan tem subcomandos
- [ ] 4 testes Gauntlet passando
- [ ] Total de commands >= 34

---

*"Planejar é trazer o futuro para o presente." -- Alan Lakein*
