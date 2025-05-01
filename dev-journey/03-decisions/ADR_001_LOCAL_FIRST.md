# ADR 001: Local First

## Status
ACEITA (2026-04-03)

## Contexto

Nyx-Code roda 100% offline via Ollama local na RTX 3050 (4GB VRAM).
Nenhuma API externa é necessária para funcionar. O modelo qwen3:4b
roda localmente com tool calling via proxy.

## Decisão

**Ollama local é o único provider. Não há fallback para cloud.**

### Hierarquia

```
1. Ollama local (:11435) via proxy (:11436)
2. Erro gracioso (sem fallback externo)
```

### Na prática

- Sem internet = funciona 100%
- Sem API key de cloud = funciona 100%
- ANTHROPIC_API_KEY no .env = apenas para auth da TUI, não para API calls
- Toda request vai para Ollama via proxy

## Consequências

### Positivas
- Zero dependência de internet
- Privacidade: dados nunca saem da máquina
- Custo: zero
- Latência previsível

### Negativas
- Qualidade limitada pelo hardware (qwen3:4b em RTX 3050)
- Tool calling mais lento que API cloud (~10-30s por turno)

## Enforcement

O run.sh configura OPENAI_BASE_URL para o proxy local.
Nenhuma variável aponta para API externa.
