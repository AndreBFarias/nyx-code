## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P-08
  title: "Session persistence + git ops"
  touches:
    - path: nyx/agent/persistence.py
      reason: "Salvar/carregar sessões"
    - path: nyx/agent/git_ops.py
      reason: "Sugerir commits, diff, status"
  acceptance_criteria:
    - "Sessão salva em JSON ao sair"
    - "Sessão restaurável ao iniciar"
    - "Sugestão de commit após modificações"
```

---

# Sprint P-08 -- Session Persistence + Git Ops

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Prioridade:** MEDIA
**Tipo:** Feature
**Dependências:** P-07

## Referência Luna

- `src/skills/code_agent/persistence.py`
- `src/skills/code_agent/git_ops.py`: suggest_commit()

---

*"O que não é registrado, não existiu." -- provérbio romano*
