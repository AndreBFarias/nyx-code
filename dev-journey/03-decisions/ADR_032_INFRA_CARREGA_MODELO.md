# ADR-032 — A INFRA CARREGA O MODELO NAS COSTAS

**Status:** ACEITO
**Data:** 2026-06-01
**Onda:** 36 (RESSURREIÇÃO)
**Sprint origem:** auditoria 2026-05-31/06-01 (crash + OOM + UX)

## Contexto

O Nyx-Code existe para uma pessoa que tem um modelo fraco (`qwen2.5-coder:3b`)
e um PC ruim (RTX 3050 4GB), com Chrome, Spotify e Discord abertos ao mesmo
tempo. A tese do projeto, declarada pelo dono, é direta:

> "Apesar do modelo ser fraco, o pior do mundo, apesar do PC ser horrível, a
> nossa infra é tão boa que torna o modelo bom."

Isso não é slogan: é a régua de toda decisão técnica. Quando algo vai mal
(lentidão, OOM, resposta ruim), existem dois caminhos. O fácil terceiriza o
problema para o bolso do usuário: "use um modelo maior", "compre uma GPU
melhor". O difícil é o único aceitável aqui: **fazer a infra absorver o
limite do hardware**.

Trocar de modelo ou de placa como "solução" trai exatamente quem o projeto
quer proteger — quem não tem dinheiro para uma A100. Ver [[ADR-034]].

## Decisão

**A solução NUNCA é trocar de modelo nem trocar de placa de vídeo. A solução é
sempre melhorar a infra.**

O modelo padrão (`qwen2.5-coder:3b`, ADR-031) e o hardware-alvo (RTX 3050 4GB)
são PREMISSAS fixas, não variáveis de ajuste. Diante de um problema de
desempenho ou memória, as únicas alavancas legítimas são de infra:

- Quantização de KV cache (`OLLAMA_KV_CACHE_TYPE`, INFRA-KVCACHE-QUANT-01).
- Flash attention (`OLLAMA_FLASH_ATTENTION`).
- `num_ctx` / `num_gpu` adaptativos à VRAM livre real.
- Degradação graciosa e reanimação de GPU pós-OOM (ADR-003, stack INFRA-OOM-*).
- Classifier de intent, retry de idioma, parser de tool-call resiliente — a
  pilha que eleva o modelo bruto (INFRA-MODEL-AGNOSTIC-01).

Modelo cloud está fora por [[ADR-001]] (Local First). Modelo maior está fora
por hardware. A engenhosidade fica toda na infra.

## Consequências

### Positivas
- A identidade do projeto fica protegida de atalhos que a esvaziariam.
- Cada gargalo vira uma oportunidade de infra mais inteligente, acumulável.

### Negativas / custo aceito
- Resolver na infra é mais difícil e mais lento que trocar o hardware. Aceitamos
  o custo: é o trabalho que entrega valor a quem o projeto serve.

## Enforcement

- Propostas de "trocar modelo/placa para resolver X" são rejeitadas em review.
- `NYX_MODEL` e flags como `--4b` existem como opt-in do usuário (paridade de
  hardware sem disputa), nunca como solução imposta a um problema de infra.
- Toda sprint de performance/memória declara qual alavanca de INFRA usou e
  traz proof runtime real (medição antes/depois).

## Referências
- [[ADR-001]] (Local First) — sem cloud.
- [[ADR-003]] (VRAM Management) — num_gpu/num_ctx, stack OOM.
- [[ADR-031]] (Model Choice) — qwen2.5-coder:3b escolhido por benchmark; premissa fixa.
- [[ADR-034]] (Feito para quem não tem A100) — a missão.
- Memória do projeto: `project_alma_infra_sobre_hardware`.

---

*"Modelo errado é gambiarra arquitetural disfarçada de pragmatismo. Trocar de
placa para fugir de um bug de infra é a mesma gambiarra com fatura mais cara."*
