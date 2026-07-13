# Próxima sprint: INFRA-NEXT-SPRINT-STATUS-SUFFIX-01 (415)

> **NOTA (definido manualmente na auditoria 2026-07-12):** o gerador `scripts/update_next_sprint.py`
> está cego para a fila atual — o ROW_PATTERN não casa as linhas da ONDA-48 (status "PENDENTE (raiz)"
> e nome com sufixo parentetizado). A sprint 415 conserta exatamente isso; ao concluí-la, rode
> `python scripts/update_next_sprint.py` e este arquivo volta a ser gerado automaticamente.

**Spec:** `dev-journey/06-sprints/producao/SPRINT_INFRA_NEXT_SPRINT_STATUS_SUFFIX_01.md`

**Fila da ONDA-48 após a 415 (ordem sugerida; specs todas em `producao/`):**
1. 402 MEMORY-RECALL-REFRESH-01 (ALTA — V11 provado vivo na holística de 2026-07-12)
2. 406 TUI-INTERNALS-LEAK-01 (ALTA — V09)
3. 409 EXEC-CONTRACT-SEARCH-GLOB-OR-REGEX-01 (ALTA)
4. 413 EXEC-CONTRACT-PROXY-STATUS-BEFORE-JSON-01 (MEDIA)
5. 411, 410, 407, 408, 414, 403 (demais colaterais com spec pronta)
6. Bloco da auditoria 2026-07-12: 416-440 (ver `dev-journey/07-reports/AUDIT_2026_07_12.md` §3 e §5 para prioridade)

## Prompt

Sessão executora: siga o fluxo de 10 passos do `GSD.md` §"Fluxo completo de uma sprint" com a spec
`dev-journey/06-sprints/producao/SPRINT_INFRA_NEXT_SPRINT_STATUS_SUFFIX_01.md`. Leia também
`dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` (Catálogo Universal) e o `VALIDATOR_BRIEF.md`.

Rodar: `bash scripts/sprint_invariants.sh` antes e depois (regra binária FAIL_AFTER <= FAIL_BEFORE).
