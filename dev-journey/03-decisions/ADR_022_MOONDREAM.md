# ADR-022 — Visão via moondream em CPU puro

**Status:** ACEITO
**Data:** 2026-05-17
**Contexto da Onda:** 22, Bloco 6, VISION-01

## Contexto

O modelo padrão do Nyx (qwen2.5-coder:3b, definido em ADR-031) é text-only.
A Onda 22 adiciona capacidade de visão (descrição e análise de imagens).

Na máquina-alvo (RTX 3050 4 GB), qwen2.5-coder:3b consome ~2.5 GB de VRAM
quando quente. moondream consome ~1.7 GB. Rodar ambos simultâneos na GPU
ultrapassa o orçamento e força swap caro do Ollama.

Alternativas consideradas:

- **(a) moondream em CPU puro (`num_gpu=0`)** — latência 2-8 s por imagem;
  o modelo de chat permanece quente; sem orquestração de VRAM.
- **(b) swap VRAM (Luna-style)** — descarrega chat, sobe moondream,
  processa, restaura. Latência menor mas complexidade alta e quebra de
  streaming entre os turnos.
- **(c) qwen2.5-vl:3b no lugar do modelo de chat** — perde qualidade de
  código e raciocínio em troca de visão integrada.

## Decisão

Moondream em CPU puro. Invocação via `POST {OLLAMA_URL}/api/generate`
com payload contendo `options: {"num_gpu": 0, "num_ctx": 2048}` para
forçar inferência fora da GPU.

Wrapper: `nyx/providers/vision_client.py` (HTTP cliente).
Fachada: `nyx/agent/services/vision_service.py` (cache + fallback).

## Consequências

- **Positiva:** o modelo de chat permanece quente — latência de chat não
  é afetada por uma chamada de visão.
- **Positiva:** sem orquestração de VRAM — sprint simples e mecanicamente
  robusta.
- **Positiva:** cache local por sha256 (arquivo + prompt) evita refazer
  inferências caras.
- **Negativa:** descrição de imagem leva 2-8 s em CPU. Aceitável para
  caminho não-quente (descrição sob demanda, não streaming contínuo).
- **Futuro:** se o hardware permitir, criar `vram_swap_service.py`
  implementando pipeline (b).

## Pontos de integração

- `OLLAMA_URL` vem de `nyx/config/defaults.py` (fonte única, ADR-013).
- Cache em `~/.nyx/vision_cache/<sha256>.txt` (segue convenção `~/.nyx/`
  de memory/sessions).
- `VisionService.is_available()` consulta `/api/tags` — não crasha quando
  moondream ausente; retorna `False` e a fachada retorna sentinela
  `"[Imagem: visão indisponível — rode \`./install.sh --vision\`]"`.

## Referências

- AUDIT-EXT-01 finding O-01 (barra de progresso absorvida nesta sprint).
- ADR-001 Local First.
- ADR-003 VRAM Management.
- ADR-013 Integração obrigatória.
- ADR-031 Modelo padrão qwen2.5-coder:3b.

*"Lento no lugar certo é mais rápido que rápido no lugar errado." — anônimo*
