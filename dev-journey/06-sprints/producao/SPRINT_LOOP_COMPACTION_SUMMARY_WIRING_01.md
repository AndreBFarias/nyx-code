# SPRINT LOOP-COMPACTION-SUMMARY-WIRING-01 — compact_history tem retorno descartado (no-op de contexto)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-COMPACTION-SUMMARY-WIRING-01
  title: "compact_history calcula resumo mas o retorno é descartado e não muta a sessão; o resumo nunca chega ao modelo"
  onda: 44
  bloco: "44 -- achado colateral do exec 360 (LOOP-CONTEXT-WINDOW-AUDIT-01)"
  prioridade: MÉDIA
  tipo: Bugfix / Core loop
  dependencias: [LOOP-CONTEXT-WINDOW-AUDIT-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Em _run_iterations (~linha 293-303) chama self._budget.compact_history(self._session) mas DESCARTA o retorno; só usa pct_before/after para telemetria. O resumo não é reinjetado no contexto enviado ao modelo."
      linhas_alvo: "293-303"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/context.py
      reason: "compact_history não muta session.history nem expõe o resumo de forma consumível pelo _call_llm."
      linhas_alvo: "compact_history"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Estourar VRAM no cenário-alvo RTX 3050 4GB (ADR-034) -- o resumo reinjetado deve ser CURTO"
    - "Adicionar emoji ou menção a IA externa; sem print()"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      esperado: "APROVADO"
    - cmd: "probe: após compactação, o contexto enviado por _call_llm contém o resumo (não só as 4 últimas)"
      timeout: 60
      esperado: "resumo presente no payload"

  acceptance_criteria:
    - "O resumo de compact_history é efetivamente reinjetado no contexto enviado ao modelo (ou a sessão é mutada de forma que to_messages o reflita)"
    - "Em conversa longa, o modelo recebe memória de longo prazo barata em tokens, sem estourar o num_ctx real"
    - "Invariantes 14/14, gauntlet rápido APROVADO"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** achado colateral 1 do executor da sprint 360 (RELATORIO_LOOP_CONTEXT_WINDOW_AUDIT_01.md §6). Não absorvido.
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Problema

A auditoria da 360 descobriu que a "compactação real" em `_run_iterations` (`_core.py:293-303`) chama `compact_history` mas **descarta o retorno** — só calcula `tokens_removed` para telemetria. `compact_history` **não muta** `session.history`, e o resumo **nunca é reinjetado** no contexto enviado ao modelo. Combinado com a janela fixa de 4 mensagens (`_call_llm`, decisão da 360), isso significa que em conversa longa o modelo **só vê 4 mensagens, ponto** — a compactação é um no-op de efeito sobre o contexto. É a raiz de fundo da alucinação de contexto longo que 354/355 mitigam por prompt.

## Solução proposta

Fazer o resumo de `compact_history` efetivamente chegar ao modelo: reinjetar o resumo (curto) no payload de `_call_llm` além das 4 recentes, OU mutar a sessão de forma que `to_messages()` reflita o histórico compactado. O resumo precisa ser CURTO (ADR-034: não estourar o `num_ctx` real de 4096). Coordenar com LOOP-CONTEXT-BUDGET-RECALIBRATE-01 (367) para que a compactação dispare na hora certa.

## Proof-of-work esperado

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
./run.sh --gauntlet --only rapido                       # APROVADO
# probe: conversa >= 12 turnos; após compactação, o payload de _call_llm contém o resumo;
#        medir tokens de input (não estourar 4096) e VRAM (nvidia-smi).
```

## Critério binário de aceite

- [ ] O resumo compactado chega ao modelo (probe prova)
- [ ] Tokens de input não estouram o num_ctx real; VRAM estável no cenário-alvo
- [ ] Invariantes 14/14, gauntlet rápido APROVADO; spec movida para `concluidos/`

---

*"Resumir e jogar o resumo fora é trabalho que finge ter acontecido." -- anônimo*
