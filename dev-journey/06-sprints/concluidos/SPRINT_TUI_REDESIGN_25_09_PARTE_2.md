# SPRINT TUI-REDESIGN-25-09-PARTE-2 — Captura e Tab keybinding para thinking block

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-09-PARTE-2
  title: "Integração: captura de thinking no loop/_iteration + Tab keybinding no REPL"
  onda: 25
  bloco: 25.meta (parte 2 de TUI-REDESIGN-25-09)
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [TUI-REDESIGN-25-09]
  desbloqueia: []
  origem: "TUI-REDESIGN-25-09 implementou render_thinking_block (visual). Integração com loop (captura) e cli.py (keybinding Tab) ficou para esta sub-sprint."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Captura response.message.thinking (qwen3) ou surrogate (assistant text antes do tool call, qwen2.5-coder). Armazena em app_state['last_thinking_block']."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Keybinding Tab: se prompt vazio + last_thinking_block existe, alterna expanded/collapsed render."

  forbidden:
    - "Forçar field thinking em modelos sem suporte"
    - "Persistir thinking em log permanente"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "qwen3: thinking real capturado e renderizado collapsed"
    - "qwen2.5-coder: surrogate text capturado quando disponível"
    - "Tab no REPL com prompt vazio alterna estado expanded"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-09-PARTE-2

**Status:** CONCLUIDA (reconciliada em AUDIT-SPRINT-STATUS-RECONCILE-01 2026-06-02; captura real do thinking fechada em PARTE-3 commit b8516ab)
**Data criação:** 2026-05-18 (achado durante TUI-REDESIGN-25-09)
**Data conclusão:** 2026-05-18 (Tab keybinding feito; captura real do thinking extraída para PARTE-3 DEFERIDA — sincronizado em SPRINT_ORDER-REFRESH-01 2026-05-19)
**Modelo obrigatório:** claude-opus-4-7

## Contexto

A TUI-REDESIGN-25-09 implementou o helper visual `render_thinking_block`.
Falta:

1. **Captura** do conteúdo do thinking em `loop/_iteration.py`.
2. **Storage** em `app_state["last_thinking_block"] = {"text", "duration_s", "expanded"}`.
3. **Render automático** após resposta da Nyx (collapsed por default).
4. **Tab keybinding** em `cli.py` que alterna `expanded` e re-renderiza.

Captura é não-trivial: qwen3 expõe `thinking` no message; qwen2.5-coder não.
Para qwen2.5-coder, usar a última mensagem do assistant antes do tool call
como "thinking surrogate".

## Solução proposta

1. `loop/_iteration.py`: detectar `response.message.thinking` ou `response.message.content` quando seguido de tool_calls. Medir duração desde início da iteração. Setar em callback de "thinking captured".
2. `cli.py`: registra callback que recebe `{text, duration_s}`, armazena em `app_state` e chama `render_thinking_block(text, duration_s, expanded=False)`.
3. `cli.py` keybinding `Tab`:
   ```python
   @kb.add("tab")
   def _toggle_thinking(event):
       buf = event.current_buffer
       if buf.text.strip():
           return  # apenas com prompt vazio (não interfere completion)
       tb = app_state.get("last_thinking_block")
       if not tb:
           return
       tb["expanded"] = not tb.get("expanded", False)
       from prompt_toolkit.application import run_in_terminal
       run_in_terminal(lambda: render_thinking_block(
           tb["text"], tb["duration_s"], expanded=tb["expanded"]
       ))
   ```

## Critério binário

- [ ] Captura funcional com qwen3 (think real)
- [ ] Surrogate funcional com qwen2.5-coder
- [ ] Render auto após resposta
- [ ] Tab alterna estado
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-09-PARTE-2): captura e Tab keybinding para thinking`

## Invariantes

#14.

## Anti-débito

- Persistência ao longo de turnos múltiplos fora de escopo (só último bloco).
- Renderização inline durante streaming (em vez de após resposta) fica para sprint futura se demandado.

## Verificação

```bash
./run.sh --4b
# pedir "explique recursão em 3 passos"
# após resposta, ver linha "▶ pensando · Ns · prévia"
# digitar Tab (prompt vazio) → expande
# digitar Tab de novo → colapsa
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Captura é uma decisão; revelação é uma escolha." -- TUI-REDESIGN-25-09-PARTE-2*
