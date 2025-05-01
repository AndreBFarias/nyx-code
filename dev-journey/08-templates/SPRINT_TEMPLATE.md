## 0. SPEC (machine-readable)

```yaml
sprint:
  id: NNN
  title: "Título descritivo"
  touches:
    - path: caminho/arquivo.py
      reason: "Por que este arquivo é modificado"
  n_to_n_pairs: []
  forbidden: []
  tests:
    - cmd: "./run.sh --gauntlet --only FASE"
      timeout: 300
  acceptance_criteria:
    - "Critério 1"
    - "Critério 2"
    - "Acentuação PT-BR correta"
```

> Executar antes de começar: verificar estado atual do sistema

---

# Sprint NNN -- Título

**Status:** PENDENTE
**Data:** YYYY-MM-DD
**Prioridade:** ALTA/MÉDIA/BAIXA
**Tipo:** Feature/Bugfix/Refactor/Infra/Docs
**Dependências:** Sprint XX
**Desbloqueia:** Sprint YY

---

## Problema / Contexto

Descrição do que precisa ser resolvido e por quê.

## Implementação

### Fase 1: ...

### Fase 2: ...

## Verificação

- [ ] Critério 1
- [ ] Critério 2
- [ ] Gauntlet passa

---

*"Citação de filósofo." -- Autor*
