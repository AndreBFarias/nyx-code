# SPRINT 250 — UX-COCKPIT-CHROME-CLOSE-SHUTDOWN-01

## 0. SPEC

```yaml
sprint:
  id: UX-COCKPIT-CHROME-CLOSE-SHUTDOWN-01
  title: "Fechar Chrome = shutdown do run.sh local (sem deixar processos órfãos)"
  onda: 31
  prioridade: ALTA
  tipo: Feature
  dependencias: [UX-WEB-NO-LOCAL-CLI-01, UX-COCKPIT-PTY-HANDOVER-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "Detectar WS disconnect + sinalizar shutdown do run.sh parent"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Em --web, sleep loop precisa de signal handler que reage a sinal do cockpit"
  creates: []
  removes: []
```

---

# Sprint 250 — UX-COCKPIT-CHROME-CLOSE-SHUTDOWN-01

**Status:** CONCLUIDA (2026-05-26)
**Data criação:** 2026-05-25

## Contexto

Usuário: "se fechei normalmente o navegador ele dá control c no terminal e finaliza lá também pra não deixar nada rodando".

Atualmente em modo `--web`:
- Chrome fecha → WS disconnect → cockpit detecta no `try/finally` do `/repl`
- PtyBridge.close() mata cli.py
- MAS: ollama serve, proxy.py, cockpit/server.py, run.sh (sleep loop) seguem vivos
- Usuário precisa abrir terminal e dar Ctrl+C manualmente

## Solução

Opção A — cockpit envia SIGTERM ao process group do run.sh quando WS fechar:
- `server.py` `/repl` no `finally`: `os.killpg(os.getpgid(os.getppid()), signal.SIGTERM)` ou via PID file
- run.sh trap SIGTERM já existe → cleanup ordenado

Opção B — heartbeat WS:
- Cliente envia ping a cada 5s
- Server sem ping em 10s → assume Chrome fechou → shutdown

**Recomendação:** Opção A (mais imediato e simples).

## Detalhes de implementação

`server.py` `/repl` no finally:
```python
finally:
    if _active_pty is bridge:
        bridge.close()
        _active_pty = None
    if _active_ws is ws:
        _active_ws = None
    # SPRINT 250: shutdown do run.sh parent quando Chrome fecha
    # (apenas se este servidor foi spawnado por run.sh --web; detectar via env)
    if os.environ.get("NYX_COCKPIT_FROM_RUN_SH") == "1":
        try:
            parent_pgid = os.getpgid(os.getppid())
            os.killpg(parent_pgid, signal.SIGTERM)
        except Exception:
            pass
```

`run.sh` em modo `--web` exporta `NYX_COCKPIT_FROM_RUN_SH=1` antes de subir cockpit.

## Aceitação

- [ ] `./run.sh --web` → Chrome abre → fechar Chrome → run.sh termina em <3s.
- [ ] `pgrep -af "ollama|nyx" | grep -v earlyoom | grep -v snapshot` retorna vazio após fechar Chrome.
- [ ] Modo default (sem --web) preservado.
- [ ] Ctrl+C no terminal continua funcionando.

## Riscos

| Risco | Mitigação |
|---|---|
| Refresh do Chrome reconecta WS mas sinaliza shutdown intermediário | Delay 2s no shutdown signal; se WS reconectar, cancela |
| Multiple tabs: fechar uma mata tudo | OK (handover da 246 já fechou anteriores; última tab = última usuária) |

## Proof-of-work (REAL, runtime cockpit, 2026-05-26)

Implementado conforme Opção A do spec, com a guarda anti-handover do risco #1:
- `run.sh` exporta `NYX_COCKPIT_FROM_RUN_SH=1` antes de subir o cockpit (confirmado
  em `/proc/<pid>/environ`).
- `server.py`: `import signal`; global `_shutdown_task`; helper `_delayed_shutdown()`
  (sleep 2s -> se `_active_ws is None` ainda, `os.killpg(os.getpgid(os.getppid()),
  SIGTERM)`); no `accept()` cancela shutdown pendente (nova conexão); no `finally`
  agenda shutdown so se `was_active` (nao em handover) e env setada.

Validado via Playwright (boot `./run.sh --web`, env confirmada no processo):
- TEST A (refresh/handover): navigate 2x -> aguardado 4s -> run.sh+ollama+proxy+cockpit
  TODOS VIVOS + /health UP. Handover NAO derruba (guarda cancela o shutdown). [PASS]
- TEST B (fechar navegador): `page.close()` -> aguardado 5s -> run.sh (1304718),
  ollama (1304782), proxy (1304881), cockpit (1304886) TODOS MORTOS;
  `pgrep "ollama serve|cockpit.server|proxy.py"` VAZIO -- zero orfaos. [PASS]
  (background task do run.sh terminou com exit 144 = SIGTERM esperado).

`./run.sh --smoke` boot ok; invariantes 14/14. Modo default (sem --web) preservado
(shutdown gated por NYX_COCKPIT_FROM_RUN_SH, so setada em --web); Ctrl+C intacto
(trap inalterado).
