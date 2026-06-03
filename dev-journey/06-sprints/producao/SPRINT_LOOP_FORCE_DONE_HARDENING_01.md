# SPRINT LOOP-FORCE-DONE-HARDENING-01 — FORCE_DONE conclui sem checar artefato + summary frágil

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-FORCE-DONE-HARDENING-01
  title: "FORCE_DONE por repetição (344) ignora o guard de artefato (351); _build_force_done_summary depende de string literal frágil"
  onda: 44
  bloco: "44 -- auditoria das ondas 36-43 (2026-06-03)"
  prioridade: BAIXA
  tipo: Bugfix / Core loop
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "(A7) _check_repetition -> SkipStrategy.FORCE_DONE (linha 366-373) conclui o turno SEM passar pelo _should_reject_done (351, que só intercepta o done EXPLÍCITO em _execute_tool_calls/_execute_parsed_action). Em turno intent=code sem nenhum write, o FORCE_DONE entrega um 'done alucinado' por outra porta."
      linhas_alvo: "366-373 (branch FORCE_DONE); 104-111 (_should_reject_done)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "(A8) _build_force_done_summary (linha 421-436) faz `entry.tool_result.split('. Se a tarefa')[0]` -- depende de uma string literal exata; se a mensagem mudar, retorna o texto inteiro silenciosamente."
      linhas_alvo: "421-436"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Transformar o FORCE_DONE em loop infinito (ele é a rede contra MAX_ITERATIONS; o guard de artefato deve agir no máximo 1x, como o 351)"
    - "Reverter a convergência da 344"
    - "Adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "probe determinístico: turno intent=code que repete read_file sem nunca escrever -> FORCE_DONE NÃO declara arquivo criado (summary honesto); com mensagem de tool diferente, _build_force_done_summary não devolve lixo"
      timeout: 60
      esperado: "summary honesto e robusto a mudança de texto"

  acceptance_criteria:
    - "FORCE_DONE em turno que queria criar/escrever e não escreveu nada produz summary honesto (não afirma artefato inexistente)"
    - "_build_force_done_summary não depende de string literal exata (parsing robusto)"
    - "Convergência da 344 intacta (sequências A/B/C ainda convergem)"
    - "Invariantes 14/14, ruff/acento OK"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** auditoria das ondas 36-43 (achados A7 e A8, severidade BAIXA, agrupados por coesão — ambos no caminho do FORCE_DONE).
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> - 344 (TUI-AGENT-LOOP-CONVERGE-01): o loop converge via `SkipStrategy.FORCE_DONE` quando há repetição.
> - 351 (LOOP-DONE-VERIFY-ARTIFACTS-01): `_should_reject_done` rejeita 1x o `done` quando o turno pediu criar/escrever e nenhum write efetivou — mas só intercepta o `done` EXPLÍCITO.
> - ADR-033 A cadeia nunca quebra / honestidade: o summary não pode afirmar o que não aconteceu.

---

## Problema

**A7 — gap done-guard × FORCE_DONE.** O `_should_reject_done` (`_iteration.py:104-111`) só é consultado nos pontos de `done` explícito (`_execute_tool_calls:130`, `_execute_parsed_action:270`). O `FORCE_DONE` por repetição (`_check_repetition`, `_iteration.py:366-373`) retorna `SessionStatus(DONE, ...)` direto, **sem** passar pelo guard. Então um turno `intent=code` em que o modelo só repete `read_file`/`list_files` e nunca escreve pode terminar em `FORCE_DONE` — o "done alucinado" que a 351 combate, voltando por outra porta.

**A8 — summary frágil.** `_build_force_done_summary` (`_core.py:426`):

```python
parts.append(entry.tool_result.split(". Se a tarefa")[0])
```

Depende da substring literal `". Se a tarefa"`. Se a mensagem da tool mudar, o `split` devolve o texto inteiro sem aviso (quebra muda).

---

## Solução proposta

**A7:** antes de o `FORCE_DONE` concluir, consultar o estado do guard (mesma lógica de `_should_reject_done`): se o turno queria criar/escrever e nada efetivou, o summary deve dizer a verdade ("não consegui criar X; repeti <ação> N vezes sem escrever") em vez de implicar sucesso. Não bloquear o FORCE_DONE (ele é a rede anti-MAX_ITERATIONS), mas tornar o desfecho **honesto** (ADR-033). Reusar `_turn_wants_create`/`_turn_writes_baseline`.

**A8:** trocar o `split(". Se a tarefa")[0]` por parsing robusto (ex.: regex tolerante ou usar o campo estruturado do `ActionResult`/`HistoryEntry` em vez de fatiar a mensagem renderizada).

---

## Proof-of-work esperado (runtime real)

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py nyx/agent/loop/_core.py
# probe: (A7) turno intent=code repetindo read_file sem write -> FORCE_DONE com summary honesto
#        (A8) tool_result sem ". Se a tarefa" -> _build_force_done_summary não devolve a string crua inteira
#        (regressão) sequências A/B/C da 344 ainda convergem
```

---

## Critério binário de aceite

- [ ] FORCE_DONE em turno sem write esperado produz summary honesto
- [ ] `_build_force_done_summary` robusto a mudança de texto da tool
- [ ] Convergência da 344 intacta
- [ ] Invariantes 14/14, ruff/acento OK; spec movida para `concluidos/`

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Guard no FORCE_DONE vira loop | Agir no máximo 1x (espelhar `_done_rejected` da 351); FORCE_DONE ainda fecha o turno |
| Mudar o summary regride KPIs do gauntlet | Rodar `--only rapido` + probe da 344 |

---

*"Forçar o fim é aceitável; mentir sobre o fim, não." -- paráfrase do ADR-033*
