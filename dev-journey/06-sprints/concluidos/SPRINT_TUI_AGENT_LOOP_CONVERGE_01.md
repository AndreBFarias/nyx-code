# SPRINT TUI-AGENT-LOOP-CONVERGE-01 — agent loop converge (SKIP real via sentinel)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-AGENT-LOOP-CONVERGE-01
  title: "SkipStrategy.SKIP volta a pular de verdade; o loop converge por FORCE_DONE em vez de rodar até MAX_ITERATIONS"
  onda: 40
  bloco: "40 -- bugs de runtime (achados na auditoria 2026-06-02)"
  prioridade: ALTA
  tipo: Bugfix / Core loop
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "SkipStrategy.SKIP retornava None; os callers (caminho de tool_calls nativo e parser fallback) só agem em valor truthy, então a tool executava mesmo (skip morto desde o port) e o `_consecutive_skips = 0` pós-execução zerava o contador, impedindo a convergência por FORCE_DONE (loop até MAX_ITERATIONS=50)."
      linhas_alvo: "47 (sentinel _SKIP_ACTION), 147-148 e 276-277 (os 2 callers), 351 (return do branch SKIP)"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Mexer no reset de _consecutive_skips ou na heurística de get_skip_strategy (fix mínimo, menor risco no loop core)"
    - "Marcar SKIP via flag booleana -- None já significa 'continuar/sem terminal'; precisa de sentinel de identidade distinto"
    - "Adicionar emoji ou menção a IA"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS (inclui #13 smoke boot ok, #10 ruff, #1 zero emoji)"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 300
      esperado: "APROVADO (19/19, qwen2.5-coder:3b)"
    - cmd: "probe determinístico com get_skip_strategy real (/tmp/converge_probe.py)"
      timeout: 30
      esperado: "com fix: SEQ A/B/C convergem (FORCE_DONE); sem fix: SEQ B/C rodam até MAX sem convergir"

  acceptance_criteria:
    - "Repetição de ação (exact/semantic/in_recent) com has_results=True força DONE em <=3 ações em vez de MAX_ITERATIONS=50"
    - "GSD progress.md de run real registra desfecho 'done' com iter << 50 para o prompt que antes loopava"
    - "Invariantes 14/14, gauntlet rápido APROVADO, acento rc=0, AST/import OK"
```

---

**Status:** CONCLUIDA (ver SPRINT_ORDER_MASTER ONDA-40, sprint 344)
**Data criação:** 2026-06-02
**Origem:** auditoria de runtime no `--web` a pedido do dono ("qual feature implementada não funciona"). Mandando o prompt real `leia o arquivo nyx/__version__.py e me diga qual a versao`, a Nyx **acionava `read_file`** (o proxy extrai o tool_call do content do 3b, ADR-032), lia `1.3.4`, mas **re-executava `read_file` repetidamente** (mesmo arquivo, depois path errado `/Nyx/`) presa em "pensando..." sem emitir resposta final. O `RepetitionDetector` existe na arquitetura mas não estava cortando.
**Modelo obrigatório:** claude-opus (sem subagentes)

## 1. Causa-raiz

Em `_check_repetition`, o branch `SkipStrategy.SKIP` logava "Ação repetida ignorada" e incrementava `_consecutive_skips`, mas **retornava `None`**. Os dois callers (`_execute_tool_calls` nativo e `_execute_parsed_action` parser) só agem com `if skip: return skip` — e `None` é falsy. Logo a tool **executava mesmo assim**, e ao final da execução o `self._consecutive_skips = 0` **zerava o contador**. Como `get_skip_strategy` só força DONE quando `consecutive_skips >= 1 and has_results` (ou `>= 3`, ou `is_cycle`), o contador nunca acumulava → o loop só terminava por MAX_ITERATIONS. **O SKIP estava funcionalmente morto desde o port.**

## 2. Fix

Sentinel de identidade `_SKIP_ACTION = object()` retornado pelo branch SKIP. Os dois callers checam `if skip is _SKIP_ACTION: return None` **antes** do `if skip:` truthy — assim a iteração pula a execução e continua o loop (return None) **sem** passar pelo reset. O `_consecutive_skips` persiste e a pressão para FORCE_DONE acumula. Mudança cirúrgica de 4 pontos, sem tocar no reset nem na heurística.

Trace pós-fix (sequência exata observada em runtime): leitura #1 (CONTINUE, `has_results=True`) → leitura #2 idêntica (`is_exact_repeat` → SKIP real, `consecutive_skips=1`) → 3ª ação (`consecutive_skips>=1 and has_results` → **FORCE_DONE**). Converge na 3ª iteração.

## 3. Proof-of-work (runtime real)

- **Invariantes:** 14/14 PASS (inclui #13 `./run.sh --smoke` = boot ok, #10 ruff, #1 zero emoji).
- **Gauntlet rápido:** 19/19 APROVADO (qwen2.5-coder:3b).
- **Acento** `_iteration.py`: rc=0. **AST** OK. **import** `_SKIP_ACTION` OK.
- **Probe determinístico** (funções reais de `repetition.py`, contabilidade do loop fielmente replicada): com o fix, repetição pura (SEQ A), a sequência observada `P1,P1,P2,P2,list,P2` (SEQ B) e o pior caso de path sempre diferente (SEQ C) **todas convergem** por FORCE_DONE (iter 3/3/6); **sem** o fix, SEQ B e C rodam até MAX sem convergir — reproduzindo o sintoma.
- **Run real (fix ativo, GSD):** o mesmo prompt terminou `done iter=7` (rótulo "done", muito abaixo de MAX_ITERATIONS=50) — ausência do sintoma "loop até o teto".

## 4. Notas

- A robustez da *detecção* sob paths de representação variável (o 3b alterna `nyx/...` e `/Nyx/...`) é separada: o fix garante convergência assim que a repetição é detectada por qualquer das 3 camadas (exact/semantic/in_recent). SEQ C prova que mesmo no pior caso o teto de `consecutive_skips >= 3` / `is_cycle` ainda fecha.
- A anotação de tipo de `_check_repetition` permanece `SessionStatus | None`; o sentinel é tratado por identidade nos callers antes de qualquer uso como `SessionStatus`.
