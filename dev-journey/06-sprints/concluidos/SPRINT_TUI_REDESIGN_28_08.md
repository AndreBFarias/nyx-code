# SPRINT TUI-REDESIGN-28-08 — Input fixo no rodapé (Application full-screen prompt_toolkit)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-28-08
  title: "Migrar REPL de PromptSession solta para Application com HSplit (output scrollável acima + input ancorado embaixo) — paridade Claude Code"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code
  prioridade: ALTA
  tipo: Refactor arquitetural
  dependencias: [TUI-REDESIGN-28-01, TUI-REDESIGN-28-02, TUI-REDESIGN-28-03, TUI-REDESIGN-28-04, TUI-REDESIGN-28-06]
  desbloqueia: []
  origem: "Feedback do usuário 2026-05-18: 'a área de input do user fica sempre fixa no canto inferior em toda a largura. Seria bom se fizéssemos o mesmo pra nossa interface'."

  sub_sprints:
    - id: 28_08a
      title: "POC Application com HSplit (output_buffer + input_buffer + bottom_toolbar)"
      escopo: |
        Criar nyx/agent/repl_app.py com prompt_toolkit Application:
          - Window(BufferControl(output_buffer)) -- altura dynamic = lines-toolbar-input
          - Window(height=1, char='─') -- separador (opcional)
          - Window(BufferControl(input_buffer), height=Dimension(min=1, max=8))
          - Window(FormattedTextControl(_bottom_toolbar), height=1)
        KeyBindings espelham PromptSession atual.
    - id: 28_08b
      title: "Stream de tokens via output_buffer (substitui prints diretos durante streaming)"
      escopo: |
        nyx/agent/output.py detecta app_state['repl_app_active']:
          - True: output_buffer.text += chunk + app.invalidate()
          - False: print() (legacy/headless)
        Streaming TUI-REDESIGN-25-07 redireciona para buffer.
    - id: 28_08c
      title: "Migrar funções render_* para Application"
      escopo: |
        render_assistant_start/end, render_user_input, render_tool_card_start/end,
        render_thinking_block, render_compaction_event, render_session_stats_card,
        banner — todas detectam modo e escrevem em output_buffer.
        Auto-scroll: cursor_position = len(text).
    - id: 28_08d
      title: "Validar gauntlet + smoke + sessão real + screenshot input fixo"
      escopo: |
        ./run.sh --smoke ok
        ./run.sh --gauntlet --only rapido = 100%
        Sessão real: ler/escrever/quit ok dentro do Application
        Screenshot import -window confirma input box embaixo

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Novo módulo: Application + Layout + KeyBindings"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Substituir prompt_session.prompt_async pelo Application.run_async; preservar fallback legacy via NYX_LEGACY_REPL=1"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Detect app_state['repl_app_active'] e redirecionar prints para output_buffer (mantém fallback)"

  forbidden:
    - "Quebrar headless (--smoke, --gauntlet, --auto-approve): modo Application só em TTY"
    - "Quebrar streaming de tokens (essencial para responsividade percebida)"
    - "Eliminar fallback legacy abruptamente (NYX_LEGACY_REPL=1 mantém PromptSession funcional 1 release)"
    - "Mexer em proxy.py, tools/*, ou loop/_iteration.py (escopo é render layer)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh | tail -3"
      timeout: 60
      deve_passar: "PASS=14 FAIL=0"
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 600
      deve_passar: "100% (11/11)"
    - cmd: "NYX_LEGACY_REPL=1 ./run.sh --smoke"
      timeout: 60
      deve_passar: "boot ok (modo legacy ainda viável)"
    - cmd: "./venv/bin/python -c 'from nyx.agent.repl_app import build_app; print(build_app)'"
      timeout: 5
      deve_passar: "import sem erro"

  acceptance_criteria:
    - "Subir Nyx: input ANCORADO no rodapé durante toda sessão (scroll do output não move input)"
    - "Toolbar inferior persiste abaixo do input"
    - "Streaming de tokens flui no output_buffer com auto-scroll"
    - "Ctrl+C cancela inflight task; /quit fecha limpo via signal handler do Application"
    - "Tools (Read/Write/Edit/Bash) executam dentro do Application sem corromper layout"
    - "Fallback NYX_LEGACY_REPL=1 funciona idêntico ao REPL atual"
    - "Smoke ok + gauntlet rapido 100%"
    - "Screenshot via 'import -window' confirma paridade Claude Code"

  proof_of_work:
    - "Sub-sprint 28_08a: ./venv/bin/python -m nyx.agent.repl_app --self-test = roda Application por 3s, recebe Ctrl+C, sai limpo"
    - "Sub-sprint 28_08b: streaming test — proxy responde 100 tokens, todos aparecem no output_buffer sem perda"
    - "Sub-sprint 28_08c: cada render_* tem teste runtime mínimo (./venv/bin/python -c 'from nyx.agent.output import render_X; render_X(...)')"
    - "Sub-sprint 28_08d: gauntlet rapido 100% + screenshot arquivado em proofs/TUI_28_08/"

  riscos:
    - "Streaming pode ficar engasgado se output_buffer não invalidar app a cada chunk — mitigar com app.invalidate() async-safe"
    - "Cursor position do output_buffer pode pular para topo em append longos — fixar com cursor_to_end() após append"
    - "Tools que imprimem direto via subprocess (Bash) escapam do redirect — capturar stdout/stderr via PIPE no PtyBridge ou tee"
```

---

# Sprint TUI-REDESIGN-28-08

**Status:** CONCLUIDA (com 28_08c_PARTE_2 DEFERIDA)
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Resultado

- 28_08a: POC Application com HSplit (output_buffer + input + toolbar) — commit `022ecc1`
- 28_08b: routing _emit (app_state flag + set_repl_app_output + clear_repl_app_output) — commit `ace4a03`
- 28_08c: migra render_* para roteamento via _emit (CONCLUIDA_PARCIAL) — commit `9125ecc`
- 28_08c_PARTE_2: switch runtime Application/PromptSession (DEFERIDA — spec em producao/)
- 28_08d: validar gauntlet + smoke + sessão real — commit `<seguinte>`

Smoke: boot ok (default + NYX_LEGACY_REPL=1)
Invariantes: 14/14 (PASS=14 FAIL=0)
Gauntlet rapido: 18/18 (100%)
Screenshot proof: dev-journey/07-reports/proofs/TUI_28_08/nyx_repl_app_selftest_20260518T233912.png

## Rollback

`git reset --hard HEAD~4` (reverte 4 commits da onda 28_08a..d)
