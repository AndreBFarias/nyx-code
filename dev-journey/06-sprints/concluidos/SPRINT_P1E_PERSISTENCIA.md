## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P1-E
  title: "Persistência: Git Ops + Session Save"
  touches:
    - path: nyx/agent/git_ops.py
      reason: "Sugerir commits, status, diff (port Luna)"
    - path: nyx/agent/persistence.py
      reason: "Salvar/restaurar sessões em JSON (port Luna)"
  origin:
    primary:
      - "Luna/src/skills/code_agent/git_ops.py"
      - "Luna/src/skills/code_agent/persistence.py"
    reference: "openclaud/src/commands/commit.ts + openclaud/src/history.ts"
  acceptance_criteria:
    - "git_ops sugere commit message baseado em arquivos modificados"
    - "Sessão salva em ~/.nyx/sessions/ ao sair"
    - "Sessão restaurável ao iniciar"
```

---

# Sprint P1-E -- Persistência

**Status:** PENDENTE
**Prioridade:** MEDIA
**Tipo:** Port (Luna -> Nyx)
**Dependências:** P1-A
**Desbloqueia:** --

---

## O que portar

### 1. `nyx/agent/git_ops.py` (Luna: git_ops.py)

- `suggest_commit()` -- gera mensagem de commit baseada em diff
- `get_status()` -- git status formatado
- `get_diff()` -- git diff dos arquivos modificados

**Ajustes:** trocar imports, formato de commit PT-BR (GUIDE.md).

### 2. `nyx/agent/persistence.py` (Luna: persistence.py)

- Salvar sessão em JSON (`~/.nyx/sessions/`)
- Restaurar sessão anterior
- Limpar sessões antigas (>7 dias)

**Ajustes:** trocar `~/.luna` -> `~/.nyx`.

## Testes Gauntlet (novos, adicionados ao nyx_gauntlet.py)

Fase: `persistencia` (nova, 3 testes)

| ID | Nome | Validação |
|----|------|-----------|
| PS-01 | Git status | git_ops.get_status() retorna string não vazia |
| PS-02 | Session save | persistence.save_session() cria arquivo em ~/.nyx/sessions/ |
| PS-03 | Session load | persistence.load_session() restaura sessão salva |

## Verificação

- [ ] 3 testes de persistência passam no Gauntlet
- [ ] `./run.sh --gauntlet --only persistencia` passa 100%
- [ ] Gauntlet completo continua passando 100%

---

*"O que não é registrado, não existiu." -- provérbio romano*
