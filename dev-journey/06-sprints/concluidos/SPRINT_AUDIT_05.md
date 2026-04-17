## 0. SPEC (machine-readable)

```yaml
sprint:
  id: AUDIT-05
  title: "Performance: conexoes, search, proxy"
  touches:
    - path: nyx/proxy.py
      reason: "ClientSession app-level, encapsular globals em ProxyConfig"
    - path: nyx/agent/loop.py
      reason: "httpx.AsyncClient reutilizavel, cache de tools selecionadas"
    - path: nyx/agent/tools/search.py
      reason: "Usar grep/rg via subprocess em vez de walk manual"
  n_to_n_pairs: []
  forbidden:
    - "Nunca criar ClientSession ou AsyncClient dentro de funcao chamada repetidamente"
    - "Nunca usar global para estado mutavel"
  tests:
    - cmd: "./run.sh --gauntlet --only audit_performance"
      timeout: 300
  acceptance_criteria:
    - "Proxy usa uma unica ClientSession por app lifetime"
    - "Loop usa um unico httpx.AsyncClient por sessao"
    - "Search usa grep/rg quando disponivel, fallback para walk"
    - "Proxy nao usa globals mutaveis"
    - "Acentuacao PT-BR correta"
```

---

# Sprint AUDIT-05 -- Performance: Conexoes, Search, Proxy

**Status:** PENDENTE
**Data:** 2026-04-15
**Prioridade:** MEDIA
**Tipo:** Performance
**Dependencias:** AUDIT-04
**Desbloqueia:** AUDIT-06

---

## Problema / Contexto

Tres gargalos de performance identificados na auditoria:

1. **Proxy** (`proxy.py:155`): cria `ClientSession` nova a cada request HTTP. Em sessoes longas com muitas tool calls, isso significa centenas de handshakes TCP desnecessarios.

2. **Loop** (`loop.py:417`): cria `httpx.AsyncClient` novo a cada chamada LLM. Mesmo problema -- conexao TCP recriada a cada iteracao.

3. **Search** (`tools/search.py:40-58`): faz `rglob("*")` + readlines manual em Python puro. Em projetos com milhares de arquivos, e 10-100x mais lento que `grep -rn` ou `rg`.

Alem disso, `proxy.py` usa globals mutaveis (`OLLAMA_URL`, `NUM_GPU`, `NUM_CTX`) modificados via `global`, o que e fragil e dificulta testes.

## Implementacao

### Fase 1: Proxy -- ClientSession app-level

```python
@dataclass
class ProxyConfig:
    ollama_url: str
    num_gpu: int
    num_ctx: int

async def on_startup(app: web.Application) -> None:
    app["session"] = ClientSession(timeout=ClientTimeout(total=600))

async def on_cleanup(app: web.Application) -> None:
    await app["session"].close()

# No handler:
session = request.app["session"]
async with session.post(...) as resp:
    ...
```

### Fase 2: Loop -- httpx.AsyncClient reutilizavel

```python
class AgentLoop:
    def __init__(self, ...):
        ...
        self._http_client = httpx.AsyncClient(timeout=LLM_TIMEOUT)

    async def _call_llm(self) -> dict:
        r = await self._http_client.post(...)
        ...

    async def close(self) -> None:
        await self._http_client.aclose()
```

Chamar `agent.close()` no CLI ao sair.

### Fase 3: Search -- usar grep/rg

```python
def _search_with_rg(pattern, target, root):
    """Tenta rg, depois grep, depois fallback Python."""
    for cmd in ["rg", "grep"]:
        if shutil.which(cmd):
            args = [cmd, "-rn", "--max-count=100", pattern, str(target)]
            if cmd == "rg":
                args.extend(["--type=py", "--type=js", "--type=json", ...])
            result = subprocess.run(args, capture_output=True, text=True, timeout=30)
            if result.returncode in (0, 1):  # 1 = no match
                return result.stdout
    return None  # fallback para walk manual
```

### Fase 4: Proxy -- encapsular globals

Mover `OLLAMA_URL`, `NUM_GPU`, `NUM_CTX` para `ProxyConfig` dataclass. Passar via `app["config"]`.

## Verificacao

- [ ] `grep -rn "ClientSession()" nyx/proxy.py` nao aparece dentro de handlers
- [ ] `grep -rn "httpx.AsyncClient(" nyx/agent/loop.py` aparece apenas no `__init__`
- [ ] `grep -rn "global " nyx/proxy.py` retorna 0 resultados
- [ ] Search encontra resultados em < 1s para projetos com 1000+ arquivos
- [ ] Gauntlet fase audit_performance passa
- [ ] Acentuacao PT-BR correta

---

*"A otimizacao prematura e a raiz de todo mal. Mas a otimizacao tardia e a raiz de todo lento." -- adaptado de Donald Knuth*
