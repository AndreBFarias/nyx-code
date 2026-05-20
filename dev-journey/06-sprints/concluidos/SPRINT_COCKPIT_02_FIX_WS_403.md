# SPRINT COCKPIT-02-FIX-WS-403 — WebSocket handshake retorna 403 (bug isolado)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: COCKPIT-02-FIX-WS-403
  title: "Bug: WS handshakes (/repl, /stream, /repl-test) retornam 403 mesmo com handler registrado"
  onda: 24
  bloco: 24.3 Cockpit
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [COCKPIT-02]
  desbloqueia: [COCKPIT-04, COCKPIT-05, VALIDATE-FINAL-01-WS]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "Investigar e corrigir o bug que retorna 403 antes do handler ser chamado"
  creates: []
  removes: []

  forbidden:
    - "Remover defesa loopback (bind 127.0.0.1)"
    - "Aceitar 403 silencioso"

  tests:
    - cmd: "./venv/bin/python -c 'import asyncio, websockets; asyncio.run(websockets.connect(\"ws://127.0.0.1:11437/repl\").__aenter__())'"
      timeout: 30
      deve_passar: "conecta sem InvalidStatus 403"

  acceptance_criteria:
    - "curl WS handshake para /repl, /stream, /repl-test retorna 101"
    - "Handler é chamado (print de stderr aparece nos logs)"
    - "PTY bridge funciona end-to-end (digitar 'oi' no terminal.html recebe resposta)"
    - "Smoke + invariantes 14/14"
```

---

# Sprint COCKPIT-02-FIX-WS-403

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-18 (achado colateral de COCKPIT-02)
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Durante implementação de COCKPIT-02 (2026-05-18 sessão Validador/Integrador), encontrei bug onde WS handshake retorna `403 Forbidden` mesmo com handler registrado.

### Sintoma observável

```
$ curl -s -i -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" http://127.0.0.1:11437/repl
HTTP/1.1 403 Forbidden

Logs do uvicorn:
INFO:     127.0.0.1:XXXXX - "WebSocket /repl" 403
INFO:     connection rejected (403 Forbidden)
```

`print(file=sys.stderr, flush=True)` colocado na primeira linha do handler `repl()` **não aparece** nos logs — confirmando que handler nem é chamado.

### Versões

- Python 3.12.1
- FastAPI 0.135.3
- Starlette 1.0.0
- uvicorn 0.43.0
- websockets 16.0
- wsproto 1.3.2

### Hipóteses investigadas (todas falharam)

1. **Middleware HTTP bloqueando WS:** removi `@app.middleware("http")` — bug persiste.
2. **Versão do websockets package:** instalei `uvicorn[standard]` + `wsproto` — bug persiste.
3. **`ws="wsproto"` no uvicorn.run:** sem efeito.
4. **Ordem dos @app.websocket vs @app.mount:** trocando ordem, bug persiste.
5. **app construído dentro de `create_app()`:** mesmo com `app = create_app()` no module-level, bug persiste.
6. **Passar app como string `"nyx.cockpit.server:app"`:** sem efeito.

### Hipótese atual (não validada)

A combinação `app.mount("/static", StaticFiles(...))` + `create_app()` wrapper provoca o bug. Testes isolados em `/tmp/test_appN.py`:

| Teste | Setup | Resultado |
|---|---|---|
| `test_app1.py` | `app = FastAPI()` no top-level, `@app.websocket` direto | 101 |
| `test_app4.py` | `create_app()` + 1 WS handler, sem mount | 403 inicialmente, depois 101 |
| `test_app6.py` | `create_app()` + 1 WS handler + `app = create_app()` no module-level | 101 |
| `test_app8.py` | `create_app()` + mount + 2 WS handlers + `app = create_app()` | 403 |
| `test_app9.py` | `create_app()` + mount + 1 WS handler | 403 |
| `test_app12.py` | `create_app()` + **route manual de static** + 1 WS handler | 101 |

Conclusão preliminar: `app.mount(StaticFiles(...))` dentro de `create_app()` parece quebrar WS routes. Removi mount do cockpit/server.py mas bug **ainda persiste** — pode haver mais uma camada (talvez interaction com `set[WebSocket]` annotation no `clients` var, ou ordem de registração das múltiplas rotas WS).

### Estado atual no commit

`nyx/cockpit/server.py` já tem:
- `app = create_app()` no module-level
- Static via route manual `/static/{path:path}` (não mais `app.mount`)
- 3 handlers WS: `/stream`, `/repl-test`, `/repl`
- Bug persiste mesmo após essas mudanças

## Solução proposta

Investigação dirigida:

1. **Bisecção mínima:** reduzir `create_app()` ao MÍNIMO que reproduz o bug. Comparar byte-a-byte com `test_app7.py` (que funciona).
2. **Testar com FastAPI/Starlette pinned em versões mais antigas:** FastAPI <0.110, Starlette <0.36. Se passar, é regressão da Starlette 1.0.
3. **Reescrever sem create_app:** instanciar `app` direto no module-level com decorators, sem function wrapper. Talvez seja a única solução para esta combinação.
4. **Reportar upstream:** isolated reproducer + abrir issue no Starlette/uvicorn se for regressão real.

Próximo passo recomendado: **reescrever cockpit/server.py sem create_app function** (tudo no module-level, igual a `/tmp/test_app7.py`). É um refactor pequeno e elimina a variável.

## Comandos de verificação

```bash
# 1. Reproduzir bug atual
./venv/bin/python -m nyx.cockpit.server &
sleep 3
curl -i -H "Connection: Upgrade" -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
     http://127.0.0.1:11437/repl

# 2. Após fix: esperado HTTP/1.1 101 Switching Protocols
```

## Critério binário de aceite

- [ ] Curl WS handshake retorna 101 para /repl, /stream, /repl-test
- [ ] Handler é chamado (print stderr aparece)
- [ ] PTY bridge end-to-end funciona (Chrome MCP em terminal.html)
- [ ] Smoke + invariantes 14/14
- [ ] /tmp/test_appN.py reproduzires deletados após confirmar fix
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `fix(COCKPIT-02-FIX-WS-403): WS handshake retorna 101 (causa: ...)`

---

*"Bug isolado é meio caminho andado." — COCKPIT-02-FIX-WS-403*
