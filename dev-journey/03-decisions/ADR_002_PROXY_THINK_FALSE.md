# ADR 002: Proxy com think=false

## Status
ACEITA (2026-04-04)

## Contexto

O qwen3:4b tem modo "thinking" ativado por padrão. Quando o openclaude
faz requests via endpoint /v1/chat/completions (OpenAI-compatible), o
Ollama não propaga o campo think=false. O reasoning consome todos os
tokens e tool_calls nunca é gerado.

Comprovado via testes:
- API nativa (/api/chat) com think=false: tool_calls funciona
- Endpoint /v1/ sem think=false: reasoning consome tudo, sem tool_calls

## Decisão

**Proxy Python (aiohttp) entre openclaude e Ollama que injeta think=false.**

```
openclaude -> proxy (:11436) -> Ollama (:11435)
                    |
                    +-> Converte /v1/ para /api/chat
                    +-> Injeta think=false
                    +-> Injeta num_gpu e num_ctx
                    +-> Converte resposta de volta para formato OpenAI
```

### Configuração

```env
NYX_PROXY_PORT=11436
NYX_OLLAMA_PORT=11435
NYX_NUM_GPU=12
NYX_NUM_CTX=4096
```

## Consequências

### Positivas
- Tool calling funciona (Write, Edit, Read, Bash, Glob, Grep)
- Controle total sobre parâmetros enviados ao Ollama
- Sem OOM (num_gpu=12 usa ~1.2GB de 4GB)
- Respostas mais rápidas (sem reasoning)

### Negativas
- Processo extra (proxy Python) rodando em background
- Sem streaming (proxy força non-streaming para estabilidade)
- Latência adicional mínima (~10ms por request)

## Implementação

Arquivo: `nyx/proxy.py`
Iniciado automaticamente pelo `run.sh`
Parado automaticamente no cleanup (trap EXIT)
