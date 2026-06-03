# Relatório LOOP-CONTEXT-WINDOW-AUDIT-01 — janela fixa de 4 mensagens em `_call_llm`

**Data:** 2026-06-03
**Tipo:** Auditoria + decisão + fix mínimo
**Onda:** 44 (auditoria das ondas 36-43)
**ADRs aplicáveis:** ADR-032 (a infra carrega o modelo), ADR-034 (feito para RTX 3050 4GB com desktop cheio), ADR-009 (qualidade de contexto faz parte da qualidade da resposta).

---

## 1. Pergunta da auditoria

A janela de 4 mensagens em `_call_llm` (`nyx/agent/loop/_iteration.py`) é deliberada ou acidental? Ela é a causa-raiz da alucinação de localização que as sprints 354/355 mitigam só por prompt? Decidir e implementar uma de três opções.

## 2. O que o código realmente faz (hipótese confirmada)

- `_call_llm` monta o contexto a partir de `self._session.to_messages()`. Quando `len(history_msgs) > 4`, envia apenas as 4 últimas. O ramo `elif self._budget.should_compact(...)` que existia logo abaixo era a suposta compactação local.
- A compactação efetiva roda antes, em `_run_iterations` (`nyx/agent/loop/_core.py`), que chama `should_compact` e `compact_history` a cada iteração, antes de `_call_llm()`.
- Ponto central, verificado por AST e por medição: o ramo `elif should_compact` em `_call_llm` é **logicamente inalcançável**. Quando há mais de 4 mensagens o `if len > 4` já captura; e `should_compact` só fica `True` por volta de ~50 turnos (medição abaixo), regime em que o `if` sempre vence. A docstring prometia "compactação se budget > 40%" que nunca rodava neste ponto.

## 3. Medição (classes reais, sem GPU, sem efeito colateral)

