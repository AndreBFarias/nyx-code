## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P8-B
  title: "Provider Ollama separado + Project context"
  touches:
    - path: nyx/providers/ollama.py
      reason: "Provider Ollama como módulo separado"
    - path: nyx/context/project.py
      reason: "Contexto de projeto automático"
    - path: nyx/agent/loop.py
      reason: "Usar provider em vez de httpx direto"
    - path: scripts/gauntlet/nyx_gauntlet.py
      reason: "2 testes novos"
  origin:
    primary: "Luna/src/core/ollama_client/"
    secondary: "openclaud/src/context/"
  tests:
    - cmd: "./run.sh --gauntlet --only p8_provider"
      timeout: 30
  acceptance_criteria:
    - "OllamaProvider encapsula comunicação com proxy"
    - "ProjectContext detecta tipo de projeto automaticamente"
    - "Loop usa provider em vez de httpx direto"
```

---

# Sprint P8-B -- Provider e Contexto

**Status:** PENDENTE
**Data:** 2026-04-05
**Prioridade:** BAIXA
**Tipo:** Port (Luna -> Python) + Refactor
**Dependências:** P6-B
**Desbloqueia:** --

---

## Implementação

### OllamaProvider (`nyx/providers/ollama.py`)
- Encapsula toda comunicação com o proxy
- `chat(messages, tools, stream)` -- retorna resposta
- `health()` -- verifica se proxy responde
- `models()` -- lista modelos disponíveis
- Retry com backoff exponencial
- Timeout configurável
- Substitui httpx direto no loop.py

### ProjectContext (`nyx/context/project.py`)
- Detecta tipo de projeto automaticamente
- Verifica: package.json, pyproject.toml, Cargo.toml, go.mod, etc.
- Gera contexto: linguagem, framework, estrutura
- `detect(project_root) -> ProjectInfo`
- ProjectInfo: language, framework, structure, entry_points
- Injetado no system prompt

### Testes Gauntlet

| ID | Nome | Validação |
|----|------|-----------|
| P8P-01 | OllamaProvider importa | Provider inicializa com URL |
| P8P-02 | ProjectContext detecta Python | Detecta pyproject.toml ou setup.py |

## Verificação

- [ ] Provider substitui httpx no loop
- [ ] ProjectContext detecta projeto Nyx como Python
- [ ] Retry funciona em caso de timeout
- [ ] 2 testes Gauntlet passando

---

*"A abstração é a essência da engenharia." -- Edsger Dijkstra*
