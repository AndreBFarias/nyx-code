## 0. SPEC

```yaml
sprint:
  id: DEBT-01
  title: "Split nyx/agent/loop.py (739 linhas) em pacote loop/"
  onda: 22
  bloco: 2
  prioridade: MÉDIA
  tipo: Refactor
  dependencias: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop.py
      reason: "Vira pacote loop/ com submódulos; API pública preservada"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/__init__.py
      reason: "Re-exporta AgentLoop, AgentStatus, AgentState, PermissionCallback"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Classe AgentLoop (método run, reset, close, get_context_info, maybe_summarize)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_iteration.py
      reason: "Loop interno de iteração: parse → executa tool → atualiza session"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_constants.py
      reason: "LLM_TIMEOUT, ACTION_TO_TOOL, PARAM_REMAP, _remap_params"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_types.py
      reason: "AgentStatus, AgentState enum, PermissionCallback Protocol"

  forbidden:
    - "Mudar API pública: AgentLoop(project_root, ...).run(user_input)"
    - "Criar arquivo > 400 linhas no pacote"
    - "Quebrar retrocompatibilidade de callbacks (on_token, on_tool, on_tool_result, on_permission)"

  tests:
    - cmd: "python -c 'from nyx.agent.loop import AgentLoop; print(\"ok\")'"
      deve_passar: true
    - cmd: "find nyx/agent/loop -name '*.py' -exec wc -l {} +"
      esperado: "nenhum arquivo > 400 linhas"
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "nyx/agent/loop.py arquivo não existe (só como pacote)"
    - "Pacote nyx/agent/loop/ com 4+ submódulos"
    - "from nyx.agent.loop import AgentLoop funciona"
    - "Callbacks on_token, on_tool, on_tool_result, on_permission preservados"
    - "Gauntlet rapido passa"
```

---

# Sprint DEBT-01 — Split loop.py

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-18

## Contexto

- Limite de 800 linhas (GUIDE.md). `loop.py` tem 739 — próximo do estouro.
- Responsabilidades misturadas: inicialização do agent, loop de iteração, parse de actions, integração com tools, compactação, sumarização.

## Problema

Arquivo monolítico crescendo desordenadamente. Próxima adição ultrapassa o limite.

## Solução

Fragmentar em pacote `nyx/agent/loop/`:

```
nyx/agent/loop/
├── __init__.py           # re-export de AgentLoop, AgentStatus, AgentState, PermissionCallback
├── _types.py             # AgentState (enum), AgentStatus (dataclass), PermissionCallback (Protocol)
├── _constants.py         # LLM_TIMEOUT, ACTION_TO_TOOL, PARAM_REMAP, _remap_params()
├── _iteration.py         # função async iterate(agent, user_input) -> AgentStatus
└── _core.py              # classe AgentLoop (init, run, reset, close, get_context_info, maybe_summarize)
```

### Regra de fragmentação

Ler `loop.py` atual (linhas 1-739). Alocar:

- Linhas ~1-50 (imports, logger) → vão em `_core.py` + replicados conforme necessário.
- Linhas ~55-92 (`LLM_TIMEOUT`, `ACTION_TO_TOOL`, `PARAM_REMAP`, `_remap_params`) → `_constants.py`.
- `AgentState` enum + `AgentStatus` dataclass + `PermissionCallback` type → `_types.py`.
- Classe `AgentLoop` + métodos → `_core.py`.
- O laço principal de iteração (se for um método complexo com > 80 linhas) → extrair para função em `_iteration.py` chamada pelo método `run`.

### Import side-effect

`__init__.py` simples re-export, sem side-effects:

```python
from nyx.agent.loop._core import AgentLoop
from nyx.agent.loop._types import AgentStatus, AgentState, PermissionCallback

__all__ = ["AgentLoop", "AgentStatus", "AgentState", "PermissionCallback"]
```

## Procedimento

1. Ler `nyx/agent/loop.py` inteiro.
2. Identificar blocos por responsabilidade.
3. Criar diretório `nyx/agent/loop/` e os 5 arquivos vazios.
4. Mover código, ajustando imports relativos.
5. Deletar `nyx/agent/loop.py` **original** (arquivo único).
6. `python -c 'from nyx.agent.loop import AgentLoop; import asyncio; asyncio.run(AgentLoop("/tmp").close())'` — smoke test.
7. Ruff limpo.
8. Gauntlet.

## Diff esperado

```
- 1 arquivo removido (loop.py 739 linhas)
+ 5 arquivos criados (loop/*)
Δ linhas líquidas ~= 0
```

## Comando de verificação

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# 1. Estrutura
test -f nyx/agent/loop/__init__.py && echo "pacote OK"
test ! -f nyx/agent/loop.py && echo "arquivo antigo removido OK"

# 2. API pública
python -c "
from nyx.agent.loop import AgentLoop, AgentStatus, AgentState
print('API OK')
"

# 3. Tamanho dos submódulos
find nyx/agent/loop -name '*.py' -exec wc -l {} + | awk '$1 > 400 { print; exit 1 }' && echo "tamanhos OK"

# 4. Gauntlet
./run.sh --gauntlet --only rapido
```

## Critério binário

- [ ] Pacote `nyx/agent/loop/` existe, arquivo único `loop.py` não
- [ ] 5 submódulos presentes
- [ ] Nenhum submódulo > 400 linhas
- [ ] API pública funciona
- [ ] Ruff limpo
- [ ] Gauntlet rapido passa
- [ ] Commit: `refactor: split loop.py 739 linhas em pacote por responsabilidade`

## Guardrails anti-engodo

**NÃO marque como concluída se:**
- IA moveu tudo pra `_core.py` (400+ linhas) sem fragmentar — burla do objetivo.
- Renomeou `loop.py` sem transformar em pacote.
- Quebrou callback (test: rodar o REPL e verificar stream funcionando).

## Validação humana

```bash
ls nyx/agent/loop/
find nyx/agent/loop -name '*.py' -exec wc -l {} +
git show --stat HEAD
./run.sh  # deve abrir normal
```

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Circular imports entre submódulos | `_types.py` e `_constants.py` não importam nada do pacote |
| Perda de callback | Testar manualmente: `/status`, enviar mensagem e ver streaming |

---

*"A simplicidade é a arte de dividir sem mutilar." -- anônimo*
