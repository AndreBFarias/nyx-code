# ADR 002: Proxy com think=false

## Status
ACEITA (2026-04-04)

## Contexto

O qwen3:4b tem modo "thinking" ativado por padrão. Quando a TUI
faz requests via endpoint /v1/chat/completions (OpenAI-compatible), o
Ollama não propaga o campo think=false. O reasoning consome todos os
tokens e tool_calls nunca é gerado.

Comprovado via testes:
- API nativa (/api/chat) com think=false: tool_calls funciona
- Endpoint /v1/ sem think=false: reasoning consome tudo, sem tool_calls

## Decisão

**Proxy Python (aiohttp) entre a TUI e Ollama que injeta think=false.**

```
Nyx TUI -> proxy (:11436) -> Ollama (:11435)
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

## Adendo 2026-05-16 (ADR-031)

`think` adaptativo descrito acima só funciona em modelos cujo `Modelfile`
suporta o campo `think` (qwen3:* e família). Modelos non-thinking
(qwen2.5-coder:*, qwen2.5:*, llama3.2:*) **retornam HTTP 400 do Ollama**
quando recebem `think=true`. Erro literal observado em testes:
`"qwen2.5-coder:3b" does not support thinking`.

A partir de ADR-031, o modelo padrão é `qwen2.5-coder:3b` (non-thinking).
O proxy continua válido mas, na prática, sempre envia `think=false` para
o default. Mantemos a heurística think adaptativa para suportar
`./run.sh --4b` (qwen3:4b legacy).

Helper canônico para detectar suporte a thinking:
`scripts/gauntlet/fixtures/model_compare.py:supports_thinking()`.
