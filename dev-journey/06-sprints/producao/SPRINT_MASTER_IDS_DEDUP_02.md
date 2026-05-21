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

**Status:** CONCLUIDA (2026-05-21, sem-mudancas-necessarias)
**Data criação:** 2026-05-21
**Data conclusão:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

Listar:
```bash
grep -hE '^\s+id:' dev-journey/06-sprints/concluidos/*.md | sort | uniq -d
```

Para cada duplicado, renomear o id YAML da spec mais nova adicionando sufixo descritivo (ex.: `-PHASE-2`, `-FIX`, `-DEFAULT-PAD`).

## Critério binário

- [x] uniq -d retorna 0 sobre headers YAML
- [x] Smoke + invariantes 14/14
- [x] Acentuação rc=0 nos arquivos modificados

## Proof-of-work (2026-05-21)

Resultado da varredura na execução da sprint: **0 IDs YAML duplicados** em
`dev-journey/06-sprints/concluidos/*.md`. O caso conhecido
`TUI-REDESIGN-26-03-PARTE-2-DEFAULT-PAD` vs `TUI-REDESIGN-26-03-PARTE-2` foi
resolvido inline em commit `df1a8d9` (TUI-REDESIGN-26-03-PARTE-2 PARTE 2),
deixando esta sprint sem trabalho residual.

### Comandos rodados

```bash
# 1) Varredura de duplicados (acceptance criterion principal)
$ grep -hE '^\s+id:' dev-journey/06-sprints/concluidos/*.md | sort | uniq -d
# (saída vazia — 0 linhas, conforme critério)

# 2) Variante normalizada (extrai valor do id, robusta a indentação)
$ grep -RHE '^\s+id:\s+[A-Z]' dev-journey/06-sprints/concluidos/ \
    | awk -F'id:' '{gsub(/^[[:space:]]+|[[:space:]]+$/, "", $2); print $2}' \
    | sort | uniq -d
# (saída vazia)

# 3) Confirmação do caso histórico resolvido
$ grep -rHnE '^\s+id:\s+TUI-REDESIGN-26-03-PARTE-2' dev-journey/06-sprints/concluidos/
dev-journey/06-sprints/concluidos/SPRINT_TUI_REDESIGN_26_03_PARTE_2.md:7:  id: TUI-REDESIGN-26-03-PARTE-2
dev-journey/06-sprints/concluidos/SPRINT_TUI_REDESIGN_26_03_PARTE_2_DEFAULT_PAD.md:7:  id: TUI-REDESIGN-26-03-PARTE-2-DEFAULT-PAD

# 4) Smoke boot
$ ./run.sh --smoke
boot ok

# 5) Invariantes
$ bash scripts/sprint_invariants.sh
PASS: 14
FAIL: 0
Sprint invariantes OK.
```

### IDs renomeados nesta sprint

Nenhum. Critério satisfeito a partir de trabalho prévio. Para histórico:
o único par duplicado conhecido (TUI-REDESIGN-26-03-PARTE-2-DEFAULT-PAD vs
TUI-REDESIGN-26-03-PARTE-2) já havia sido renomeado em commit df1a8d9
ANTES da promoção desta sprint. Inventário pós-execução de
`dev-journey/06-sprints/concluidos/*.md` = 377 arquivos, 0 duplicados.
