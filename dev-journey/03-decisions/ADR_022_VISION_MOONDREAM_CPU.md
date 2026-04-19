# ADR-022 — Visão via moondream CPU

**Status:** ACEITO
**Data:** 2026-04-19
**Contexto da Onda:** 22, Bloco 2.5

## Contexto

Sprint VISION-01/02/03 precisa que o REPL entenda imagens coladas pelo usuário (Ctrl+V → `[Image #N]` no buffer). A máquina-alvo de referência é uma RTX 3050 Laptop 4 GB + 16 GiB RAM (Local First, ADR-001).

Orçamento de VRAM atual (medido em idle com REPL aberto):

| Processo | VRAM consumida |
|---|---|
| qwen3:4b via Ollama (num_gpu=12) | ≈ 2.6 GiB |
| Compositor/X + buffers | ≈ 0.4 GiB |
| Folga | ≈ 1.0 GiB (insuficiente para vision model decente em GPU) |

RAM: com Ollama + REPL + processo de visão ocioso, **~14.8 GiB livres** (estimado via `free -g` em idle com stack completa). Há margem para carregar um modelo de visão **em CPU** sem perturbar qwen3 na GPU (ADR-003 VRAM Management).

## Decisão

Usar **moondream2** (vikhyatk/moondream2, HuggingFace) rodando **em CPU** via `transformers` para visão.

- Peso aproximado: **≈ 1.8 GiB residente em RAM** em FP16 (estimativa baseada em spec do modelo: ~1.8B parâmetros efetivos × 2 bytes; não medido empiricamente, a ser confirmado em VISION-01).
- Latência aceita: **~3-5s por imagem** em CPU (estimado; depende do número de tokens gerados na caption/query).
- Carregamento: **lazy** -- só instancia quando há `[Image #N]` real no prompt; libera com TTL se o buffer esfria.
- Licença: **Apache-2.0** (verificada no repositório HuggingFace em 2026-04-19 via API). Compatível com Local First offline.
- Versão: `moondream2` estável. `moondream3-preview` disponível upstream mas em preview; upgrade será reavaliado em sprint futura.

Formato de integração segue ADR-021 (dependência opcional): `transformers` + `torch` + `pillow` viram extras `[vision]`; flag `HAS_MOONDREAM` em runtime; sem a dep, `[Image #N]` é descartado e o prompt segue só com texto.

## Consequências

Positivas:

- VRAM intacta para qwen3 (nenhuma competição por recurso escasso; ADR-003 preservada).
- Totalmente offline após download inicial (Local First).
- Latência ocasional (imagem colada é evento raro vs. tokens textuais).

Negativas:

- CPU spike por 3-5s durante inferência (bloqueia REPL se não for async; mitigação em VISION-01).
- +1.8 GiB de RAM residente mesmo entre inferências (a menos que descarreguemos via TTL; trade-off latência × memória).
- Download inicial de ~3.7 GiB (pesos safetensors FP16) -- one-time, documentado no README.
- Números de VRAM/RAM aqui são **estimados**; benchmark empírico fica a cargo de VISION-01, e esta ADR é atualizada se divergir significativamente.

## Alternativas consideradas

**Alt A: LLaVA-7B (llava-hf/llava-1.5-7b-hf) via Ollama.**
- Contra: exige ≈ 5-6 GiB VRAM mesmo em Q4. **Não cabe** no orçamento (4 GiB total, 2.6 já ocupados por qwen3).
- Contra: qwen3 teria que ser descarregado para carregar LLaVA e re-carregado depois → latência absurda por imagem.
- Rejeitada por inviabilidade de VRAM.

**Alt B: llama.cpp vision (llava.cpp / minicpm-v em GGUF).**
- A favor: roda em CPU, quantização agressiva (Q4_K_M ~2 GiB).
- Contra: modelos de visão em llama.cpp ainda têm qualidade inferior ao moondream em tarefas de OCR/descrição curta.
- Contra: dependência extra (llama-cpp-python) com compilação.
- Rejeitada por qualidade insuficiente para o caso de uso (descrição de screenshot colado).

**Alt C: Qwen-VL / Qwen2-VL local.**
- Contra: versões pequenas (2B) ainda pedem ≈ 4-5 GiB VRAM, mesma restrição do LLaVA.
- Contra: versões CPU-friendly são raras e menos maduras.
- Rejeitada por mesma razão do LLaVA.

**Alt D: API cloud (Claude, GPT-4V, etc.).**
- Contra: viola ADR-001 Local First. Não-negociável.
- Rejeitada imediatamente.

## Referências

- ADR-001 Local First.
- ADR-003 VRAM Management.
- ADR-015 Documentação para continuidade.
- ADR-021 Dependências opcionais (padrão de integração).
- HuggingFace: vikhyatk/moondream2 (licença Apache-2.0).
- Sprint VISION-01 (primeiro consumidor, valida números desta ADR).

*"Quem não pode ver tudo que a máquina grande vê, que veja o essencial com a máquina pequena." -- Sêneca (paráfrase)*
