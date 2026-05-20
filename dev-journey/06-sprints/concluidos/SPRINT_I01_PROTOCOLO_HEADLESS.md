## 0. SPEC (machine-readable)

```yaml
sprint:
  id: I-01
  title: "Protocolo JSON headless formalizado"
  touches:
    - path: nyx/cli.py
      reason: "Expandir run_headless() com novos message types"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "Nova fase headless_protocol com 4 testes"
  forbidden:
    - "Quebrar protocolo existente (ping, request, reset)"
  tests:
    - cmd: "./run.sh --gauntlet --only headless_protocol"
      timeout: 30
  acceptance_criteria:
    - "Headless responde status com info do agent"
    - "Headless responde tools com lista de nomes"
    - "Headless rejeita tipo desconhecido com error"
    - "Pipeline sequencial funciona (ping+status+tools+reset)"
    - "Acentuação PT-BR correta"
```

---

# Sprint I-01 -- Protocolo JSON headless

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** ALTA
**Tipo:** Feature
**Dependências:** P3-D (headless base)
**Desbloqueia:** I-02, I-03

---

## Problema / Contexto

O `--headless` do P3-D aceita apenas `ping`, `request`, `reset`.
Para integração Luna, o protocolo precisa ser mais completo.

## Implementação

Expandir `run_headless()` em `nyx/cli.py` com novos tipos de mensagem:

### Novos message types

| Tipo | Input | Output |
|------|-------|--------|
| `status` | `{"type": "status"}` | `{"type": "status", "tools": 19, "history": 0, "model": "qwen3:4b"}` |
| `tools` | `{"type": "tools"}` | `{"type": "tools", "list": ["read_file", "write_file", ...]}` |
| `session` | `{"type": "session"}` | `{"type": "session", "files_read": N, "files_modified": N, "iterations": N}` |
| desconhecido | `{"type": "xyz"}` | `{"type": "error", "message": "Tipo desconhecido: xyz"}` |

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| I1-01 | Headless status | tools >= 19, history == 0 |
| I1-02 | Headless tools list | lista contém "read_file" e "done" |
| I1-03 | Headless tipo desconhecido | type == "error" |
| I1-04 | Headless pipeline | ping + status + tools + reset em sequência |

## Verificação

- [ ] `echo '{"type":"status"}' | python -m nyx.cli --headless` retorna JSON válido
- [ ] `echo '{"type":"tools"}' | python -m nyx.cli --headless` retorna lista de tools
- [ ] Tipo desconhecido retorna error
- [ ] Pipeline sequencial funciona via subprocess
- [ ] Protocolo existente (ping, request, reset) inalterado
- [ ] Gauntlet completo continua passando

---

*"A simplicidade é a sofisticação suprema." -- Leonardo da Vinci*
