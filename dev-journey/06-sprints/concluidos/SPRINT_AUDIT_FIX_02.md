## 0. SPEC

```yaml
sprint:
  id: AUDIT-FIX-02
  title: "Conectar NyxSettings ao bootstrap real (cli.py + loop.py + proxy.py)"
  onda: 22
  bloco: 2
  prioridade: CRÍTICA
  tipo: Refactor
  dependencias: [AUDIT-FIX-03]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/settings.py
      reason: "Expandir NyxSettings com proxy_port e computar URLs já centralizadas"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "run_repl() e run_headless() passam a receber settings ou carregá-las no topo"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop.py
      reason: "AgentLoop aceita settings opcional; proxy_url derivado dela"

  forbidden:
    - "Criar uma segunda fonte de verdade (settings E defaults independentes)"
    - "Quebrar os env vars NYX_OLLAMA_PORT / NYX_PROXY_PORT (devem continuar sobrescrevendo)"
    - "Remover defaults.py — é a fonte das constantes imutáveis; settings.py lê dela"

  tests:
    - cmd: "python -c 'from nyx.config.settings import load_settings; s=load_settings(); assert s.proxy_port == 11436 and s.ollama_port == 11435'"
      deve_passar: true
    - cmd: "NYX_OLLAMA_PORT=11500 python -c 'from nyx.config.settings import load_settings; s=load_settings(); assert s.ollama_port == 11500'"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "NyxSettings ganha campo proxy_port (11436 default)"
    - "NyxSettings ganha propriedades proxy_url e proxy_v1_url"
    - "cli.run_repl() e cli.run_headless() usam load_settings() ou recebem settings por parâmetro"
    - "AgentLoop tem construtor que aceita NyxSettings opcional (retrocompatível)"
    - "grep retorna pelo menos 2 pontos de uso de NyxSettings ou load_settings() em nyx/cli.py e nyx/agent/loop.py"
    - "Gauntlet rapido passa"
```

---

# Sprint AUDIT-FIX-02 — Conectar NyxSettings ao bootstrap real

**Status:** PENDENTE
**Data criação:** 2026-04-18
**Dependência:** AUDIT-FIX-03 já concluída (portas centralizadas)

## Contexto do projeto (snapshot)

- ADR-001 (Local First), ADR-013 (Integração Obrigatória — nada solto)
- `nyx/config/settings.py` define `NyxSettings` dataclass + `load_settings()`. Arquivo existe mas NUNCA foi importado em produção (descoberto por AUDIT-EXT-01 finding C-02).
- `nyx/config/defaults.py` é a fonte única de constantes (AUDIT-FIX-03 já plugou OLLAMA_PORT, PROXY_PORT, OLLAMA_URL, PROXY_URL, PROXY_V1_URL).

## Problema

`NyxSettings` é dataclass sem consumidor. Mudanças em `.env` ou `NYX_OLLAMA_PORT` não propagam pelo sistema — cada módulo lê env por conta própria, duplicando lógica.

## Solução

1. **Expandir `settings.py`** adicionando `proxy_port` e propriedades `proxy_url`, `proxy_v1_url`.
2. **Bootstrap de `cli.py`** chama `load_settings()` uma vez e passa para `AgentLoop` e para helpers.
3. **`AgentLoop.__init__`** aceita `settings: NyxSettings | None = None`. Se `None`, chama `load_settings()`.
4. Funções que lêem `os.environ.get("NYX_OLLAMA_PORT", ...)` passam a consultar `settings`.

## Arquivos alvo

### `nyx/config/settings.py`

**Antes (linha 15-40, atual):**
```python
@dataclass
class NyxSettings:
    project_root: Path
    ollama_host: str
    ollama_port: int
    model: str
    vram_max_gb: float
    max_iterations: int
    temperature: float
    max_tokens: int
    num_ctx: int
    debug: bool
    headless: bool

    @property
    def ollama_base_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"
```

**Depois:**
```python
@dataclass
class NyxSettings:
    project_root: Path
    ollama_host: str
    ollama_port: int
    proxy_port: int          # NOVO
    model: str
    vram_max_gb: float
    max_iterations: int
    temperature: float
    max_tokens: int
    num_ctx: int
    debug: bool
    headless: bool

    @property
    def ollama_base_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"

    @property
    def proxy_url(self) -> str:
        return f"http://{self.ollama_host}:{self.proxy_port}"

    @property
    def proxy_v1_url(self) -> str:
        return f"{self.proxy_url}/v1"
```

E em `load_settings()`, logo após `port = int(os.getenv("NYX_OLLAMA_PORT", str(defaults.OLLAMA_PORT)))`:

```python
proxy_port = int(os.getenv("NYX_PROXY_PORT", str(defaults.PROXY_PORT)))
```

