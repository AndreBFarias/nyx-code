# ADR 003: Gerenciamento de VRAM

## Status
ACEITA (2026-04-04)

## Contexto

RTX 3050 Laptop GPU: 4096 MiB VRAM total.
O qwen3:4b com todas as 37 layers na GPU usa ~3.3GB, sobrando
apenas ~700MB para KV cache e contexto. Com o system prompt
complexo da TUI (9 tools + contexto), OOM é frequente.

Testes de OOM:
- num_gpu=37 (todas): 3.3GB -> OOM com tools
- num_gpu=20: 1.6GB -> funciona mas instável com contexto grande
- num_gpu=15: 1.4GB -> estável mas lento
- num_gpu=12: 1.2GB -> estável, sem OOM, performance aceitável

## Decisão

**num_gpu=12 como padrão. Configurável via NYX_NUM_GPU no .env.**

### Cálculo

```
VRAM total:    4096 MiB
Modelo (12L):  ~1200 MiB
KV cache:      ~300 MiB (num_ctx=4096)
Compute:       ~100 MiB
Sistema:       ~200 MiB
--------------------------
Livre:         ~2296 MiB (margem segura)
```

### Trade-off

| num_gpu | VRAM | Velocidade | Estabilidade |
|---------|------|-----------|-------------|
| 37 | 3.3GB | Rápido | OOM frequente |
| 20 | 1.6GB | Médio | Instável |
| 15 | 1.4GB | Médio-lento | Estável |
| 12 | 1.2GB | Lento | Muito estável |

## Consequências

### Positivas
- Zero OOM em operação normal
- Modelo fica carregado por mais tempo (keep_alive)
- Sobra VRAM para desktop e outras aplicações

### Negativas
- ~60% das layers rodam em CPU (mais lento)
- Respostas ~2x mais lentas que full GPU

## Configuração

```env
NYX_NUM_GPU=12    # Layers na GPU (default: 12 de 37)
NYX_NUM_CTX=4096  # Tamanho do contexto
NYX_VRAM_MAX=2.5  # Limite em GB (referência)
```

## Enforcement

O proxy (nyx/proxy.py) injeta num_gpu e num_ctx em toda request.
O run.sh faz warmup com os mesmos parâmetros.

## Revisão empírica 2026-05-25 (RTX 3050 4GB)

Auditoria pós-ONDA-30 detectou padrão de 23 OOMs consecutivos em 4 dias com
`num_gpu=12` cap original. Cap reduzido para 6 layers em RTX 3050 4GB.

| VRAM | Cap antigo | Cap novo | Justificativa |
|---|---|---|---|
| 4096 MiB | 12 | **6** | OOM crônico com Chrome + terminal + Spellbook (~600 MiB residual). 6 layers cabem com folga. |
| 6144 MiB | 28 | 28 | sem regressão reportada |
| 8192 MiB | 36 | 36 | sem regressão reportada |

Auditoria longitudinal: `cat ~/.nyx/proxy_stats.json` retorna `oom_recovery_count`.
Padrão para detectar regressão: `grep "OOM degradation step:" logs/proxy.log`.

Opt-in agressivo preserva paridade com hardware sem disputa: `.env`
`NYX_NUM_GPU=12` ou env shell. Auto-tune respeita override do usuário.
