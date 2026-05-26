# SPRINT 246 — UX-COCKPIT-PTY-HANDOVER-01

## 0. SPEC

```yaml
sprint:
  id: UX-COCKPIT-PTY-HANDOVER-01
  title: "Cockpit faz handover de PTY quando nova WS conecta (em vez de busy)"
  onda: 31
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [UX-WEB-NO-LOCAL-CLI-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "Endpoint /repl rejeita segunda conexão com 'PTY ocupado'; usuário não pode reabrir tab sem matar tudo"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/static/terminal.html
      reason: "Cliente WS deve tratar `type:'replaced'` como info, não erro"
  creates: []
  removes: []
```

---

# Sprint 246 — UX-COCKPIT-PTY-HANDOVER-01

**Status:** PENDENTE
**Data criação:** 2026-05-25

## Contexto

Usuário reportou repetidamente: ao abrir Chrome no cockpit, mostra "outra sessao PTY ativa. Aguarde ela fechar". WebSocket fechado.

Causa: `server.py:541-581` `/repl` rejeita segunda conexão WS quando `_pty_lock.locked()` ou `preflight.state == 'alive'`. Mas usuário tipicamente:
- Abre Chrome → primeira tab pega PTY
- Refresh/F5 → cria nova WS sem fechar anterior cleanly
- Nova WS recebe "busy" → mostra erro
- Tab antiga fica em zombie state com PTY órfão

## Solução: handover automático

Nova conexão WS:
1. Se `_active_pty is None` → spawnar normal (caso atual).
2. Se `_active_pty is not None` (sessão prévia):
   a. Enviar `{"type":"replaced"}` para WS anterior (`_active_ws`) e fechar com code 1000.
   b. Chamar `_active_pty.terminate()` para matar cli.py antigo.
   c. Esperar `_pty_lock` liberar (timeout 2s).
   d. Spawnar novo PTY para a WS atual.

Estado adicional:
```python
_active_ws: WebSocket | None = None
```

Em `/repl`:
```python
if _active_pty is not None:
    try:
        if _active_ws is not None:
            await _active_ws.send_text(json.dumps({"type": "replaced"}))
            await _active_ws.close(code=1000)
    except Exception:
        pass
    try:
        _active_pty.terminate()
    except Exception:
        pass
    _active_pty = None
    _active_ws = None
    # Aguarda lock liberar
    for _ in range(20):
        if not _pty_lock.locked():
            break
        await asyncio.sleep(0.1)

# ... lógica normal de spawn ...
_active_ws = ws  # registrar
```

Em `terminal.html` cliente:
```js
if (meta.type === "replaced") {
    setStatus("info", "Sessão substituída por nova aba");
    return;  // sem mostrar erro vermelho
}
```

## Acceptance

- [ ] Abrir Chrome no cockpit → 1ª tab funciona
- [ ] Abrir 2ª tab → 1ª recebe `replaced`, 2ª funciona
- [ ] cli.py antigo (1ª) é morto, novo cli.py spawnado para 2ª
- [ ] Sem mais mensagem "outra sessao PTY ativa" em uso normal
- [ ] Smoke + invariantes preservados

## Proof-of-work

```bash
./run.sh --web &
sleep 15
# Tab 1
google-chrome --new-window http://127.0.0.1:11437/static/terminal.html &
sleep 5
# Tab 2
google-chrome --new-window http://127.0.0.1:11437/static/terminal.html &
sleep 5
# Capturar ambas — esperado: tab 2 conectada, tab 1 com info "Sessão substituída"
```