E no `return NyxSettings(...)`:
```python
return NyxSettings(
    project_root=project_root,
    ollama_host=os.getenv("NYX_OLLAMA_HOST", defaults.OLLAMA_HOST),
    ollama_port=port,
    proxy_port=proxy_port,        # NOVO
    ...
)
```

### `nyx/cli.py` — bootstrap

No topo de `run_repl()` e `run_headless()`, **antes** de carregar `AgentLoop`:

```python
from nyx.config.settings import load_settings
settings = load_settings()
```

Substituir:
```python
proxy_url = os.environ.get("OPENAI_BASE_URL", _PROXY_V1_URL)
proxy_url = proxy_url.replace("/v1", "").rstrip("/")
if not proxy_url.startswith("http"):
    proxy_url = _PROXY_URL
model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", "qwen3:4b"))
```

Por:
```python
proxy_url = os.environ.get("OPENAI_BASE_URL", settings.proxy_v1_url)
proxy_url = proxy_url.replace("/v1", "").rstrip("/")
if not proxy_url.startswith("http"):
    proxy_url = settings.proxy_url
model = os.environ.get("OPENAI_MODEL", os.environ.get("NYX_MODEL", settings.model))
```

### `nyx/agent/loop.py`

No construtor de `AgentLoop`:

```python
def __init__(
    self,
    project_root: str,
    proxy_url: str = _DEFAULT_PROXY_URL,
    model: str = "qwen3:4b",
    max_iterations: int = MAX_ITERATIONS_DEFAULT,
    settings: "NyxSettings | None" = None,    # NOVO (import tardio na linha)
    ...
```

Se `settings` fornecido: usar `settings.proxy_url`, `settings.model`, `settings.max_iterations` como defaults (mantendo retrocompatibilidade: argumentos explícitos vencem).

## Diff esperado

```
~ 3 arquivos modificados (settings.py, cli.py, loop.py)
+ ~45 linhas
- ~10 linhas
```

## Comando de verificação

```bash
# 1. Carrega settings com defaults
python -c "
from nyx.config.settings import load_settings
s = load_settings()
print('ollama:', s.ollama_port, 'proxy:', s.proxy_port)
print('proxy_url:', s.proxy_url)
print('proxy_v1_url:', s.proxy_v1_url)
assert s.ollama_port == 11435
assert s.proxy_port == 11436
assert s.proxy_url == 'http://127.0.0.1:11436'
print('OK')
"

# 2. Env override funciona
NYX_OLLAMA_PORT=11500 NYX_PROXY_PORT=11501 python -c "
from nyx.config.settings import load_settings
s = load_settings()
assert s.ollama_port == 11500, f'got {s.ollama_port}'
assert s.proxy_port == 11501, f'got {s.proxy_port}'
print('env override OK')
"

# 3. grep mostra 2+ pontos de uso
grep -rn 'load_settings\|NyxSettings' /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop.py

# 4. Gauntlet
./run.sh --gauntlet --only rapido
```

## Critério binário

- [ ] `NyxSettings.proxy_port` existe e default é 11436
- [ ] `NyxSettings.proxy_url` e `proxy_v1_url` retornam URLs corretas
- [ ] `load_settings()` é chamada em `cli.run_repl` ou `cli.run_headless`
- [ ] `AgentLoop` aceita parâmetro opcional `settings`
- [ ] Os 4 comandos de verificação acima passam
- [ ] Gauntlet rapido passa
- [ ] Commit: `refactor: conecta NyxSettings ao bootstrap (ADR-013)`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- `grep -rn load_settings nyx/cli.py nyx/agent/loop.py` retornar 0 linhas.
- Env override (`NYX_OLLAMA_PORT=11500 ./run.sh`) não mudar a porta real.
- Foi adicionado `from nyx.config.settings import load_settings` mas nunca chamado.

## Validação humana

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code
git show --stat HEAD | head
python -c "from nyx.config.settings import load_settings; s=load_settings(); print(s.proxy_port, s.proxy_url)"
# saída esperada: 11436 http://127.0.0.1:11436
NYX_OLLAMA_PORT=11500 python -c "from nyx.config.settings import load_settings; print(load_settings().ollama_port)"
# saída esperada: 11500
ls dev-journey/06-sprints/concluidos/SPRINT_AUDIT_FIX_02.md  # deve existir
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Import circular settings ↔ defaults | settings importa de defaults, nunca o contrário |
| Retrocompatibilidade quebrada | `settings=` é param opcional; chamadas antigas continuam funcionando |

---

*"Centralizar é delegar ao pensamento o que os nervos não deveriam resolver." -- Martin Fowler (paráfrase)*
