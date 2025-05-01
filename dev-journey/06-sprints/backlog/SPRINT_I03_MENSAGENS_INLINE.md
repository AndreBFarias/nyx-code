## 0. SPEC (machine-readable)

```yaml
sprint:
  id: I-03
  title: "Mensagens inline na TUI Luna ([nyx] prefix)"
  touches:
    - path: Luna/src/app/event_handlers.py
      reason: "Handler para mensagens do Nyx"
    - path: Luna/src/skills/code_agent/loop.py
      reason: "Integrar respostas do Nyx no fluxo"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "2 testes novos"
  forbidden:
    - "Quebrar mensagens existentes da Luna"
  tests:
    - cmd: "./run.sh --gauntlet --only i_inline"
      timeout: 30
  acceptance_criteria:
    - "Respostas do Nyx aparecem com prefixo [nyx]"
    - "Tool calls do Nyx mostram nome da tool"
    - "Status done do Nyx mostra resumo"
    - "Erros do Nyx formatados como [nyx:erro]"
```

---

# Sprint I-03 -- Mensagens inline

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Feature (integração)
**Dependências:** I-02
**Desbloqueia:** --

---

## Problema / Contexto

Quando o Nyx-Code processa um request via headless, as respostas
precisam aparecer inline na TUI da Luna com prefixo `[nyx]`,
similar ao estilo `[kernel]` ou `[augur]`.

## Implementação

### Formato de mensagens na TUI

```
[nyx] Lendo arquivo README.md...
[nyx:tool] read_file(README.md) -> 120 linhas
[nyx:tool] edit_file(README.md) -> 3 linhas modificadas
[nyx] Tarefa concluída: arquivo atualizado com documentação.
```

### Handler de eventos
- Cada mensagem JSON do stdout do Nyx é parseada
- `type: "tool_use"` -> `[nyx:tool] nome(args)`
- `type: "response"` -> `[nyx] resumo`
- `type: "error"` -> `[nyx:erro] mensagem`

### Streaming (futuro)
- Se Nyx suportar streaming headless, mostrar tokens em tempo real
- Prefixo `[nyx]` só no início da resposta

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| I3-01 | Formato [nyx] | Mensagem formatada contém prefixo |
| I3-02 | Handler parseia JSON | JSON de tool_use vira string formatada |

## Verificação

- [ ] Mensagens com prefixo [nyx] na TUI
- [ ] Tool calls formatados corretamente
- [ ] Erros formatados como [nyx:erro]
- [ ] 2 testes Gauntlet passando

---

*"A comunicação clara é a base da cooperação." -- Peter Drucker*
