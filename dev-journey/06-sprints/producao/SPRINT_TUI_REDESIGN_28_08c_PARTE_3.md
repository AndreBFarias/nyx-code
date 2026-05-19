# SPRINT TUI-REDESIGN-28-08c-PARTE-3 — Render ANSI no output_buffer da Application

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-28-08c-PARTE-3
  title: "Interpretar escape ANSI no output_buffer do repl_app (cores + estilo no fluxo Application)"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code
  prioridade: ALTA
  tipo: Correcao arquitetural derivada de PARTE-2
  dependencias: [TUI-REDESIGN-28-08c-PARTE-2]
  origem: |
    Materializada pelo executor durante validação visual de 28-08c-PARTE-2.
    Banner pré-populado e fluxo de tokens via _emit chegam ao output_buffer
    como string ANSI bruta (^[[38;2;212;170m...). O BufferControl do
    prompt_toolkit NÃO interpreta ANSI; soh FormattedTextControl o faz.
    Mitigacao temporaria em PARTE-2 strip-a ANSI no pre-populate do banner,
    perdendo cores. PARTE-3 deve substituir BufferControl por arquitetura
    que renderize ANSI (cores + bold + dim) preservando append-only stream.

  escopo: |
    Substituir output_window (BufferControl(buffer=output_buffer)) por um
    FormattedTextControl alimentado por um callback que retorna FormattedText
    a partir de ANSI.from_ansi(buffer.text). OU manter Buffer + criar wrapper
    que processa ANSI a cada append e gera lista de (style, text) tuples.

    Pontos criticos:
      - Stream de tokens chega em chunks; ANSI escape pode quebrar entre
        chunks (parser tem que ser stateful).
      - Scroll: FormattedTextControl precisa de window.scroll_offsets para
        manter cursor no final.
      - Performance: re-parse de buffer.text inteiro a cada append eh O(N);
        manter cache stateful de FormattedText acumulado.

  touches:
    - path: nyx/agent/repl_app.py
      reason: "Reescrever output_window para usar FormattedTextControl + ANSI parser stateful"
    - path: nyx/cli.py
      reason: "Remover strip ANSI do pre-populate do banner (volta a usar banner com cores)"

  forbidden:
    - "Quebrar self-test repl_app --self-test"
    - "Quebrar streaming de tokens (chunks ANSI partidos entre flushes)"
    - "Regredir performance: parse stateful obrigatorio"

  tests:
    - cmd: "./venv/bin/python -m nyx.agent.repl_app --self-test"
      deve_passar: "ok"
    - cmd: "./run.sh --smoke"
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      deve_passar: "PASS=14 FAIL=0"
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: "100%"

  acceptance_criteria:
    - "Banner pré-populado renderiza com cores no output_buffer"
    - "Streaming de tokens com cores ANSI (render_assistant_start/render_tool_card) flui colorido"
    - "Scroll segue cursor no final mesmo com FormattedText"
    - "Self-test passa em headless"

  riscos:
    - "FormattedTextControl recalcular toda lista de tuplas a cada invalidate"
    - "ANSI parser stateful precisa lidar com codigos truncados entre chunks"

  estrategia_implementacao: |
    1. Criar AnsiStreamParser stateful em nyx/agent/ansi_parser.py (ou usar
       prompt_toolkit.formatted_text.ANSI nativo se aceitar stream).
    2. Trocar output_control de BufferControl para FormattedTextControl com
       callback que retorna lista de (style, text) tuplas acumuladas.
    3. append_to_buffer vira append_to_output: parse incremental + invalidate.
    4. Remover strip ANSI em nyx/cli.py pre-populate banner.
    5. Testar com banner colorido + render_assistant_start (ACCENT).
```

---

# Sprint TUI-REDESIGN-28-08c-PARTE-3

**Status:** PENDENTE
**Data criação:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7
**Origem:** materializada durante execução de TUI-REDESIGN-28-08c-PARTE-2 (achado colateral em validação visual).
