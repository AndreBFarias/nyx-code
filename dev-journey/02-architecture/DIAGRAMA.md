# Arquitetura Nyx-Code

## Fluxo completo

```
┌─────────────────────────────────────────────────────────────┐
│                        run.sh                                │
│  1. Kill Ollama/Proxy anteriores                             │
│  2. Inicia Ollama (:11435) com OLLAMA_MODELS=./models       │
│  3. Warmup do modelo (num_gpu=12, think=false)               │
│  4. Inicia Proxy (:11436)                                    │
│  5. Inicia OpenClaude (TUI)                                  │
│  6. Cleanup ao sair (trap EXIT)                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌────────────────────────────────────┐
        │         OpenClaude (TUI)             │
        │  Node.js | Interface interativa      │
        │  Slash commands | Tool calling        │
        │  OPENAI_BASE_URL=:11436/v1           │
        └──────────────┬──────────────────────┘
                       │ /v1/chat/completions
        ┌────────────────────────────────────┐
        │         Proxy  (:11436)              │
        │  nyx/proxy.py (aiohttp)              │
        │                                      │
        │  Recebe: formato OpenAI              │
        │  Converte: /v1/ -> /api/chat         │
        │  Injeta: think=false                  │
        │  Injeta: num_gpu=12, num_ctx=4096    │
        │  Retorna: formato OpenAI + tool_calls │
        └──────────────┬──────────────────────┘
                       │ /api/chat (nativo)
        ┌────────────────────────────────────┐
        │         Ollama  (:11435)             │
        │  qwen3:4b | 12/37 layers na GPU     │
        │  ~1.2GB VRAM | RTX 3050             │
        │  Tool calling nativo                  │
        │  OLLAMA_MODELS=./models              │
        └─────────────────────────────────────┘
```

## Por que o Proxy existe (ADR-002)

O endpoint `/v1/chat/completions` do Ollama (compatível OpenAI) não propaga
o campo `think=false` para modelos qwen3. Sem essa flag, o modelo gasta
todos os tokens no reasoning interno e nunca gera `tool_calls`.

O proxy converte para a API nativa (`/api/chat`) onde `think=false` funciona.

## Gestão de VRAM (ADR-003)

RTX 3050: 4096 MiB total. Com `num_gpu=12` (de 37 layers), o modelo
usa ~1.2GB. Sobram ~2.8GB para KV cache, contexto e sistema.

Com todas as layers (`num_gpu=37`): 3.3GB + contexto = OOM frequente.
