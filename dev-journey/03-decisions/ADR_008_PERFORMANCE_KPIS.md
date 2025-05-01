# ADR 008: KPIs de Performance Obrigatórios

## Status
ACEITA (2026-04-04)

## Contexto

Nyx-Code roda em hardware limitado (RTX 3050 4GB VRAM). Sem métricas,
é impossível saber se uma mudança melhorou ou piorou a experiência.
O objetivo é ser um serviço premium gratuito para quem não tem acesso
a APIs cloud. Performance é parte da qualidade.

## Decisão

**Toda execução do Gauntlet mede e registra KPIs. Regressões são bloqueantes.**

### KPIs medidos

| Métrica | Baseline | Alerta | Crítico |
|---------|----------|--------|---------|
| Boot time (Ollama pronto) | <30s | >45s | >60s |
| Warmup (primeira inferência) | <90s | >120s | >180s |
| TTFR chat (sem tools) | <15s | >25s | >45s |
| TTFR tool call simples | <20s | >35s | >60s |
| TTFR tool call com conteúdo | <45s | >60s | >120s |
| Tokens/resposta chat | 30-100 | >150 | >300 |
| Tokens/resposta tool call | 200-800 | >1200 | >2000 |
| VRAM em uso estável | <2500MiB | >3000MiB | >3500MiB |
| Tool call success rate | >85% | <70% | <50% |
| Gauntlet total | <25min | >35min | >45min |

### Coleta

O Gauntlet mede automaticamente via:
1. `time.monotonic()` para tempos
2. `response.usage.total_tokens` para tokens
3. `nvidia-smi --query-gpu=memory.used` para VRAM
4. Contagem de tool_calls bem-sucedidos para success rate

### Histórico

Cada execução salva KPIs em `dev-journey/07-reports/gauntlet/`.
O report mostra tendência comparando com execuções anteriores.

## Consequências

### Positivas
- Regressões de performance detectadas antes do merge
- Baseline documentado para comparar modelos (3b vs 4b vs 7b)
- Dados reais para decisões de num_gpu, num_ctx, max_tokens

### Negativas
- Gauntlet leva mais tempo (~2min extra para medir VRAM)
- KPIs variam com temperatura do GPU (não determinístico)

---

*"Não se pode gerenciar o que não se pode medir." -- Peter Drucker*
