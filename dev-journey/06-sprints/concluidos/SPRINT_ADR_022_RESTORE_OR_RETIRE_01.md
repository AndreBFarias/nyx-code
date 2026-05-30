# SPRINT 296 — ADR-022-RESTORE-OR-RETIRE-01

## 0. SPEC

```yaml
sprint:
  id: ADR-022-RESTORE-OR-RETIRE-01
  title: "Investigar a suspeita da auditoria ONDA-34 de que ADR_022_VISION_MOONDREAM_CPU.md foi deletado por engano na ONDA-32 (commit ef79c17), e decidir restaurar ou formalizar aposentadoria"
  onda: 34
  prioridade: BAIXA
  tipo: Decisão/Investigação
  dependencias: []
  desbloqueia: []

  origem: "Item da matriz de auditoria ONDA-34 (plano redesign, linha 44/93): 'ADR_022_VISION_MOONDREAM_CPU.md DELETADO junto na ONDA-32 (suspeito)' — flag INVESTIGAR."

  touches: []
  creates: []
  removes: []

  forbidden:
    - "Restaurar o arquivo obsoleto ADR_022_VISION_MOONDREAM_CPU.md — sua remoção foi intencional (dedup da SPRINT 261)"
    - "Tocar o ADR-022 canônico (ADR_022_MOONDREAM.md, ACEITO)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Confirmar que a deleção de ADR_022_VISION_MOONDREAM_CPU.md foi INTENCIONAL (dedup), não perda de dado"
    - "Confirmar que o ADR-022 canônico (ADR_022_MOONDREAM.md) está presente, ACEITO e sem referências quebradas"
    - "Decisão: nenhuma ação (nem restaurar nem aposentar) — já resolvido pela SPRINT 261"
```

## 1. INVESTIGAÇÃO (CONCLUIDA — 2026-05-30)

**Suspeita do plano (29/mai):** `ADR_022_VISION_MOONDREAM_CPU.md` teria sido deletado por
engano na migração Textual (ef79c17, ONDA-32), causando perda do ADR-022.

**Achado: a suspeita tinha premissa stale — já resolvido pela SPRINT 261 (2026-05-26).**

Histórico git reconstruído:
- `git show ef79c17 --diff-filter=D` confirma a deleção de `ADR_022_VISION_MOONDREAM_CPU.md`,
  **mas a própria mensagem do commit a rotula:** `"261 ADR_022_DEDUP -- mantem ADR_022_MOONDREAM (Ollama)"`.
- A **SPRINT 261 (ADR-022-DEDUP-01)** já havia diagnosticado e corrigido: existiam **dois**
  arquivos ADR-022 com nomes invertidos. Decisão (registrada no MASTER L722):
  - `ADR_022_MOONDREAM.md` (2026-05-17, origem 843977a VISION-01; Ollama `/api/generate`
    `num_gpu=0` + qwen2.5-coder:3b; aponta vision_client.py/vision_service.py) = **CANÔNICO, mantido**.
  - `ADR_022_VISION_MOONDREAM_CPU.md` (2026-04-19, origem 70063ca; transformers/HuggingFace
    moondream2 + qwen3:4b) = **OBSOLETO, removido via git rm** (premissas qwen3/transformers
    poluiriam o doc da impl atual; git preserva em 70063ca).
  - README `ADRs (32)→(31)`, `sync.py _check_adrs` 32→31 sem gap.

**Estado atual verificado:**
- `ADR_022_MOONDREAM.md`: rastreado, 65 linhas, `Status: ACEITO`, título "Visão via moondream em CPU puro".
- Referências a ADR-022 no repo (ADR-021, VISION-01, templates, MASTER) citam por **número**
  e resolvem todas ao arquivo canônico presente — **zero links quebrados** por nome.

**Decisão: NENHUMA AÇÃO.** Nem restaurar (a remoção foi dedup intencional, não perda) nem
aposentar (o canônico está ACEITO e em uso). O item de auditoria ONDA-34 estava obsoleto —
a 261 já o havia resolvido antes do plano ser escrito; o autor do plano não tinha o 261 em vista.

**Validação:** sprint de investigação, zero arquivo tocado. `bash scripts/sprint_invariants.sh`
14/14 (FAIL=0). Gauntlet N/A.
