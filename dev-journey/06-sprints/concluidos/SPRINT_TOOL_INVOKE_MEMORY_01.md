# SPRINT TOOL-INVOKE-MEMORY-01 — prompt guia qwen3:4b a disparar write_memory

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: TOOL-INVOKE-MEMORY-01
  title: "System prompt e tool description fazem o modelo pequeno chamar write_memory com frase natural"
  onda: 22
  bloco: 2.6
  prioridade: ALTA
  tipo: Bugfix / Infra
  dependencias: [AUTOTUNE-FIX-01]
  desbloqueia: [VALIDATE-ONDA-20, CTX-02, TUI-01, TUI-02]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/prompt.py
      reason: "prompt diz apenas 'write_memory -- só quando o usuário pedir pra lembrar algo estável'; abstrato demais para qwen3:4b. Precisa de verbos-gatilho + exemplo de chamada."
      linhas_alvo: "35-62 (template principal)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tools/write_memory.py
      reason: "ToolDef.description é declarativa, não acionável. Enriquecer com verbos-gatilho para reforçar o casamento com o prompt."
      linhas_alvo: "19-24 (description)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "adicionar CTX-11 que faz roundtrip LLM real com frase natural e valida que tool_calls contém write_memory"
      linhas_alvo: "após CTX-10 (~2858)"

  creates: []
  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Mudar NyxMemory.write() ou sandbox -- feature backend está correta (gauntlet CTX-02/03/04/05 passa)"
    - "Chamar write_memory manualmente quando o LLM não chamar -- gambiarra que viola ADR-002 (infra adapta o modelo)"
    - "Baixar limite de caracteres ou sandbox pra 'facilitar' disparo -- gambiarra"
    - "Adicionar emoji, menção a IA"

  tests:
    - cmd: "./run.sh --gauntlet --only contexto"
      timeout: 300
      esperado: "11/11 APROVADO (inclui CTX-11 novo)"
    - cmd: "validação visual: REPL com 'lembra que eu uso pyenv 3.12 neste projeto' -> box tool ⏺ write_memory + linha └─ OK"
      timeout: 90
    - cmd: "cross-session: depois de /exit, ./run.sh de novo, perguntar 'o que você sabe sobre meu setup?' -> resposta cita pyenv"
      timeout: 120

  acceptance_criteria:
    - "CTX-11 no gauntlet: roundtrip real com 'lembra que uso pyenv 3.12' retorna tool_calls contendo write_memory com file/content/reason não-vazios"
    - "Screenshot da rodada 2 de VALIDATE-ONDA-20 mostra box `⏺ write_memory(...)` + `└─ OK` após prompt natural"
    - "Pasta ~/.nyx/memory/Nyx-Code-*/ tem ao menos 1 arquivo .md após o turno"
    - "FAIL invariantes <= baseline"
```

---

**Status:** CONCLUIDA (commit 815f2fc)
**Data criação:** 2026-04-20
**Origem:** VALIDATE-ONDA-20 rodada 1 descobriu que o LLM não dispara `write_memory` quando o usuário diz "lembra que eu uso pyenv 3.12 neste projeto". O roundtrip é via proxy (think=false, OK) e a tool está registrada (gauntlet CTX-04: tools=35), então o gap está na **camada de decisão do LLM**. ADR-002 é o precedente canônico: infra (proxy) adaptou Ollama para fazer tool_calls funcionarem em geral — agora cabe ao system prompt / tool description fazer o modelo pequeno **decidir** chamar a tool específica.
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

### Observação visual (rodada 1)

Prompt do usuário: `lembra que eu uso pyenv 3.12 neste projeto`

Resposta do Nyx: `nyx/agent/loop/_core.py. Projeto em Python 3.12 com pyenv.`

Iteração: `iter 1` (loop único, sem tool calling). Tool não foi invocada.

### Prompt atual (`nyx/agent/prompt.py:35-62`)

```
USE tools (...) APENAS quando a tarefa exigir:
- Ler/listar/buscar arquivo real (read_file, ...)
- Escrever/editar arquivo (write_file, ...)
- Executar comando (run_command)
- Buscar externo (web_fetch, web_search)
- Gravar memória persistente (write_memory -- só quando o usuário pedir pra lembrar algo estável)
```

A frase `só quando o usuário pedir pra lembrar algo estável` é **abstrata**. Qwen3:4b (modelo pequeno) não sabe decodificar "lembra que..." como a condição de disparo. Modelos maiores (gpt-4, claude) aproximam essa ponte sozinhos; qwen3:4b não.

### Princípio ADR-002

O proxy injeta `think=false` porque o qwen3:4b "thinking" consome todos os tokens antes de gerar tool_calls. **Infra adapta o modelo**. Aqui é o mesmo padrão: a infra (prompt) precisa dizer com exemplos concretos.

---

## Solução proposta

### Parte 1 — prompt.py ganha seção explícita

```python
USE tools ({tools_str}) APENAS quando a tarefa exigir:
- Ler/listar/buscar arquivo real (read_file, list_files, grep_files)
- Escrever/editar arquivo (write_file, edit_file)
- Executar comando (run_command)
- Buscar externo (web_fetch, web_search)
- Gravar memória persistente (write_memory)

DISPARE write_memory SEMPRE que o usuário usar verbos-gatilho seguidos de fato:
  "lembra que ...", "anota que ...", "guarda que ...", "memoriza ...", "fixa ..."
Exemplo de disparo obrigatório:
  Usuário: "lembra que eu uso pyenv 3.12 neste projeto"
  Chame: write_memory(file="ambiente", content="Uso pyenv 3.12 neste projeto.", reason="setup do dev")
