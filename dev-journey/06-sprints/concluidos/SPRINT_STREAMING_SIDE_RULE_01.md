# SPRINT STREAMING-SIDE-RULE-01 — Faixa lateral │ em cada linha da resposta streamada

## 0. SPEC

```yaml
sprint:
  id: STREAMING-SIDE-RULE-01
  title: "on_token wrap line-by-line para prefixar SIDE_RULE_NYX em cada linha durante streaming"
  onda: 25
  bloco: 25.meta (parte 2 de TUI-REDESIGN-25-08)
  prioridade: MÉDIA
  tipo: UX+Refactor
  dependencias: [TUI-REDESIGN-25-08]
  desbloqueia: []
  origem: "TUI-REDESIGN-25-08 implementou faixa lateral em start/end; spec original pedia faixa em CADA linha da resposta streamada. Implementação completa exige interceptar on_token e wrappar em \\n com prefix '│ '. Risco de quebrar Rich + concorrência."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "on_token (callback de streaming) wrappar: detectar '\\n' e prefixar próxima linha com '│ ' purple"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Helper wrap_streaming_with_side_rule() reaproveitável"

  forbidden:
    - "Adicionar latência >50ms ao streaming"
    - "Quebrar render Rich (Panel, Syntax, Diff)"
    - "Tocar em código que não seja o on_token + helper"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Durante streaming, cada nova linha começa com '│ ' em PURPLE"
    - "Última linha (sem \\n final) também tem prefix"
    - "Streaming continua suave (latência <50ms extra por token)"
    - "Rich Panel/Syntax/Diff em mensagens não-streaming continuam funcionando"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint STREAMING-SIDE-RULE-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-18 (achado durante TUI-REDESIGN-25-08)
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

A TUI-REDESIGN-25-08 implementou header + meta com faixa lateral, mas
a faixa lateral **em cada linha da resposta** ficou para esta sprint.

Razão da extração: interceptar `on_token` (callback de streaming) e
wrappar com `\n` → `\n│ ` requer:

1. Estado entre tokens (saber se acabou de imprimir `\n`).
2. Cuidado com tokens parciais (token pode chegar como "abc\n", "\n", "\nxyz").
3. Não interferir com renders Rich (Panel, Syntax, Diff) que aparecem
   fora do streaming via output("nyx", ...) ou output_style.

## Solução proposta

1. Helper em `output.py`:
   ```python
   def wrap_token_with_side_rule(text: str, state: dict) -> str:
       """Insere '│ ' (PURPLE) após cada \\n encontrado. state mantém
       continuidade entre chamadas (last_ended_newline bool)."""
   ```
2. `cli.py` on_token: chama `wrap_token_with_side_rule(token, side_rule_state)` antes de `sys.stdout.write`.
3. Inicialização: side_rule_state reset a cada turno (em render_assistant_start).
4. Bypass: se output_style != "default" (ex: Rich Panel renderiza fora), pular wrap.

## Critério binário

- [ ] Cada linha da resposta começa com `│` em PURPLE
- [ ] Streaming não engasga (latência <50ms extra)
- [ ] Renders Rich não-streaming intactos
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(STREAMING-SIDE-RULE-01): faixa lateral em cada linha da resposta`

## Invariantes

#6, #14 (PURPLE de design_tokens preservado; SIDE_RULE_NYX já existe).

## Anti-débito

- Faixa lateral no Rich Panel (output `("nyx", ...)`) fica fora — Panel já tem border, dobrar visual é ruído.
- Animação de gradiente na faixa lateral fica fora (over-engineering).

## Verificação

```bash
./run.sh
# digitar "conta 3 linhas pra mim"
# observar: cada linha da resposta tem '│ ' purple no início
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"A presença visual da Nyx é contínua, não apenas no início e fim." -- STREAMING-SIDE-RULE-01*
