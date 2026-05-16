## 0. SPEC

```yaml
sprint:
  id: AUDIT-FIX-03
  title: "Centralizar portas Ollama/Proxy em config/defaults.py (fonte única)"
  onda: 22
  bloco: 1
  prioridade: CRÍTICA
  tipo: Refactor
  dependencias: []
  desbloqueia: [AUDIT-FIX-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "Adicionar PROXY_PORT = 11436 e PROXY_URL / OLLAMA_URL helpers"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Importar OLLAMA_PORT, PROXY_PORT de defaults"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Substituir 11435/11436 hardcoded"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/providers/ollama.py
      reason: "URL vem de defaults"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop.py
      reason: "URL padrão em construtor vem de defaults"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands.py
      reason: "/doctor e /status usam defaults"

  n_to_n_pairs:
    - descricao: "Ports 11435/11436 em 15+ lugares — única fonte"
      paths: [cli, proxy, providers/ollama, agent/loop, agent/commands, config/defaults]

  forbidden:
    - "Manter port literal fora de config/defaults.py"
    - "Quebrar variáveis de ambiente NYX_OLLAMA_PORT / NYX_PROXY_PORT (env overrides continuam)"

  tests:
    - cmd: "grep -rn '11435\\|11436' nyx/ --include='*.py' | grep -v defaults.py"
      deve_passar: true  # resultado deve ser vazio (ou só variáveis de env)
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "config/defaults.py exporta OLLAMA_PORT=11435 e PROXY_PORT=11436"
    - "Nenhum literal 11435/11436 fora de defaults.py (exceto strings de env override)"
    - "./run.sh sobe Ollama + Proxy nas portas corretas"
    - "Variável NYX_OLLAMA_PORT=11500 muda a porta sem editar código"
    - "Gauntlet rapido passa"
```

---

# Sprint AUDIT-FIX-03 — Centralizar portas

**Status:** PENDENTE
**Data criação:** 2026-04-18

## Contexto

Meta-regra N-para-N (GUIDE.md inviolável): "Se um valor existe em N lugares, atualizar TODOS ou nenhum". Ports `11435` e `11436` aparecem em 15+ pontos (cli, proxy, providers, loop, commands). `config/defaults.py` tem `OLLAMA_PORT=11435` mas ninguém importa.

## Problema

Mudar porta = caçar 15 lugares. Inclusive strings fstring (`"http://127.0.0.1:11435/v1"`).

## Solução

1. Adicionar em `defaults.py`:
   ```python
   PROXY_PORT: int = 11436
   OLLAMA_URL: str = f"http://127.0.0.1:{OLLAMA_PORT}"
   PROXY_URL: str  = f"http://127.0.0.1:{PROXY_PORT}"
   ```
2. Trocar todos os literais `11435`/`11436` e URLs hardcoded por imports de defaults.
3. Preservar `os.environ.get("NYX_OLLAMA_PORT", str(OLLAMA_PORT))` (env override continua funcionando).

## Arquivos alvo

### `nyx/config/defaults.py`
```python
OLLAMA_PORT: int = 11435
PROXY_PORT: int = 11436
OLLAMA_HOST: str = "127.0.0.1"
OLLAMA_URL: str = f"http://{OLLAMA_HOST}:{OLLAMA_PORT}"
PROXY_URL: str = f"http://{OLLAMA_HOST}:{PROXY_PORT}"
PROXY_V1_URL: str = f"{PROXY_URL}/v1"
```

### `nyx/cli.py` (linhas 53-54, 217-220, 557-560)

Antes:
```python
ollama_port = os.environ.get("NYX_OLLAMA_PORT", "11435")
proxy_port = os.environ.get("NYX_PROXY_PORT", "11436")
```

Depois:
```python
from nyx.config.defaults import OLLAMA_PORT, PROXY_PORT
ollama_port = os.environ.get("NYX_OLLAMA_PORT", str(OLLAMA_PORT))
proxy_port = os.environ.get("NYX_PROXY_PORT", str(PROXY_PORT))
```

### `nyx/proxy.py` (linhas 38, 283-284)

Antes:
```python
OLLAMA_URL = "http://127.0.0.1:11435"
parser.add_argument("--port", type=int, default=11436)
parser.add_argument("--ollama-port", type=int, default=11435)
```

Depois:
```python
from nyx.config.defaults import OLLAMA_URL as _DEFAULT_OLLAMA_URL, OLLAMA_PORT as _DEFAULT_OLLAMA_PORT, PROXY_PORT as _DEFAULT_PROXY_PORT
OLLAMA_URL = _DEFAULT_OLLAMA_URL
parser.add_argument("--port", type=int, default=_DEFAULT_PROXY_PORT)
parser.add_argument("--ollama-port", type=int, default=_DEFAULT_OLLAMA_PORT)
```

### `nyx/providers/ollama.py` (linha 18)

Antes:
```python
def __init__(self, proxy_url: str = "http://127.0.0.1:11436", timeout: int = DEFAULT_TIMEOUT):
```

Depois:
```python
from nyx.config.defaults import PROXY_URL
def __init__(self, proxy_url: str = PROXY_URL, timeout: int = DEFAULT_TIMEOUT):
```

### `nyx/agent/loop.py` (linha 99)

Antes:
```python
proxy_url: str = "http://127.0.0.1:11436",
```

Depois:
```python
from nyx.config.defaults import PROXY_URL
...
proxy_url: str = PROXY_URL,
```

### `nyx/agent/commands.py` (linhas 247, 253, 258, 263, 442, 444, 635)

Idem: usar `OLLAMA_URL`, `PROXY_URL`, `PROXY_V1_URL` nas chamadas `httpx.get(...)` e nas strings de `/doctor` (mas números visíveis ao usuário nas mensagens devem usar `OLLAMA_PORT`/`PROXY_PORT` via fstring, mantendo legibilidade).

## Verificação

```bash
# 1. Nenhum literal remanescente
grep -rn '11435\|11436' nyx/ --include='*.py' | grep -v 'defaults.py' | grep -v 'NYX_OLLAMA_PORT\|NYX_PROXY_PORT'
# saída esperada: vazia

# 2. Subir e conferir
./run.sh &
sleep 5
curl -s http://127.0.0.1:11436/v1/models | head
kill %1
```

## Critério binário

- [ ] `defaults.py` exporta `OLLAMA_PORT`, `PROXY_PORT`, `OLLAMA_URL`, `PROXY_URL`, `PROXY_V1_URL`
- [ ] Zero literais `11435`/`11436` fora de `defaults.py`
- [ ] `./run.sh` funciona (Ollama + Proxy sobem)
- [ ] Env override `NYX_OLLAMA_PORT=11500 ./run.sh` funciona (teste manual)
- [ ] Gauntlet rapido passa
- [ ] Commit: `refactor: centraliza portas ollama/proxy em defaults.py (N-para-N)`

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Quebrar env override | Preservar `os.environ.get` em todos pontos que já tinham |
| Import circular | `defaults.py` não importa de ninguém — só constantes |

---

*"Um valor em dois lugares é um valor em dois estados." -- Fowler*
