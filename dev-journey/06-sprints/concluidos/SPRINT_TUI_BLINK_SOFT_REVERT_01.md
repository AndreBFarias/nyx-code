## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TUI-BLINK-SOFT-REVERT-01
  title: "Revert cirúrgico da sprint 187 (BLINK_SOFT) — remove banner_blink_loop que causa flicker via app.invalidate() global"
  onda: 29
  prioridade: ALTA
  tipo: Revert
  dependencias: [TUI-BANNER-BLINK-SOFT-03]
  desbloqueia: [TUI-TEXTUAL-MIGRATION-PLAN-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Remover funções `banner_blink_loop`, `replace_banner_prefix` introduzidas pela 187 — restaurar para estado pré-commit 8523220"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Remover dispatch de asyncio.create_task(banner_blink_loop(...)) e ref em app_state['_banner_blink_task'] — restaurar para append_to_buffer simples sem blink loop"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Remover helpers build_banner_frame_a/build_banner_frame_b e parâmetro `cursor` em build_banner se não usados por mais ninguém — restaurar build_banner simples com glifo `▌` fixo"

  preservar_da_188:
    - path: nyx/cli_keybindings.py
      reason: "Binding c-q da 188 fica intacto"
    - path: nyx/agent/repl_app.py
      reason: "Binding c-q + c-d das sprints 188/189 ficam intactos"
    - path: nyx/cli_boot.py
      reason: "Bloco ollama stop all da 188 fica intacto"
    - path: nyx/cli.py
      reason: "Early-return __quit__ da 188 fica intacto"
    - path: nyx/agent/banner_blink.py
      reason: "Frame OFF com `chr(0x258F)` da 187 (legacy path) — DECISÃO: mantém porque o caminho legacy não tem flicker (escreve via stdout cru, sem buffer global). Só remove o loop async da Application."

  forbidden:
    - "Reverter qualquer mudança da sprint 188 (CTRL_Q + ollama stop all)"
    - "Reverter qualquer mudança da sprint 189 (CTRL_D paridade Unix)"
    - "Reverter mudanças da 184/185/186/190"
    - "Usar git revert no commit 8523220 (vai tirar a 188 junto — revert cirúrgico manual via Edit)"
    - "Remover banner_blink.py (caminho legacy)"
    - "Adicionar emoji"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "grep -n 'banner_blink_loop\\|replace_banner_prefix' nyx/agent/repl_app.py retorna zero"
    - "grep -n '_banner_blink_task' nyx/cli.py retorna zero"
    - "grep -n 'build_banner_frame_a\\|build_banner_frame_b' nyx/agent/ retorna zero"
    - "Ctrl+Q ainda fecha TUI (sprint 188 preservada)"
    - "Ctrl+D em buffer vazio ainda fecha (sprint 189 preservada)"
    - "Cursor `▌` aparece estático no banner do caminho Application (sem blink async, sem flicker)"
    - "Caminho legacy (NYX_LEGACY_REPL=1) mantém blink crú via banner_blink.py — não tocado"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint TUI-BLINK-SOFT-REVERT-01 — Revert cirúrgico da 187

**Status:** PENDENTE
**Data criação:** 2026-05-22
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - Sprint 187 (TUI-BANNER-BLINK-SOFT-03, commit 8523220, 2026-05-21) introduziu `banner_blink_loop` async em `nyx/agent/repl_app.py` que muta a primeira linha do `output_buffer` a cada 0.5s alternando entre frame_a (▌ U+258C) e frame_b (▏ U+258F).
> - Sprint 188 (TUI-CTRL-Q-OLLAMA-STOP-04, mesmo commit 8523220) adicionou binding Ctrl+Q + ollama stop all em `shutdown_repl()`.
> - Usuário reportou em 2026-05-22 que a TUI "quebra, volta, quebra, fica suja na transição".
> - Auditoria identificou causa raiz: `banner_blink_loop` chama `app.invalidate()` global a cada 0.5s (via `append_to_buffer` ou `replace_banner_prefix` que disparam invalidate). Prompt_toolkit refaz repaint da tela inteira → race com streaming + flicker visual.
> - Luna (em `/home/andrefarias/Desenvolvimento/Luna/`) usa **Textual** com widgets isolados (`self.update(text)` local) — não tem esse problema. Migração para Textual é planejada na sprint 194 (TUI-TEXTUAL-MIGRATION-PLAN-01).

---

## Problema

A sprint 187 introduziu flicker observável na TUI por arquitetura incompatível com prompt_toolkit: `app.invalidate()` é global. Sprint 188 (Ctrl+Q + ollama stop all) foi commitada junto (commit 8523220 consolidado) e PRECISA ser preservada.

`git revert 8523220` derrubaria as duas. Esta sprint faz **revert cirúrgico manual** via Edit, removendo APENAS o código da 187 e preservando a 188.

---

## Solução proposta

Edit cirúrgico nos 3 arquivos modificados pela 187 (banner.py, repl_app.py, cli.py), removendo:

1. `banner_blink_loop` async (em repl_app.py)
2. `replace_banner_prefix` helper (em repl_app.py)
3. `asyncio.create_task(banner_blink_loop(...))` + `app_state["_banner_blink_task"]` (em cli.py)
4. `build_banner_frame_a`/`build_banner_frame_b` helpers + parâmetro `cursor` em `build_banner` (em banner.py) — se não usados por mais ninguém.

`banner_blink.py` (caminho legacy) NÃO é tocado — frame OFF com `chr(0x258F)` continua sendo melhor que espaço, e o caminho legacy não sofre do flicker (escreve via stdout cru com `\033[s` save/restore cursor, fora do output_buffer da Application).

Banner final na Application volta a usar `build_banner(...)` simples com cursor `▌` estático (estado pré-187).

---

## Comandos de verificação

```bash
# 1. Revert aplicado
grep -n "banner_blink_loop\|replace_banner_prefix" nyx/agent/repl_app.py  # esperado: vazio
grep -n "_banner_blink_task" nyx/cli.py                                    # esperado: vazio
grep -n "build_banner_frame_a\|build_banner_frame_b" nyx/agent/             # esperado: vazio

# 2. Sprint 188/189 preservadas
grep -n "c-q\|c-d" nyx/cli_keybindings.py nyx/agent/repl_app.py | head
grep -n "ollama ps\|ollama stop" nyx/cli_boot.py | head

# 3. Smoke + invariantes
./run.sh --smoke
bash scripts/sprint_invariants.sh

# 4. Runtime visual via tmux
tmux new-session -d -s nyx_test './run.sh'
sleep 6
tmux capture-pane -t nyx_test -p > /tmp/post_revert.txt
# Inspecionar: deve ter banner estático com ▌, sem flicker, output_buffer estável
tmux send-keys -t nyx_test C-q
sleep 3
tmux has-session -t nyx_test 2>&1   # esperado: "can't find session" (Ctrl+Q ainda funciona)

# 5. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/agent/repl_app.py nyx/cli.py nyx/agent/banner.py
```

---

## Critério binário de aceite

- [ ] `grep "banner_blink_loop" nyx/agent/repl_app.py` → 0 matches
- [ ] `grep "_banner_blink_task" nyx/cli.py` → 0 matches
- [ ] `grep "build_banner_frame_a" nyx/agent/` → 0 matches
- [ ] `grep "@kb.add(.c-q.)" nyx/cli_keybindings.py` → ≥1 match (188 preservada)
- [ ] `grep "@kb.add(.c-d.)" nyx/cli_keybindings.py` → ≥1 match (189 preservada)
- [ ] `grep "ollama ps" nyx/cli_boot.py` → ≥1 match (188 preservada)
- [ ] `./run.sh --smoke` boot ok exit 0
- [ ] `bash scripts/sprint_invariants.sh` PASS 14/14
- [ ] Captura tmux: banner estático sem flicker
- [ ] Captura tmux pós-Ctrl+Q: sessão fechou
- [ ] Acentuação PT-BR rc=0

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Edit acidental remove código da 188/189 | Acceptance criteria explícitos garantem Ctrl+Q e Ctrl+D continuam funcionando |
| `build_banner` perder parâmetro `cursor` quebra import em outro lugar | grep antes de remover: `grep -rn "build_banner_frame\|build_banner.*cursor=" nyx/` |
| banner_blink.py mantém ▏ no frame OFF mas pode parecer inconsistente sem o blink da Application | Aceitar: caminho legacy é raro (NYX_LEGACY_REPL=1), e ▏ é melhor que espaço |
| Migração Textual futura precisar do helper frame_a/frame_b | Pode ser re-introduzido na sprint de migração com arquitetura correta |

---

*"Voltar atrás cirurgicamente é virtude, não derrota." -- princípio refactor Nyx-Code.*