Probe construiu uma `CodeSession` real onde um arquivo (`nyx/agent/context.py`) é citado no 1º turno e a localização é perguntada num turno tardio (cenário exato do #354). `ContextBudget.max_tokens = 12000` (gatilho interno); `NUM_CTX` real do Ollama (janela de entrada) `= 4096`.

| turns | msgs | history_pct | should_compact | nível | últimas 4 (tok) | resumo compactado (tok) | opção B = resumo+4 (tok) | resumo cita o arquivo antigo? |
|------:|-----:|------------:|:--------------:|:-----:|----------------:|------------------------:|-------------------------:|:------------------------------|
| 2     | 10   | 0.026       | False          | 0     | 240             | 310                     | 550                      | sim (mas histórico já cabia inteiro) |
| 6     | 22   | 0.067       | False          | 0     | 240             | 809                     | 1049                     | sim (resumo cresce, não comprime)    |
| 12    | 40   | 0.130       | False          | 0     | 241             | 1561                    | 1802                     | sim (resumo cresce, não comprime)    |
| 25    | 79   | 0.267       | False          | 0     | 241             | 3202                    | 3443                     | sim, mas custa ~84% do num_ctx 4096  |
| 50    | 154  | 0.530       | True           | 1     | 241             | 264                     | 505                      | NÃO — `_compact_partial` omite a 1ª msg ("143 ações omitidas") |
| 90    | 274  | 0.951       | True           | 3     | 241             | 44                      | 285                      | coincidência do conteúdo, não confiável |

Leituras da tabela:

1. A janela de 4 **realmente corta a 1ª mensagem** (onde o arquivo foi citado). Confirma a causa-raiz da alucinação do #354. A mitigação 354/355 trata o sintoma, não a janela.
2. **Opção B (anexar o resumo às 4 recentes) é uma armadilha medida:** em conversa de 6 a 25 turnos `should_compact` é `False`, então `compact_history` devolve o histórico inteiro re-serializado, que **cresce sem comprimir** (até 3202 tokens, ~84% do `num_ctx` de 4096). Isso é exatamente o estouro de janela/latência que o ADR-034 manda não assumir. E quando a compactação enfim dispara (~50 turns, nível 1), o `_compact_partial` **descarta a 1ª msg** ("143 ações omitidas"), logo nem resolve a alucinação no regime onde ela mais importa.
3. **Compensação estrutural existente:** a memória de longo prazo barata já é reinjetada pelo `<system-reminder>` (`build_reminder` recebe `repo_map` + `session_summary` + `original_input`) via `_maybe_inject_reminder`, e não por `_call_llm`. Esse é o canal correto para memória, não a janela de mensagens.

## 4. Decisão: opção (c)

Manter a janela de 4 deliberadamente, **remover o branch morto** e **corrigir a docstring**, assumindo o trade-off por escrito.

Por quê, com base na medição e no risco:

- **(b) descartada por medição.** Custa até 84% do `num_ctx` em conversas médias sem comprimir e não preserva a citação antiga no regime longo. Mau custo-benefício e risco real de VRAM/latência (ADR-034).
- **(a) descartada por risco e escopo.** Janela adaptativa exige aumentar a entrada com proof de VRAM caro e instável (o `VALIDATOR_BRIEF` documenta flakiness reprodutível de OOM no RTX 3050). `NUM_CTX` é fixo em 4096 sem override de entrada; mexer nisso é refactor de orçamento, fora de uma auditoria.
- **(c) escolhida.** A janela de 4 é uma escolha de sobrevivência defensável para `num_ctx=4096` em GPU de 4GB. O branch é comprovadamente morto. A docstring mentia. A correção de fundo (a compactação que não injeta nada, a descalibração 12000 vs 4096) é refactor maior que o próprio spec manda virar sprint própria.

## 5. Fix aplicado (mínimo e cirúrgico)

Arquivo: `nyx/agent/loop/_iteration.py`, método `_call_llm`.

- Docstring reescrita para descrever o comportamento real (janela de 4 deliberada; memória via `<system-reminder>`) e registrar o trade-off + ponteiro para este relatório.
- Ramo `elif self._budget.should_compact(...)` removido. Resta `if len > 4: últimas 4` / `else: histórico completo`.
- A compactação real em `_run_iterations` (`_core.py`) ficou **intocada** (proibição explícita do spec).

## 6. Achados colaterais (não absorvidos — viram sprint nova)

Levantados aqui para registro; nenhum foi corrigido nesta sprint (protocolo "nenhum débito fica para trás").

- **AC-1 — `compact_history` tem retorno descartado em `_core.py`.** Em `_run_iterations`, `self._budget.compact_history(self._session)` é chamado só para calcular `tokens_removed` (telemetria do callback `_on_compaction`). O resumo produzido **não é reinjetado em lugar nenhum** do contexto enviado ao modelo, e `compact_history` não muta `session.history`. Na prática a "compactação real" é hoje um no-op de efeito sobre o contexto. Sprint sugerida: `LOOP-COMPACTION-SUMMARY-WIRING-01`.
- **AC-2 — descalibração de orçamento `ContextBudget` vs `NUM_CTX`.** `max_tokens = 12000` (interno) contra `NUM_CTX = 4096` (janela real do Ollama). O gatilho `should_compact` (> 40% de 12000 = 4800 tokens) só dispara por volta de ~50 turnos, bem depois de a janela real apertar. Sprint sugerida: `LOOP-CONTEXT-BUDGET-RECALIBRATE-01` (alinhar `max_tokens` ao `num_ctx` efetivo, possivelmente derivando do `detect_gpu`).

Ambos conectam-se à causa-raiz da alucinação de localização: se AC-1 for resolvido (resumo realmente reinjetado, preservando citações antigas) e AC-2 calibrado, a mitigação por prompt de 354/355 pode deixar de ser necessária. Fica como trabalho futuro, fora do escopo desta auditoria.

## 7. Proof-of-work

Ver bloco de proof na entrega do executor (invariantes 14/14, gauntlet rápido, medição reproduzida, acentuação e ruff nos arquivos tocados). O probe de medição é reproduzível e não tem efeito colateral nem dependência de GPU.

---

*"Tapar o sintoma com prompt é remédio; achar a janela curta é diagnóstico." — anônimo (epígrafe do spec)*
