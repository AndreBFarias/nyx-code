# SPRINT LOOP-CONTEXT-BUDGET-RECALIBRATE-01 — max_tokens=12000 vs num_ctx=4096 real

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-CONTEXT-BUDGET-RECALIBRATE-01
  title: "ContextBudget.max_tokens (12000) descalibrado do num_ctx real (4096); should_compact dispara tarde demais"
  onda: 44
  bloco: "44 -- achado colateral do exec 360 (LOOP-CONTEXT-WINDOW-AUDIT-01)"
  prioridade: MÉDIA
  tipo: Bugfix / Core loop
  dependencias: []
  desbloqueia: [LOOP-COMPACTION-SUMMARY-WIRING-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/context.py
      reason: "ContextBudget.max_tokens=12000 não reflete o num_ctx real (4096 no .env). should_compact (limiar relativo a max_tokens) só dispara ~50 turnos -- tarde demais para uma GPU 4GB."
      linhas_alvo: "max_tokens / should_compact"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "Fonte do num_ctx (NUM_CTX). max_tokens do budget deveria derivar dele (fonte única, ADR-013), não ser literal divergente."
      linhas_alvo: "NUM_CTX"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "O tamanho de contexto aparece como NUM_CTX (defaults/.env) e como max_tokens (ContextBudget); devem derivar de uma fonte."  # noqa-acento
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/context.py

  forbidden:
    - "Mudar o limiar de forma que a compactação dispare cedo demais e degrade chats curtos"
    - "Adicionar emoji ou menção a IA externa; sem print()"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "probe: should_compact dispara num número de turnos coerente com num_ctx real, não ~50"
      timeout: 60
      esperado: "limiar calibrado ao num_ctx"

  acceptance_criteria:
    - "max_tokens do ContextBudget deriva do num_ctx real (fonte única)"
    - "should_compact dispara em tempo coerente com a GPU 4GB (não tarde demais)"
    - "Chats curtos não sofrem compactação prematura"
    - "Invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** achado colateral 2 do executor da sprint 360 (RELATORIO_LOOP_CONTEXT_WINDOW_AUDIT_01.md §6). Não absorvido.
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Problema

A auditoria da 360 mediu: `ContextBudget.max_tokens=12000`, mas o `num_ctx` real (`.env`) é **4096**. Como `should_compact` compara o histórico contra `max_tokens`, a compactação só dispara por volta de **50 turnos** — tarde demais para uma GPU 4GB, onde o `num_ctx` real é 3× menor. O orçamento de contexto está descalibrado da janela real do modelo.

## Solução proposta

Derivar `max_tokens` do `num_ctx` real (fonte única, ADR-013) em vez de um literal 12000. Calibrar `should_compact` para disparar em tempo coerente com 4096, sem penalizar chats curtos. Pré-requisito útil para a 366 (LOOP-COMPACTION-SUMMARY-WIRING) — a compactação precisa disparar na hora certa para ter efeito.

## Proof-of-work esperado

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/context.py nyx/config/defaults.py
# probe: simular conversa crescente; should_compact dispara coerente com num_ctx (não ~50 turnos)
```

## Critério binário de aceite

- [ ] `max_tokens` deriva do `num_ctx` real
- [ ] `should_compact` calibrado; chats curtos intactos
- [ ] Invariantes 14/14; spec movida para `concluidos/`

---

*"Medir o copo grande quando o copo é pequeno é transbordar achando que sobra." -- anônimo*
