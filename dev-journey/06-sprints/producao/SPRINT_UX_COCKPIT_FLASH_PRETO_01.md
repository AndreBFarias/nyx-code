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
