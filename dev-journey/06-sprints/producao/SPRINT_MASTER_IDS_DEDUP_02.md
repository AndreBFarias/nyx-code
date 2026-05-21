# SPRINT MASTER-IDS-DEDUP-02 — Deduplicação de IDs YAML em specs concluídas

## 0. SPEC

```yaml
sprint:
  id: MASTER-IDS-DEDUP-02
  title: "Renomear IDs YAML duplicados em dev-journey/06-sprints/concluidos/*.md"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: BAIXA
  tipo: Refactor doc
  dependencias: [MASTER-IDS-DEDUP-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/concluidos/*.md
      reason: "IDs YAML duplicados entre specs com mesmo `id:` em arquivos diferentes"

  forbidden:
    - "Mexer em status / proof-of-work / descrição das specs (só linha do `id:` YAML)"
    - "Renomear filenames (gera ruído git mv)"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"

  acceptance_criteria:
    - "grep -hE '^\\s+id:' dev-journey/06-sprints/concluidos/*.md | sort | uniq -d retorna 0 linhas"
    - "Pelo menos TUI-REDESIGN-26-03-PARTE-2-DEFAULT-PAD vs TUI-REDESIGN-26-03-PARTE-2 corrigido (já feito inline em commit df1a8d9 — verificar)"
    - "Smoke + invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

Listar:
```bash
grep -hE '^\s+id:' dev-journey/06-sprints/concluidos/*.md | sort | uniq -d
```

Para cada duplicado, renomear o id YAML da spec mais nova adicionando sufixo descritivo (ex.: `-PHASE-2`, `-FIX`, `-DEFAULT-PAD`).

## Critério binário

- [ ] uniq -d retorna 0 sobre headers YAML
- [ ] Smoke + invariantes 14/14
- [ ] Acentuação rc=0 nos arquivos modificados