Exemplos de NÃO-disparo:
  "você lembra do arquivo X?" (pergunta, não ordem)
  "lembra de rodar o teste" (instrução ao LLM, não fato a persistir)
```

### Parte 2 — write_memory description reforçada

```python
description=(
    "Grava memória persistente sobre o projeto ou desenvolvedor. "
    "USE SEMPRE que o usuário pedir em tom imperativo: 'lembra que ...', "
    "'anota que ...', 'guarda essa decisão ...', 'memoriza ...'. "
    "Armazena em ~/.nyx/memory/<projeto>/. Só para fatos estáveis entre sessões."
)
```

### Parte 3 — CTX-11 no gauntlet

Caso novo que manda uma frase natural via proxy e valida que `tool_calls` contém `write_memory`:

```python
# CTX-11: write_memory disparado por linguagem natural (verifica infra ADR-002)
t = time.monotonic()
try:
    import httpx
    from nyx.agent.prompt import build_system_prompt
    from nyx.agent.tools.registry import ToolRegistry

    registry = ToolRegistry()
    tool_names = registry.tool_names()
    system = build_system_prompt(str(PROJECT_ROOT), tool_names)
    tool_schemas = [
        {"type": "function", "function": {
            "name": t.tool_def.name,
            "description": t.tool_def.description,
            "parameters": {"type": "object", "properties": t.tool_def.parameters, "required": t.tool_def.required},
        }}
        for t in registry.all_tools()
    ]

    payload = {
        "model": self._model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": "lembra que eu uso pyenv 3.12 neste projeto"},
        ],
        "tools": tool_schemas,
        "stream": False,
    }
    async with httpx.AsyncClient(timeout=180) as client:
        r = await client.post(f"{self._proxy}/v1/chat/completions", json=payload)
        data = r.json()
    msg = data["choices"][0]["message"]
    tool_calls = msg.get("tool_calls") or []
    chose_write_memory = any(
        c.get("function", {}).get("name") == "write_memory" for c in tool_calls
    )
    self._add(
        "CTX-11",
        "write_memory por linguagem natural",
        "contexto",
        chose_write_memory,
        time.monotonic() - t,
        details=f"tool_calls={len(tool_calls)} write_memory={chose_write_memory}",
    )
except Exception as e:
    self._add("CTX-11", "write_memory por linguagem natural", "contexto", False, time.monotonic() - t, error=str(e))
```

(Signature exato de `ToolRegistry.tool_names()` / `all_tools()` será verificado no momento — adapto ao API real; o teste é o que importa.)

---

## Diff esperado

```
~ 3 arquivos modificados
+ ~30 linhas em prompt.py (few-shot + verbos)
+ ~5 linhas em write_memory.py (description expandida)
+ ~40 linhas em nyx_gauntlet.py (CTX-11)
```

---

## Comandos de verificação

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before.txt)

# Fix nos 3 arquivos

./run.sh --smoke
./run.sh --gauntlet --only contexto   # esperado 11/11

# Validação visual (kitty + scrot):
# 1. Abrir TUI
# 2. Digitar "lembra que eu uso pyenv 3.12 neste projeto" + Enter
# 3. Capturar screenshot: deve ter box ⏺ write_memory(...) + └─ OK
# 4. Rodar /memory: deve listar 1 entrada
# 5. Ctrl+D, ./run.sh de novo
# 6. Perguntar "o que você sabe sobre meu setup?" -> cita pyenv

bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
```

---

## Critério binário de aceite

- [ ] CTX-11 retorna PASS (tool_calls contém write_memory)
- [ ] Screenshot rodada 2 mostra `⏺ write_memory(...)` + `└─ OK`
- [ ] `ls ~/.nyx/memory/Nyx-Code-*/` mostra >=1 `.md` após turno
- [ ] Gauntlet contexto 11/11 + rapido 18/18
- [ ] FAIL invariantes <= baseline

---

## Gambiarras específicas

1. **Chamar write_memory manualmente no loop quando detectar "lembra que"** — bypass de LLM, quebra arquitetura (o loop decide com base em tool_calls, não em regex).
2. **Expandir tool description com texto irrelevante pra inflar peso** — ruído aumenta confusão. Texto acionável é o que ajuda.
3. **Forçar `tool_choice: required`** — aplicaria a todas as chamadas, inclusive saudações. Gambiarra.
4. **Colocar lista de verbos em um arquivo externo e importar** — overhead sem ganho; 5-6 verbos cabem inline.

---

## Proof-of-work obrigatório

- `./run.sh --gauntlet --only contexto` output mostrando CTX-11 PASS com `write_memory=True`.
- Screenshot da TUI pós-turno com frase natural: box `⏺ write_memory(...)` visível.
- `cat ~/.nyx/memory/Nyx-Code-*/MEMORY.md` mostrando entrada criada.
- 2ª sessão: screenshot de "o que você sabe sobre meu setup?" citando pyenv.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| Few-shot inflar o prompt e degradar respostas normais | Mantê-lo curto (6-8 linhas); segmentar de "USE tools APENAS quando" |
| Verbo-gatilho disparar falso positivo ("lembra de rodar o teste") | Exemplo de NÃO-disparo explícito no prompt |
| Qwen3:4b continuar ignorando mesmo com few-shot | Plano B: ajustar também ToolDef e testar `tool_choice: auto` no payload — se persistir, cria TOOL-INVOKE-MEMORY-02 com abordagem router LLM |

---

*"A instrução precisa: o mapa; o modelo pequeno: o caminhante. Sem mapa claro, ele toma caminho errado." — ADR-002 parafraseado*
