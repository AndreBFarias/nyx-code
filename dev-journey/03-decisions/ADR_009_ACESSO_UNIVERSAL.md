# ADR 009: Acesso Universal -- Premium Gratuito para Hardware Limitado

## Status
ACEITA (2026-04-04)

## Contexto

Nyx-Code existe para permitir que pessoas com hardware modesto (GPU 4GB,
sem acesso a APIs pagas) tenham um agente de código de qualidade.
Cada decisão de arquitetura deve considerar: isso funciona numa RTX 3050?
Isso funciona sem internet? Isso funciona sem cartão de crédito?

## Decisão

**Performance e qualidade são otimizadas para hardware limitado.
O modelo pode demorar o tempo que precisar, desde que o resultado tenha qualidade.**

### Princípios

1. **Sem limite artificial de tokens**: O modelo decide quantos tokens precisa.
   `max_tokens` nunca é forçado pelo proxy -- quem controla é o `num_ctx`.
2. **num_ctx adaptativo**: Começar com 8192. Se VRAM estourar, reduzir para 4096.
   Se sobrar VRAM, subir para 16384.
3. **Tempo não é limitante**: Uma resposta de 60s com tool_call correto vale
   mais que uma resposta de 5s truncada.
4. **VRAM gerenciada, não limitada**: `num_gpu` ajustado para estabilidade,
   não para velocidade. `OLLAMA_MAX_LOADED_MODELS=1`.
5. **Qualidade mensurável**: O Gauntlet mede tool call success rate.
   Regressão abaixo de 85% é bloqueante.

### Configuração de VRAM

```
RTX 3050 (4GB):
  num_gpu=12    num_ctx=8192   -> ~2.5GB, estável
  num_gpu=15    num_ctx=8192   -> ~3.0GB, marginal
  num_gpu=12    num_ctx=16384  -> ~3.2GB, marginal

RTX 3060 (6GB):
  num_gpu=20    num_ctx=16384  -> ~4.0GB, confortável

RTX 4060 (8GB):
  num_gpu=-1    num_ctx=32768  -> full GPU, confortável
```

### Fallback de VRAM

```
1. Tentar num_ctx configurado
2. Se OOM: reduzir num_ctx pela metade
3. Se OOM: reduzir num_gpu para 8
4. Se OOM: erro claro (hardware insuficiente)
```

## Consequências

### Positivas
- Funciona em hardware a partir de GPU 4GB
- Qualidade não é sacrificada por velocidade
- Configuração adaptativa sem intervenção manual

### Negativas
- Respostas podem demorar 30-60s (aceitável)
- Não compete em velocidade com APIs cloud

---

*"A verdadeira liberdade é a ausência de dependência." -- Sêneca*
