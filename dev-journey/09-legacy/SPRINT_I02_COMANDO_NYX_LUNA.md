## 0. SPEC (machine-readable)

```yaml
sprint:
  id: I-02
  title: "Comando /nyx na Luna"
  touches:
    - path: Luna/src/skills/code_agent/commands.py
      reason: "Registrar comando /nyx"
    - path: Luna/src/skills/code_agent/hooks.py
      reason: "Hook de troca de entidade"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "2 testes novos"
  forbidden:
    - "Quebrar funcionalidade existente da Luna"
  tests:
    - cmd: "./run.sh --gauntlet --only i_luna"
      timeout: 30
  acceptance_criteria:
    - "/nyx inicia Nyx-Code em modo headless como subprocess"
    - "Entidade troca para Nyx ao ativar"
    - "Nyx-Code subprocess gerenciado (start/stop)"
    - "Timeout e error handling"
```

---

# Sprint I-02 -- Comando /nyx na Luna

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** ALTA
**Tipo:** Feature (integração)
**Dependências:** I-01
**Desbloqueia:** I-03

---

## Problema / Contexto

A Luna tem um code agent interno. Precisamos registrar `/nyx` como
comando que inicia o Nyx-Code como subprocess em modo headless,
delegando tarefas de código para ele.

## Implementação

### Comando /nyx no command_registry da Luna
- Registrar `/nyx` como command
- `/nyx` -- ativa modo Nyx (inicia subprocess)
- `/nyx off` -- desativa (para subprocess)
- `/nyx status` -- mostra status do subprocess

### NyxCodeService
- Inicia `python -m nyx.cli --headless` como subprocess
- Comunicação via stdin/stdout JSON (protocolo I-01)
- Gerenciamento de lifecycle (start/stop/restart)
- Timeout por request (120s default)
- Health check via ping/pong

### Troca de entidade
- Ao ativar /nyx, mensagens usam nome "Nyx"
- Ao desativar, volta para entidade anterior

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| I2-01 | NyxCodeService importa | Classe inicializa |
| I2-02 | Subprocess headless responde | start + ping + stop |

## Verificação

- [ ] /nyx registrado na Luna
- [ ] Subprocess inicia e responde ping
- [ ] Cleanup ao parar
- [ ] Timeout funciona
- [ ] 2 testes Gauntlet passando

---

*"A integração é mais difícil que a criação." -- Fred Brooks*
