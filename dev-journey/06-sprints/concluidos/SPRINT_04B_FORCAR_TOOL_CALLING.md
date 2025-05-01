# Sprint 4b: Forçar Tool Calling Correto

**Objetivo:** Garantir que o modelo qwen3:4b execute tool calls (Write, Edit)
de forma consistente, resolvendo a incompatibilidade entre o shim OpenAI do
Nyx TUI e a API nativa do Ollama.

---

## Diagnóstico (comprovado)

### O modelo funciona via API nativa
```bash
curl -sf http://127.0.0.1:11435/api/chat \
  -d '{"model":"qwen3:4b","messages":[...],"tools":[...],"think":false,"stream":false}'
```
Resultado: `tool_calls` retornado corretamente com name="Write" e argumentos.

### O modelo falha via endpoint OpenAI-compatible
```bash
curl -sf http://127.0.0.1:11435/v1/chat/completions \
  -d '{"model":"qwen3:4b","messages":[...],"tools":[...],"max_tokens":500}'
```
Resultado: o campo `reasoning` consome todos os tokens. `tool_calls` nunca é gerado.

### Causa raiz
O qwen3 tem modo "thinking" ativado por padrão. Para desabilitar:
- API nativa: `"think": false` → **funciona**
- Endpoint /v1/: não tem equivalente → `reasoning` sempre ativo → tokens esgotam

O `--thinking disabled` do Nyx TUI não propaga `think=false` para o Ollama.

---

## Soluções possíveis

### Solução 1: Proxy de compatibilidade (recomendada)
Criar um proxy Python leve que fica entre o Nyx TUI e o Ollama:

```
Nyx TUI (porta 11436) → proxy Python → Ollama (porta 11435)
```

O proxy:
1. Recebe request no formato OpenAI `/v1/chat/completions`
2. Converte para formato nativo Ollama `/api/chat`
3. Adiciona `"think": false` na request
4. Converte a resposta nativa de volta para formato OpenAI
5. Garante que `tool_calls` está no formato correto

Implementação: ~150 linhas de Python com httpx.

### Solução 2: Modelfile com /nothink
Criar um Modelfile que força o qwen3:4b a não usar thinking:

```
FROM qwen3:4b
PARAMETER num_gpu 20
SYSTEM "Voce e Nyx. Use tools sempre. Nunca descreva o que faria."
TEMPLATE """{{- if .System }}{{ .System }}{{ end }}
{{ range .Messages }}{{ .Role }}: {{ .Content }}
{{ end }}
/nothink"""
```

Problema: pode não funcionar com tool calling via /v1/.

### Solução 3: Aumentar max_tokens drasticamente
Se o `reasoning` consome ~300 tokens, aumentar `max_tokens` para 2000+
garante que sobra espaço para o tool_call após o reasoning.

Problema: aumenta latência e custo de VRAM.

### Solução 4: Patch do cli.mjs
Editar o `reference/dist/cli.mjs` para adicionar `"think": false`
na request quando o provider é local.

Problema: arquivo de 19MB, difícil de manter.

---

## Plano de execução (Solução 1: Proxy)

### 4b.1 Criar proxy Python

Arquivo: `nyx/proxy.py`

```python
"""Proxy OpenAI -> Ollama nativa com think=false."""
import httpx
from fastapi import FastAPI, Request
import uvicorn

app = FastAPI()
OLLAMA_URL = "http://127.0.0.1:11435"

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()

    # Converter formato OpenAI -> Ollama nativo
    ollama_body = {
        "model": body["model"],
        "messages": body["messages"],
        "tools": body.get("tools"),
        "think": False,  # CRITICO: desabilita reasoning
        "stream": body.get("stream", False),
        "options": {
            "num_gpu": 20,
            "num_ctx": 4096,
            "temperature": body.get("temperature", 0.3),
        }
    }

    async with httpx.AsyncClient(timeout=300) as client:
        resp = await client.post(f"{OLLAMA_URL}/api/chat", json=ollama_body)
        ollama_data = resp.json()

    # Converter resposta Ollama nativo -> formato OpenAI
    openai_response = convert_to_openai_format(ollama_data)
    return openai_response
```

### 4b.2 Atualizar run.sh

```bash
# Iniciar proxy antes do Nyx TUI
./venv/bin/python nyx/proxy.py --port 11436 &
PROXY_PID=$!

# Apontar Nyx TUI para o proxy
export OPENAI_BASE_URL="http://127.0.0.1:11436/v1"
```

### 4b.3 Atualizar install.sh

Adicionar dependências do proxy:
```
fastapi
uvicorn
```

### 4b.4 Testar

```bash
./run.sh
> crie o arquivo /tmp/test.py com print("funciona")
# Deve chamar Write tool e criar o arquivo
> edite /tmp/test.py e troque "funciona" por "funciona perfeitamente"
# Deve chamar Edit tool e modificar
```

---

## Verificação

- [ ] Write tool chamada corretamente (arquivo criado no disco)
- [ ] Edit tool chamada corretamente (arquivo modificado)
- [ ] Read, Bash, Grep, Glob continuam funcionando
- [ ] Slash commands continuam funcionando
- [ ] Performance não degradou significativamente
- [ ] Proxy inicia e para com o run.sh

---

## Arquivos a criar/modificar

- `nyx/proxy.py` — proxy OpenAI -> Ollama nativa
- `run.sh` — iniciar proxy + apontar Nyx TUI
- `install.sh` — adicionar deps do proxy
- `requirements.txt` — fastapi, uvicorn
