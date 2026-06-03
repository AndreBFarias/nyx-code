# SPRINT LOOP-ACTIONTYPE-FALLBACK-DONE-01 — tool fora do enum vira ActionType.DONE no detector de repetição

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: LOOP-ACTIONTYPE-FALLBACK-DONE-01
  title: "tool_call cujo nome não está no enum ActionType cai em ActionType.DONE para detecção de repetição (semântica errada)"
  onda: 44
  bloco: "44 -- auditoria das ondas 36-43 (2026-06-03)"
  prioridade: BAIXA
  tipo: Bugfix / Core loop
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Em _execute_tool_calls (linha 170-173), o AgentAction usa `ActionType(name) if name in [a.value for a in ActionType] else ActionType.DONE`. multi_edit/skill/task_*/agent/ask_user/etc. NÃO estão no enum -> viram DONE no _check_repetition, distorcendo a detecção de repetição (e podendo mascarar repetição real de multi_edit)."
      linhas_alvo: "170-173"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Forçar todas as tools no enum ActionType (o enum é do parser/ações canônicas; nem toda tool registrada precisa estar lá)"
    - "Mudar a execução da tool (que usa `name` direto e está correta) -- o bug é só no `action_type` para repetição"
    - "Adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "probe determinístico: dois multi_edit consecutivos idênticos são detectados como repetição (não confundidos com DONE)"
      timeout: 60
      esperado: "detecção de repetição correta para tools fora do enum"

  acceptance_criteria:
    - "Tool fora do enum ActionType não é tratada como DONE no detector de repetição"
    - "Repetição real de multi_edit/skill/task_* é detectável (ou explicitamente isenta com justificativa)"
    - "done explícito continua sendo o único que conclui o turno"
    - "Invariantes 14/14, ruff/acento OK"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** auditoria das ondas 36-43 (achado A6, severidade BAIXA). Impacto prático baixo (o 3b raramente usa essas tools), mas é semântica de código incorreta.
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Contexto do projeto (snapshot — não referência)

> - O enum `ActionType` (models.py) cobre as ações canônicas do parser (read/write/edit/run/search/glob/list/analyze/patch/repl/web_*/todo_write/write_memory/mcp_tool/plugin_tool/done). Várias tools registradas NÃO têm valor no enum: `multi_edit`, `skill`, `task_create/update/list/get/output/stop`, `agent`, `ask_user`, `enter/exit_plan_mode`, `enter/exit_worktree`, `notebook_edit`, `send_message`, `brief`, `config`, `sleep`, `tool_search`.
> - 344 (TUI-AGENT-LOOP-CONVERGE-01) tornou o SKIP/FORCE_DONE eficaz; este achado é adjacente (a qualidade da entrada do detector).

---

## Problema

`_execute_tool_calls` (`_iteration.py:170-173`):

```python
action = AgentAction(
    action_type=ActionType(name) if name in [a.value for a in ActionType] else ActionType.DONE,
    params=args,
)
skip = self._check_repetition(action)
```

Quando o modelo chama uma tool fora do enum (ex.: `multi_edit`), o `action_type` vira `ActionType.DONE`. Isso é passado a `_check_repetition`/`get_skip_strategy`, que então raciocina sobre essas tools como se fossem `done`. Efeitos:
- repetição real de `multi_edit` (tool de escrita relevante) pode não ser detectada corretamente;
- diferentes tools fora do enum colapsam no mesmo `DONE`, confundindo `is_exact_repeat`/`is_in_recent`.

A **execução** está correta (usa `name` direto, `_iteration.py:210`); só a detecção de repetição recebe um `action_type` semanticamente errado.

---

## Solução proposta

Não forçar `DONE` para nomes desconhecidos. Opções (escolher a de menor risco):
- usar um sentinel/`ActionType` neutro que o detector trate como "ação opaca" identificada pelo `name` real (passar o `name` para o detector usar como chave), em vez de colapsar em `DONE`;
- ou estender `_check_repetition` para chavear por `name` quando o `action_type` não é canônico.

O importante: o `done` de verdade (que conclui o turno) só deve vir de `is_done(name)` (já tratado antes, `_iteration.py:129`), nunca de um fallback de nome desconhecido.

---

## Proof-of-work esperado (runtime real)

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/agent/loop/_iteration.py
# probe: 2x multi_edit idêntico -> _check_repetition retorna SKIP (não tratado como DONE/terminal)
```

---

## Critério binário de aceite

- [ ] Tool fora do enum não vira `DONE` no detector de repetição
- [ ] Repetição de tools fora do enum é detectável (ou isenta com justificativa)
- [ ] Conclusão de turno só via `is_done` real
- [ ] Invariantes 14/14, ruff/acento OK; spec movida para `concluidos/`

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Mexer no detector regride a convergência da 344 | Reusar o probe da 344 (sequências A/B/C) como teste de não-regressão |

---

*"Chamar tudo que não conheço de 'pronto' é como dar baixa no que nem comecei." -- anônimo*
