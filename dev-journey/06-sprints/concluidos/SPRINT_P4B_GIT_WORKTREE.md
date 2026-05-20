## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P4-B
  title: "Git Worktree -- EnterWorktree, ExitWorktree"
  touches:
    - path: nyx/agent/tools/worktree.py
      reason: "Novas tools: git worktree create/cleanup"
    - path: nyx/agent/tools/registry.py
      reason: "Registrar 2 novas tools"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "2 testes novos"
  origin:
    primary: "openclaud/src/tools/EnterWorktreeTool/"
    secondary: "openclaud/src/tools/ExitWorktreeTool/"
  tests:
    - cmd: "./run.sh --gauntlet --only p4_worktree"
      timeout: 30
  acceptance_criteria:
    - "EnterWorktreeTool cria worktree isolada"
    - "ExitWorktreeTool limpa worktree"
    - "Worktree usa branch temporária"
    - "Cleanup remove diretório e branch"
```

---

# Sprint P4-B -- Git Worktree

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-05
**Prioridade:** MÉDIA
**Tipo:** Port (TS -> Python)
**Dependências:** P4-A
**Desbloqueia:** P4-D

---

## Implementação

### 1. EnterWorktreeTool (`nyx/agent/tools/worktree.py`)
- Cria branch `nyx-worktree-{timestamp}`
- `git worktree add /tmp/nyx-wt-{ts} -b nyx-worktree-{ts}`
- Retorna path da worktree criada
- Muda project_root do agent para a worktree

### 2. ExitWorktreeTool (mesmo arquivo)
- `git worktree remove /tmp/nyx-wt-{ts}`
- `git branch -d nyx-worktree-{ts}` (se sem mudanças)
- Restaura project_root original
- Se há mudanças, retorna diff para o agente decidir

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P4W-01 | EnterWorktree cria | Diretório existe, branch criada |
| P4W-02 | ExitWorktree limpa | Diretório removido, branch removida |

## Verificação

- [ ] Worktree cria e limpa corretamente
- [ ] Branch temporária removida no exit
- [ ] Funciona em repos com uncommitted changes
- [ ] 2 testes Gauntlet passando

---

*"Cada problema contém a semente de sua solução." -- Norman Vincent Peale*
