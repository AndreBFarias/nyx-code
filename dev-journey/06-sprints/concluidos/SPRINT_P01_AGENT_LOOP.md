## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P-01
  title: "Agent loop + tools (plan-execute-observe com 10 tools)"
  touches:
    - path: nyx/agent/loop.py
      reason: "Ciclo principal: prompt -> LLM -> parse -> tool -> repeat"
    - path: nyx/agent/tools/
      reason: "10 tools: read, write, edit, bash, glob, grep, search, list, analyze, done"
    - path: nyx/agent/models.py
      reason: "Dataclasses: AgentAction, ActionResult, SessionState"
    - path: nyx/agent/session.py
      reason: "Estado da sessão: histórico, arquivos lidos/modificados"
    - path: nyx/agent/prompt.py
      reason: "System prompt Nyx + contexto do projeto"
    - path: nyx/cli.py
      reason: "REPL mínimo para testar o loop"
  n_to_n_pairs:
    - a: "nyx/agent/loop.py -> nyx/proxy.py"
      reason: "Loop envia requests ao proxy, proxy encaminha ao Ollama"
  forbidden:
    - "Mocks de Ollama ou proxy"
    - "Dependência de Node.js"
    - "Import de src/ da Luna (copiar e adaptar, não importar)"
  tests:
    - cmd: "./run.sh --gauntlet"
      timeout: 900
  acceptance_criteria:
    - "Agent loop funciona: recebe input, chama LLM, parseia ação, executa tool, mostra resultado"
    - "10 tools implementadas e testáveis"
    - "Loop termina quando LLM emite done() ou atinge max_iterations"
    - "Gauntlet inclui testes E2E do agent loop"
    - "nyx/cli.py funciona como REPL interativo"
    - "Acentuação PT-BR correta"
```

---

# Sprint P-01 -- Agent Loop + Tools

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-04-04
**Prioridade:** CRITICA
**Tipo:** Feature
**Dependências:** F-01
**Desbloqueia:** P-02 a P-08, V-01 a V-05

---

## Problema

O Nyx-Code depende de um bundle Node.js compilado (OpenClaude) que não temos source.
Precisamos de um agent loop Python próprio, inspirado na Luna (`src/skills/code_agent/`).

## Arquitetura (baseada na Luna)

```
nyx/agent/
├── __init__.py
├── loop.py          # AgentLoop: plan-execute-observe
├── models.py        # AgentAction, ActionResult, ActionType, SessionState
├── session.py       # CodeSession: histórico, arquivos, iterações
├── prompt.py        # build_agent_prompt(), system prompt Nyx
├── tools/
│   ├── __init__.py
│   ├── base.py      # RegisteredTool, ToolDef (interface)
│   ├── registry.py  # ToolRegistry: auto-descoberta + execução
│   ├── read_file.py
│   ├── write_file.py
│   ├── edit_file.py
│   ├── run_command.py
│   ├── glob_tool.py
│   ├── search.py    # grep
│   ├── list_files.py
│   ├── analyze.py
│   └── done.py
nyx/cli.py           # REPL: banner + input loop + agent.run()
```

## Fluxo do AgentLoop

```
1. Recebe pedido do usuário
2. Constrói prompt: system + contexto do projeto + histórico + último resultado
3. Envia ao proxy (POST /v1/chat/completions com tools)
4. Parseia resposta:
   - Se tool_call: executa a tool, coleta resultado, volta ao passo 2
   - Se texto puro: parseia ação via fallback (Luna tem 7 níveis)
   - Se done(): termina
5. Verifica limites (max_iterations, repetição)
6. Mostra resultado ao usuário
```

## Decisões de design

1. **Comunicação via proxy:** o loop envia requests HTTP ao proxy (porta 11436),
   que converte para Ollama nativo e injeta think=false.

2. **Tools via function calling:** usa o mecanismo de tool_calls do Ollama/qwen3,
   não parse de texto. Fallback textual vem na P-02.

3. **Sem permissões por agora:** na v1, tudo é permitido (read, write, bash).
   Permissões e confirmação vêm em sprint futura.

4. **Session simples:** lista de (ação, resultado). Sem SQLite por agora (P-08).

## Implementação

### 1. `nyx/agent/models.py`

```python
from enum import Enum
from dataclasses import dataclass

class ActionType(Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    EDIT_FILE = "edit_file"
    RUN_COMMAND = "run_command"
    GLOB = "glob"
    SEARCH = "search"
    LIST_FILES = "list_files"
    ANALYZE = "analyze"
    DONE = "done"

@dataclass
class AgentAction:
    action_type: ActionType
    params: dict
    reasoning: str = ""

@dataclass
class ActionResult:
    success: bool
    output: str
    error: str = ""
```

### 2. `nyx/agent/tools/base.py`

Cada tool implementa `execute(params) -> ActionResult`.

### 3. `nyx/agent/loop.py`

```python
class AgentLoop:
    def __init__(self, project_root, proxy_url, model):
        self._proxy = proxy_url
        self._model = model
        self._tools = ToolRegistry(project_root)
        self._session = CodeSession()
        self._max_iterations = 30

    async def run(self, user_input: str) -> str:
        self._session.add_user(user_input)
        for i in range(self._max_iterations):
            response = await self._call_llm()
            if response.has_tool_calls:
                for tc in response.tool_calls:
                    result = self._tools.execute(tc)
                    self._session.add_tool_result(tc, result)
            elif response.is_done:
                break
            else:
                self._session.add_assistant(response.content)
                break
        return self._session.last_output()
```

### 4. `nyx/cli.py`

```python
async def main():
    print(banner)
    agent = AgentLoop(project_root=Path.cwd(), ...)
    while True:
        user_input = input("nyx> ")
        result = await agent.run(user_input)
        print(result)
```

## Verificação

- [ ] `python nyx/cli.py` inicia e mostra banner
- [ ] Enviar "leia README.md" -> agent chama Read, mostra conteúdo
- [ ] Enviar "crie /tmp/test.py com print('ok')" -> agent chama Write
- [ ] Enviar "execute echo hello" -> agent chama Bash
- [ ] Loop termina com done() ou max_iterations
- [ ] `./run.sh --gauntlet` continua passando 100%
- [ ] Gauntlet inclui testes do agent loop (novos testes E2E)

---

*"A complexidade mata. Simplifique implacavelmente." -- Steve Jobs*
