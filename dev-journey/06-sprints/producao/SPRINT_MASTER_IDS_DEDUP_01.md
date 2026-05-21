# SPRINT MASTER-IDS-DEDUP-01 — Deduplicação de IDs numéricos no MASTER

## 0. SPEC

```yaml
sprint:
  id: MASTER-IDS-DEDUP-01
  title: "Renumerar 22 IDs numéricos duplicados no SPRINT_ORDER_MASTER.md"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: BAIXA
  tipo: Refactor doc
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Coluna ID — renumerar entries pós-150 para serem únicas, preservando chaves textuais"

  forbidden:
    - "Mexer em status / links / dependencias / descrição das entries (só coluna ID)"
    - "Renumerar entries pré-150 (estável historicamente)"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"

  acceptance_criteria:
    - "awk -F'|' '/^\\| [0-9]+/{gsub(/ /,\"\",$2); print $2}' MASTER | sort -n | uniq -d retorna 0 linhas"
    - "Todas as 377 sprints concluídas preservam suas chaves textuais (IDs ALPHANUM como TUI-REDESIGN-X)"
    - "Smoke + invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

Comando para listar duplicados:
```bash
awk -F'|' '/^\| [0-9]+/{gsub(/ /,"",$2); print $2}' dev-journey/06-sprints/SPRINT_ORDER_MASTER.md | sort -n | uniq -d
```

Para cada duplicado, atribuir novo ID acima do max atual (vai usar séries 200+ pra não conflitar).

## Critério binário

- [ ] uniq -d retorna 0 linhas
- [ ] Smoke + invariantes 14/14
- [ ] Acentuação rc=0
