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

**Status:** PENDENTE
**Prioridade:** MEDIA
**Tipo:** Feature
**Dependências:** P-07

## Referência Luna

- `src/skills/code_agent/persistence.py`
- `src/skills/code_agent/git_ops.py`: suggest_commit()

---

*"O que não é registrado, não existiu." -- provérbio romano*
