# SPRINT 249 — UX-COCKPIT-FLASH-PRETO-01

## 0. SPEC

```yaml
sprint:
  id: UX-COCKPIT-FLASH-PRETO-01
  title: "Eliminar flash preto entre Enter e início da resposta da Nyx"
  onda: 31
  prioridade: MÉDIA
  tipo: Bugfix
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Possivelmente clear screen ou cursor positioning ANSI emitido entre input echo e response start"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Application path pode estar invalidating renderer entre Enter e on_token"
  creates: []
  removes: []
```

---

# Sprint 249 — UX-COCKPIT-FLASH-PRETO-01

**Status:** PENDENTE
**Data criação:** 2026-05-25

## Contexto

Usuário reportou: "após dar o enter, a tela fica super preta ao invés de mostrar o que já mostra mas exibir o aquecendo da nix acima do nome dela".

Sequência atual observada:
1. User digita texto + Enter
2. Tela inteira fica preta brevemente (flash)
3. Resposta aparece com `◆ Nyx` + stream

Desejado:
1. User digita texto + Enter
2. SEM flash preto
3. Aparece `◆ NyxCode` + linha "aquecendo..." (com spinner) ENQUANTO modelo processa
4. Spinner some quando resposta começa a streamar

## Hipóteses de causa-raiz

1. **`renderer.clear()` ou `app.reset()`** em algum lugar do submit handler do REPL.
2. **Application alternate-screen toggle** quando entra em modo de streaming.
3. **CSS do xterm.js no Chrome** com transição CSS escura entre frames.
4. **`stop_spinner` + `render_assistant_start`** ordem dispara repaint completo.

## Solução

Fase 1 — diagnóstico:
- Adicionar `logger.info` em pontos críticos do REPL submit handler.
- Capturar 6 frames @ 100ms via tmux/import durante o flash.
- Identificar qual chamada emite o ANSI clear screen (`\x1b[2J`).

Fase 2 — fix cirúrgico:
- Substituir clear screen por update parcial.
- Mostrar `◆ NyxCode` + `│ aquecendo...` (spinner inline) IMEDIATAMENTE após Enter (não esperar 1ª tokenização).
- Spinner substituído por `│ token1 token2...` quando stream inicia.

## Aceitação

- [ ] 6 frames @ 100ms entre Enter e 1º token: SEM frame totalmente preto (sem outlier <1KB).
- [ ] `◆ NyxCode` + spinner aparece em <100ms após Enter.
- [ ] Streaming substitui spinner suavemente.
- [ ] Smoke + invariantes preservados.

## ROOT-CAUSE CONFIRMADO (2026-05-26, repro empírico no cockpit)

Reproduzido via Playwright + captura X11 @80ms (`/tmp/fl_008.png`): durante TODO o
processamento a conversa some (tela vazia), reaparece com a resposta. NÃO é flash
breve -- dura o turno inteiro.

Causa-raiz REAL (mais profunda que as hipóteses originais -- é a #2 + #4 combinadas):
- `repl_app.py:578` constrói a Application com `full_screen=True` (alternate screen).
- `cli.py:640` faz `await repl_app.run_async()` POR TURNO: a Application roda só
  para capturar input e SAI (`app.exit`) quando o usuário submete.
- O `agent.run()` (cli.py:783) processa o turno com a Application JÁ ENCERRADA.
- Ao sair do `run_async()`, o prompt_toolkit DEIXA a alternate screen -> o
  `output_window` (que desenha a conversa) some -> tela principal em branco durante
  todo o processamento. Próximo `run_async()` re-entra a alternate screen e
  re-renderiza o `output_buffer` (agora com a resposta) -> conversa "volta".
- Secundário: `NyxSpinner` (output.py:490,516) escreve `sys.stdout` CRU em vez de
  `_emit`; em modo Application isso não aparece coerentemente.

Por que "spinner no buffer" sozinho NÃO resolve: durante o processamento a
Application está encerrada, logo o `output_buffer` nem é renderizado -- `◆ NyxCode`
+ spinner iriam para um buffer invisível.

## SOLUÇÃO ESCOLHIDA (usuário 2026-05-26): refactor in-app

Manter a Application VIVA durante o processamento (padrão moderno prompt_toolkit):
- `run_async()` roda UMA vez (não por turno).
- `accept_handler` (Enter), em vez de `app.exit(result=text)`, agenda o
  processamento como background task: `app.create_background_task(process_turn(text))`
  e NÃO sai da Application.
- Extrair o corpo do turno atual (cli.py ~662-870: handle_command, agent.run,
  render_assistant_start/end, summarize, cancel/erro) para uma coroutine
  `process_turn(text)`.
- Com a Application viva, `_emit`/`append_to_buffer` renderizam AO VIVO (visível);
  `get_app()` funciona nos callbacks do event loop -> spinner pode animar no buffer
  com line-replace + `app.invalidate()`.
- Reentrância: desabilitar/ignorar submit enquanto `inflight` ativo (ou enfileirar).
- Cancel (Ctrl+C / /cancel) cancela a background task.
- Interação com 248: `suppress_live` permanece (box ao fim); o spinner cobre o
  período de processamento; ao 1º token o spinner para e o box materializa ao fim.

Risco ALTO (núcleo do REPL). Validar: smoke + invariantes + repro no cockpit
(conversa NÃO some durante processamento; spinner "aquecendo" visível acima do
NyxCode; resposta materializa o box sem flash). Considerar sub-sprint dedicada por
ser refactor de ~250 linhas críticas.

**Status permanece PENDENTE** -- diagnóstico e design prontos; implementação é o
próximo passo focado.
