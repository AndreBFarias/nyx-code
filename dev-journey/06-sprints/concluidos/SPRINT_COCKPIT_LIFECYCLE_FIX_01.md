# SPRINT COCKPIT-LIFECYCLE-FIX-01 — PTY do cockpit colide com single-instance lock

## 0. SPEC

```yaml
sprint:
  id: COCKPIT-LIFECYCLE-FIX-01
  title: "Cockpit/PTY reutiliza REPL existente em vez de matar+criar (UX-LIFECYCLE-01)"
  onda: 24
  bloco: 24.3 Cockpit
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [COCKPIT-02, UX-LIFECYCLE-01]
  desbloqueia: [VALIDATE-FINAL-01-PARTE-2, NYX-AUTO-APPROVE-01]
  origem: "Achado real 2026-05-18: ao reabrir terminal.html no cockpit (2a sessao PTY), lifecycle matou processo anterior (PID 395937), e proxy nao reiniciou. UX-LIFECYCLE-01 protege contra zumbi mas conflita com fluxo cockpit."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/pty_bridge.py
      reason: "PtyBridge.start verifica lock existente antes de spawnar run.sh"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "@app.websocket(/repl) detecta lock e oferece reattach se PID vivo"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/lifecycle.py
      reason: "Opcional: aceitar env NYX_LIFECYCLE_TAKEOVER=1 (cockpit substitui anterior limpo)"

  forbidden:
    - "Desabilitar single-instance lock (anti-zumbi) globalmente"
    - "Matar processo TUI ativo quando usuario humano esta usando"
    - "Lock leak: se cockpit cai, lock fica preso"

  tests:
    - cmd: "echo 'cockpit + 2 sessões PTY consecutivas'"
      timeout: 60

  acceptance_criteria:
    - "PtyBridge detecta PID anterior via NYX_PID_FILE"
    - "Se PID existe e processo vivo: cockpit avisa 'sessao ativa, reabra'"
    - "Se PID stale (processo morto): cockpit limpa lock e spawnar"
    - "Cockpit nao causa cascata de kill em UX-LIFECYCLE-01"
    - "Proxy reiniciado limpo apos cockpit fechar PTY"
```

---

# Sprint COCKPIT-LIFECYCLE-FIX-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-18 (achado de uso real)
**Data conclusão:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Cenário real 2026-05-18: durante validacao do cockpit via Playwright, dois PTYs consecutivos foram abertos (cada visita ao terminal.html spawna um novo). Na segunda visita:

```
[nyx] Matando instancia anterior (PID 395937)...
[nyx] proxima sprint: VISUAL-LAYOUT-02 (24 pendentes)
[nyx] Pre-carga falhou (modelo sera carregado na primeira requisicao)
Terminado
[nyx] Desconectando...
[nyx] Fim.
[nyx] Proxy nao iniciou. Verifique logs/proxy.log
[nyx] Desconectando...
[nyx] Fim.
```

UX-LIFECYCLE-01 (single-instance via NYX_PID_FILE) mata processo anterior (correto pra anti-zumbi), mas ao matar destruiu o proxy 11436 num estado inconsistente. Nova sessão não conseguiu rebootar.

## Solução proposta

3 níveis defensivos:

**Nível 1 — detecção:** `PtyBridge.start()` lê `NYX_PID_FILE` antes de exec. Se PID vivo, retorna erro `{type:"busy", reason:"sessao Nyx ativa em outro lugar"}` em vez de spawnar.

**Nível 2 — takeover opt-in:** env `NYX_LIFECYCLE_TAKEOVER=1` instrui lifecycle a fazer shutdown ordenado (não SIGKILL) do anterior. Cockpit pode usar isso explicitamente.

**Nível 3 — cleanup pos-mortem:** se PID morto mas lock prendeu (PID stale), cockpit limpa lock antes de spawnar.

## Critério binário

- [ ] PtyBridge detecta lock vivo
- [ ] Cockpit retorna 'busy' em vez de cascade-kill
- [ ] Takeover ordenado via env opt-in
- [ ] Stale lock auto-limpa
- [ ] Cockpit reabre terminal sem proxy zumbi
- [ ] Smoke + invariantes 14/14
- [ ] Commit `fix(COCKPIT-LIFECYCLE-FIX-01): PTY detecta lock UX-LIFECYCLE-01 e reusa em vez de matar`

---

*"Lock e cockpit precisam se conhecer." -- COCKPIT-LIFECYCLE-FIX-01*
