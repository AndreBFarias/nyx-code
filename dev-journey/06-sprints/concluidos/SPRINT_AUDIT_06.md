## 0. SPEC (machine-readable)

```yaml
sprint:
  id: AUDIT-06
  title: "Robustez e UX: shutdown, health check, atomicidade"
  touches:
    - path: nyx/cli.py
      reason: "Graceful shutdown no headless, ativar logging, corrigir _ask_permission"
    - path: nyx/agent/persistence.py
      reason: "Escrita atomica de sessoes"
    - path: nyx/proxy.py
      reason: "Health check endpoint"
    - path: nyx/agent/loop.py
      reason: "Metricas de latencia por iteracao e tool call"
  n_to_n_pairs:
    - "_ask_permission callback deve usar level corretamente"
  forbidden:
    - "Nunca write_text direto para sessoes (usar escrita atomica)"
  tests:
    - cmd: "./run.sh --gauntlet --only audit_robustez"
      timeout: 300
  acceptance_criteria:
    - "Headless salva sessao ao receber SIGINT/SIGTERM"
    - "Proxy tem GET /health que retorna status"
    - "Sessoes escritas atomicamente (write .tmp -> rename)"
    - "Sessoes antigas limpas automaticamente no startup"
    - "Logging rotacionado ativo na CLI"
    - "Metricas de latencia disponiveis via /stats"
    - "_ask_permission exibe nivel de permissao corretamente"
    - "Acentuacao PT-BR correta"
```

---

# Sprint AUDIT-06 -- Robustez e UX

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-15
**Prioridade:** MEDIA
**Tipo:** Feature/Robustez
**Dependencias:** AUDIT-05
**Desbloqueia:** Nenhuma (ultima sprint de auditoria)

---

## Problema / Contexto

A auditoria identificou problemas de robustez e UX que impedem o modo "ultra":

1. **Headless sem graceful shutdown**: Ctrl+C no modo headless nao salva sessao. Trabalho perdido.
2. **Proxy sem health check**: nao ha como verificar se o proxy esta saudavel programaticamente.
3. **Sessoes nao atomicas**: `write_text()` pode corromper JSON se crash durante escrita.
4. **Sessoes nunca limpas**: acumulam indefinidamente em `~/.nyx/sessions/`.
5. **Logging nao ativo**: `InternalLogging` existe mas nunca e instanciado.
6. **Sem metricas de latencia**: impossivel saber quanto tempo o LLM demora por chamada.
7. **_ask_permission ignora level**: o primeiro argumento (nivel de permissao) e recebido mas ignorado.

## Implementacao

### Fase 1: Graceful shutdown no headless

```python
async def run_headless() -> int:
    agent = AgentLoop(...)

    async def _shutdown():
        saved = save_session(agent.session, PROJECT_ROOT.name)
        if saved:
            msg = json.dumps({"type": "shutdown", "session": saved.name})
            sys.stdout.write(msg + "\n")
            sys.stdout.flush()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(_shutdown()))
    ...
```

### Fase 2: Health check na proxy

```python
async def handle_health(request: web.Request) -> web.Response:
    try:
        async with ClientSession(timeout=ClientTimeout(total=5)) as session:
            async with session.get(f"{OLLAMA_URL}/api/version") as resp:
                ollama_ok = resp.status == 200
    except Exception:
        ollama_ok = False

    status = "ok" if ollama_ok else "degraded"
    return web.json_response({
        "status": status,
        "ollama": ollama_ok,
        "proxy": True,
    })

# Registrar:
app.router.add_get("/health", handle_health)
```

### Fase 3: Escrita atomica de sessoes

```python
def save_session(session, project_name=""):
    ...
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(data, ...), encoding="utf-8")
    tmp_path.rename(path)  # Atomico no mesmo filesystem
    ...
```

### Fase 4: Metricas de latencia

No `loop.py`, adicionar timing:
```python
import time

async def run(self, user_input: str) -> SessionStatus:
    ...
    for i in range(self._max_iterations):
        iter_start = time.monotonic()
        ...
        response = await self._call_llm()
        llm_time = time.monotonic() - iter_start
        self._metrics["llm_times"].append(llm_time)
        ...
```

Expor via `/stats`:
```
Latencia media LLM: 12.3s
Latencia media tool: 0.4s
```

### Fase 5: Corrigir _ask_permission

```python
# Antes (cli.py:63)
def _ask_permission(level: str, tool_name: str, args: dict) -> bool:

# Depois -- usar level na mensagem
def _ask_permission(level: str, tool_name: str, args: dict) -> bool:
    level_label = {
        "confirm_once": "uma vez",
        "always_confirm": "sempre",
    }.get(level, level)
    resp = input(
        f"  {ACCENT}[permissao: {level_label}]{NC} Executar {BOLD}{tool_name}{NC}(...)? [S/n] "
    )
    ...
```

## Verificacao

- [ ] Headless salva sessao ao receber SIGINT
- [ ] `curl http://127.0.0.1:11436/health` retorna JSON com status
- [ ] Sessoes em `~/.nyx/sessions/` nunca ficam como `.tmp`
- [ ] Sessoes > 7 dias sao removidas no startup
- [ ] `~/.nyx/logs/nyx.log` existe e rota apos 5MB
- [ ] `/stats` mostra latencia media do LLM
- [ ] Prompt de permissao mostra "uma vez" ou "sempre"
- [ ] Gauntlet fase audit_robustez passa
- [ ] Acentuacao PT-BR correta

---

*"A robustez e a elegancia que sobrevive ao caos." -- Nassim Taleb*
