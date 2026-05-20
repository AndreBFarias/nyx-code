## 0. SPEC (machine-readable)

```yaml
sprint:
  id: AUDIT-03
  title: "Sincronizacao N-para-N: versao, constantes, dependencias"
  touches:
    - path: nyx/__version__.py
      reason: "Criar single source of truth para versao"
    - path: nyx/cli.py
      reason: "Importar versao de __version__"
    - path: nyx/agent/commands.py
      reason: "Importar versao de __version__"
    - path: pyproject.toml
      reason: "Sincronizar versao com __version__"
    - path: nyx/config/defaults.py
      reason: "Unica fonte de NUM_CTX, MAX_ITERATIONS, etc"
    - path: nyx/proxy.py
      reason: "Importar constantes de defaults.py"
    - path: nyx/agent/loop.py
      reason: "Importar MAX_ITERATIONS de defaults.py"
    - path: nyx/agent/models.py
      reason: "Adicionar ActionType.WEB_FETCH e ActionType.REPL"
    - path: nyx/agent/tools/web_fetch.py
      reason: "Corrigir action_type para WEB_FETCH"
    - path: nyx/agent/tools/repl_tool.py
      reason: "Corrigir action_type para REPL"
    - path: requirements.txt
      reason: "Remover pydantic, adicionar ddgs e html2text como opcionais"
  n_to_n_pairs:
    - "Versao: __version__.py -> pyproject.toml -> cli.py -> commands.py"
    - "NUM_CTX: defaults.py -> proxy.py -> run.sh"
    - "MAX_ITERATIONS: defaults.py -> loop.py"
    - "ActionType de cada tool deve corresponder a sua funcao real"
  forbidden:
    - "Nunca hardcodar versao em mais de 1 lugar"
    - "Nunca hardcodar constante que existe em defaults.py"
  tests:
    - cmd: "./run.sh --gauntlet --only audit_sync"
      timeout: 300
    - cmd: "python scripts/sync.py"
      timeout: 60
  acceptance_criteria:
    - "Versao definida em 1 unico arquivo (nyx/__version__.py)"
    - "pyproject.toml, cli.py, commands.py importam a mesma versao"
    - "NUM_CTX definido apenas em defaults.py"
    - "MAX_ITERATIONS definido apenas em defaults.py"
    - "web_fetch.action_type == ActionType.WEB_FETCH"
    - "repl.action_type == ActionType.REPL"
    - "pydantic removido de requirements.txt"
    - "ddgs e html2text em requirements.txt (opcionais)"
    - "sync.py passa sem erros"
    - "Acentuacao PT-BR correta"
```

---

# Sprint AUDIT-03 -- Sincronizacao N-para-N

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-15
**Prioridade:** ALTA
**Tipo:** Refactor/Infra
**Dependencias:** Nenhuma
**Desbloqueia:** AUDIT-02

---

## Problema / Contexto

A meta-regra "Sincronizacao N-para-N" (GUIDE.md regra 9.1) diz: "Se um valor existe em N lugares, atualizar TODOS ou nenhum." A auditoria encontrou 3 violacoes:

1. **Versao**: `pyproject.toml` diz `1.1.1`, `cli.py` diz `1.2.0`, `commands.py` diz `v1.2.0`
2. **NUM_CTX**: `defaults.py` = 16384, `proxy.py` = 4096, `run.sh` = 4096
3. **MAX_ITERATIONS**: `defaults.py` = 50, `loop.py` = 30

Alem disso, `web_fetch.action_type` aponta para `READ_FILE` em vez de ter seu proprio tipo, e dependencias fantasma/ausentes no `requirements.txt`.

## Implementacao

### Fase 1: Versao centralizada

1. Criar `nyx/__version__.py` com `__version__ = "1.2.0"`
2. `pyproject.toml`: usar `dynamic = ["version"]` com `[tool.setuptools.dynamic] version = {attr = "nyx.__version__.__version__"}`
3. `cli.py`: `from nyx.__version__ import __version__` e usar `NYX_VERSION = __version__`
4. `commands.py`: importar e usar no cmd_version

### Fase 2: Constantes centralizadas

1. `defaults.py` e a unica fonte -- manter NUM_CTX=4096 (valor correto para GPU limitada)
2. `proxy.py`: `from nyx.config.defaults import NUM_CTX, NUM_GPU_3B` (remover hardcode)
3. `loop.py`: `from nyx.config.defaults import MAX_ITERATIONS` (remover hardcode)
4. `run.sh`: ler NUM_CTX via `python -c "from nyx.config.defaults import NUM_CTX; print(NUM_CTX)"`

### Fase 3: ActionTypes corretos

1. Adicionar `WEB_FETCH = "web_fetch"` e `REPL = "repl"` em `models.py`
2. Corrigir `web_fetch.py`: `action_type = ActionType.WEB_FETCH`
3. Corrigir `repl_tool.py`: `action_type = ActionType.REPL`
4. Atualizar `ACTION_TO_TOOL` no `loop.py` se necessario

### Fase 4: Dependencias

1. Remover `pydantic>=2.0.0` do `requirements.txt` (nunca importado)
2. Adicionar ao final:
   ```
   # Opcionais (web search/fetch)
   ddgs>=6.0.0
   html2text>=2024.2.26
   ```

## Verificacao

- [ ] `python -c "from nyx.__version__ import __version__; print(__version__)"` imprime `1.2.0`
- [ ] `grep -rn "1.1.1\|1.2.0" nyx/ pyproject.toml` mostra apenas `__version__.py` e imports
- [ ] `grep -rn "NUM_CTX" nyx/proxy.py` mostra import, nao hardcode
- [ ] `grep -rn "MAX_ITERATIONS_DEFAULT" nyx/agent/loop.py` nao existe (importa de defaults)
- [ ] `python -c "from nyx.agent.tools.web_fetch import WebFetchTool; print(WebFetchTool.action_type.value)"` imprime `web_fetch`
- [ ] `grep pydantic requirements.txt` nao retorna nada
- [ ] `python scripts/sync.py` passa
- [ ] Gauntlet fase audit_sync passa
- [ ] Acentuacao PT-BR correta

---

*"A coerencia e a virtude dos sistemas robustos." -- Edsger Dijkstra*
