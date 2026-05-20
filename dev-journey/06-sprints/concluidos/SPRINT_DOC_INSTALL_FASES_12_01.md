# SPRINT DOC-INSTALL-FASES-12-01 -- Atualizar README.md para 12 fases (pós INFRA-INSTALL-ZSTD-FALLBACK-01)

## 0. SPEC

```yaml
sprint:
  id: DOC-INSTALL-FASES-12-01
  title: "README.md atualizado de '11 fases' para '12 fases' (FASE 3 zstd inserida)"
  onda: 24
  bloco: 24.5 Release (anti-débito de INFRA-INSTALL-ZSTD-FALLBACK-01)
  prioridade: BAIXA
  tipo: Docs
  dependencias: [INFRA-INSTALL-ZSTD-FALLBACK-01]
  desbloqueia: []

  touches:
    - path: README.md
      reason: "Linha 30: 'lista completa das 11 fases' -> '12 fases'; Linha 360: 'A FASE 12' continua sendo a fase de ícones (era 12 antes da renumeração, continua 12 após)"

  creates: []
  removes: []

  forbidden:
    - "Modificar conteúdo semântico do README além das 2 linhas com contagem desatualizada"

  tests:
    - cmd: "grep -c '11 fases' README.md"
      timeout: 5
      deve_passar: "exit 1 (zero ocorrências)"
    - cmd: "grep -c '12 fases' README.md"
      timeout: 5
      deve_passar: "exit 0 (>=1)"

  acceptance_criteria:
    - "README.md não tem mais menção a '11 fases'"
    - "README.md menciona '12 fases'"
    - "Texto sobre FASE 12 (ícones) explicitamente nota a renumeração via INFRA-INSTALL-ZSTD-FALLBACK-01"
```

---

**Status:** CONCLUIDA (2026-05-19)
**Data:** 2026-05-19
**Modelo:** claude-opus-4-7 (sessão validador/integrador/despachador)

## Contexto

Anti-débito de INFRA-INSTALL-ZSTD-FALLBACK-01 (commit `028d06e`). A nova FASE 3 do install.sh renumerou TOTAL=11 → TOTAL=12. README.md tinha duas linhas com contagem antiga:
- Linha 30: "lista completa das 11 fases"
- Linha 360: "A FASE 12 do install.sh copia ícones"

Note que FASE 12 continua sendo ícones (antes era índice 11 → agora 12 após shift). A nota de renumeração é discreta para futura referência.

## Implementação

Edit cirúrgico de 2 linhas:
1. Linha 30: `11 fases` → `12 fases (0..12)`
2. Linha 360: `A FASE 12 do install.sh` → `A FASE 12 (última, após INFRA-INSTALL-ZSTD-FALLBACK-01) do install.sh`

## Proof-of-work

```
[pre]
grep -n "11 fases\|FASE 1[12]" README.md
→ linha 30: "11 fases"; linha 360: "FASE 12"

[edit]
2 Edit cirúrgicos (texto único, sem reordenação)

[pos]
grep -c "11 fases" README.md → 0
grep -c "12 fases" README.md → 1
./run.sh --smoke → boot ok
bash scripts/sprint_invariants.sh → PASS 14/14
```

## Touches

- `README.md` (+2 edits cirúrgicos, sem outras alterações)

---

*"A documentação envelhece junto com o código." -- DOC-INSTALL-FASES-12-01*
