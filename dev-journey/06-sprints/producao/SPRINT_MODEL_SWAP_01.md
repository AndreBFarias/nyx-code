# SPRINT MODEL-SWAP-01 — Avaliar modelos alternativos non-thinking

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: MODEL-SWAP-01
  title: "Avaliar e escolher modelo Ollama alternativo non-thinking compatível com chat curto em PT-BR + tool calling"
  onda: 23
  bloco: 23.0 Performance
  prioridade: ALTA
  tipo: Pesquisa+Decisão
  dependencias: []
  desbloqueia: [LANG-ENFORCE-01]
  origem: "Investigação de LANG-ENFORCE-01 (2026-05-17 sessão) demonstrou que Qwen3-4B-Thinking-2507 é arquiteturalmente incompatível com a meta: (a) com think=false produz thinking-as-content em inglês saturado; (b) com think=true consome num_predict inteiro em thinking sem chegar à resposta. Modelo não-thinking é pré-requisito."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/.env
      reason: "NYX_MODEL muda para o modelo escolhido após avaliação"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "DEFAULT_MODEL alinha com a nova escolha"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Comentários sobre modelos suportados; flags --3b/--4b/--7b mantidas"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_002_PROXY_THINK_FALSE.md
      reason: "Anotar que think adaptativo só funciona em modelos não-thinking-by-default"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_031_MODEL_CHOICE.md
      reason: "Decisão arquitetural: modelo escolhido + critérios + benchmark literal"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/fixtures/model_compare.py
      reason: "Benchmark literal comparando 3+ modelos nas mesmas 7 perguntas-tipo (lat + PT-BR rate)"

  removes: []

  n_to_n_pairs:
    - descricao: "Modelo padrão aparece em .env, defaults.py, run.sh, GUIDE.md, GAUNTLET_REPORT — fonte única em defaults.py"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
        - /home/andrefarias/Desenvolvimento/Nyx-Code/.env

  forbidden:
    - "Escolher modelo sem rodar benchmark literal nas 7 perguntas-tipo"
    - "Trocar modelo sem ADR documentando trade-off (lang_rate vs latência vs VRAM)"
    - "Quebrar config existente do usuário (qwen3:4b continua suportado, só não é mais padrão)"
    - "Modelo cloud (ADR-001 Local First)"
    - "Modelo > 4 GB GGUF (não cabe na RTX 3050 4GB com num_gpu razoável)"
    - "Emoji"

  tests:
    - cmd: "./venv/bin/python scripts/gauntlet/fixtures/model_compare.py"
      timeout: 1800
      deve_passar: true
      nota: "Roda os 3 modelos candidatos, grava logs/model_compare.json com lat + PT-BR rate"
    - cmd: "test -f dev-journey/03-decisions/ADR_031_MODEL_CHOICE.md"
      timeout: 5
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "scripts/gauntlet/fixtures/model_compare.py existe e benchmarka >=3 modelos: qwen3:4b atual, qwen2.5-coder:3b, qwen2.5-coder:7b"
    - "Cada modelo testado nas 7 perguntas-tipo de PERF-INFERENCE-01 com 3 amostras cada"
    - "Métricas medidas: P50 latência, P95 latência, lang_pt_br_rate, tool_call_success_rate (1 caso), VRAM pico"
    - "ADR-031 criado com tabela comparativa e justificativa de escolha"
    - "Critérios da escolha documentados: (1) lang_pt_br_rate >=95% em chat curto, (2) tool call funcional, (3) lat P50 <=8s 'oi'"
    - ".env e defaults.py atualizados se modelo padrão muda"
    - "Run.sh --smoke continua passando com modelo escolhido"
    - "Documentação atualizada (GUIDE.md / GAUNTLET_REPORT) com novo padrão"
    - "PT-BR; zero emoji; zero menção a IA"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-17
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
**Origem:** descoberta crítica durante investigação de LANG-ENFORCE-01: Qwen3-Thinking-2507 é arquiteturalmente incompatível com chat curto em PT-BR.

---

# Sprint MODEL-SWAP-01

## Problema (medido)

Investigação 2026-05-17 com modelo Qwen3-4B-Thinking-2507:

| Config | Resultado |
|---|---|
| `think=false`, `num_predict=80` | Content = thinking-in-english truncado, zero resposta real |
| `think=false`, `num_predict=1024` | Content = thinking-in-english longo, ainda inglês |
| `think=true`, `num_predict=80` | Content vazio (80 tokens consumidos em thinking field) |
| `think=true`, `num_predict=1024` | Content vazio (1024 tokens consumidos sem chegar à resposta) |
| `think=true`, `num_predict=512` + system curto | Funcionou! Content "Oi!" em PT-BR após 489 tokens de thinking |

Modelo precisa de **system prompt MUITO específico + num_predict alto** para responder em PT-BR. Não é solução escalável.

## Candidatos a avaliar

| Modelo | Razão |
|---|---|
| `qwen2.5-coder:3b` | Non-thinking, especializado em tool calling, ~2GB |
| `qwen2.5-coder:7b` | Non-thinking, mais capacidade, ~4GB (cabe apertado em 4GB VRAM) |
| `llama3.2:3b` | Non-thinking, suporte multilíngue declarado pra PT-BR, ~2GB |

## Critério de escolha (matriz de decisão)

| Critério | Peso | Como medir |
|---|---|---|
| lang_pt_br_rate em chat | 35% | Fixture perf_inference.py --check-lang |
| Latência P50 chat | 25% | Fixture perf_inference.py |
| Tool calling funcional | 25% | 1 caso "leia README" com tool Read |
| VRAM em uso (4GB cap) | 15% | nvidia-smi durante inferência |

Modelo escolhido = maior pontuação ponderada com lang_rate ≥ 90% e tool calling = OK.

## Verificação

```bash
./venv/bin/python scripts/gauntlet/fixtures/model_compare.py
# Gera logs/model_compare.json
# Imprime tabela: modelo | p50 | p95 | lang_rate | tool_ok | vram_pico
```

---

*"Modelo errado é gambiarra arquitetural disfarçada de pragmatismo." -- princípio de escolha técnica*
