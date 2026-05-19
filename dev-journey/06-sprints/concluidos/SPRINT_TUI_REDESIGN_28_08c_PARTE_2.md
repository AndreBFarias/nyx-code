# SPRINT TUI-REDESIGN-28-08c-PARTE-2 — Switch runtime Application vs PromptSession

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-28-08c-PARTE-2
  title: "Ativar runtime do Application (substitui PromptSession.prompt_async no loop REPL)"
  onda: 28
  bloco: 28.1 TUI paridade Claude Code
  prioridade: MEDIA
  tipo: Integração arquitetural
  dependencias: [TUI-REDESIGN-28-08a, TUI-REDESIGN-28-08b, TUI-REDESIGN-28-08c]
  origem: "Materializada pelo executor ao concluir 28_08c. A migração de render_* via _emit ficou completa; a ativação do Application em runtime (substituir loop while True + prompt_async) requer redesenho do REPL que excede o escopo da sub-sprint original sem regressões."

  escopo: |
    Reescrever loop principal em nyx/cli.py para:
      - Se sys.stdin.isatty() E não NYX_LEGACY_REPL=1: usar run_repl_app_async
        com app_state["repl_app_active"]=True e set_repl_app_output(output_buffer, app_state)
        antes do primeiro prompt
      - Loop fica: while True: try: user_input = await run_repl_app_async(...);
        processar; após processar limpa input_buffer.text="" via callback
      - Streaming de tokens (loop em cli.py ~linha 1100+) routeia chunks via
        _emit (já está pronto para isso após 28_08b)
      - Banner inicial: continua via stdout puro (boot phase, antes do Application)
      - Após print do banner, antes do while True, ativar repl_app_active=True

    Pontos críticos:
      - Application full-screen ocupa toda a tela; banner não pode coexistir
        com Application no mesmo viewport sem ser absorvido pelo output_buffer
      - Solução: pre-popular output_buffer com banner ANSI (append_to_buffer)
        antes de app.run_async; ou fazer banner como primeiro append já dentro
        do Application
      - Tools que rodam subprocess (Bash) precisam de captura stdout via PIPE
        para não escapar do Application — usar tee ou redirect interno
      - Ctrl+C precisa cancelar inflight sem sair do Application
      - /quit precisa fechar Application limpo via app.exit()

  touches:
    - path: nyx/cli.py
      reason: "Reescrever loop principal substituindo prompt_async pelo run_repl_app_async"

  forbidden:
    - "Quebrar headless (--smoke, --gauntlet, --auto-approve)"
    - "Quebrar streaming de tokens"
    - "Eliminar NYX_LEGACY_REPL=1 fallback"

  tests:
    - cmd: "./run.sh --smoke"
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh | tail -3"
      deve_passar: "PASS=14 FAIL=0"
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: "100%"
    - cmd: "NYX_LEGACY_REPL=1 ./run.sh --smoke"
      deve_passar: "boot ok"

  acceptance_criteria:
    - "Em TTY: input ANCORADO no rodapé, output scroll acima, toolbar persistente"
    - "Streaming de tokens flui no output_buffer com auto-scroll"
    - "Ctrl+C cancela inflight; /quit fecha limpo"
    - "Fallback NYX_LEGACY_REPL=1 funciona"
    - "Tools subprocess capturadas corretamente"

  riscos:
    - "Application ocupar toda tela conflita com prints pré-existentes (boot logs, render_user_input legacy via PromptSession)"
    - "Streaming pode engasgar se invalidate() não ser thread-safe em chunks rápidos"
    - "Subprocess Bash escapa do Application — mitigação via tee/PIPE no PtyBridge"

  estrategia_implementacao: |
    1. Pre-populate output_buffer com banner antes do run_async
    2. Reescrever while True para usar run_repl_app_async no lugar de prompt_async
    3. Adaptar render_user_input dentro do Application (já está pronto via _emit)
    4. Capturar stdout/stderr de tools subprocess via PtyBridge ou tee
    5. Smoke validar não-tty fallback (headless usa input() builtin)
```

---

# Sprint TUI-REDESIGN-28-08c-PARTE-2

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7
**Motivo da deferência:** sub-sprint 28_08c (migração de render_*) concluída; ativação do Application em runtime requer redesenho do loop REPL com mitigação de boot logs, banner overlap e captura de subprocess, fora do escopo de "migrar render_*" original.
**Promoção 2026-05-19:** DEFERIDA → PENDENTE para execução com arquitetura herdada de 28_08a/b/c (build_app, run_repl_app_async, set_repl_app_output, _emit) já presente.
**Resultado:** Switch runtime ativo. Em TTY + NYX_LEGACY_REPL!=1: build_app uma vez, set_repl_app_output ativa routing _emit, app.run_async() reaproveitado por iteração. Pre-populate de banner com strip ANSI imediato (mitigação até PARTE-3 trocar BufferControl por FormattedTextControl). Smoke ok (TTY + NYX_LEGACY_REPL=1), invariantes 14/14, gauntlet rápido APROVADO, self-test repl_app ok. Achado colateral: BufferControl não interpreta ANSI → SPRINT_TUI_REDESIGN_28_08c_PARTE_3.md criada em producao/.
