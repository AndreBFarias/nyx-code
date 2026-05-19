# ADR-031 — Escolha de modelo padrão: qwen2.5-coder:3b

**Status:** ACEITO
**Data:** 2026-05-16
**Contexto da Onda:** 23, Bloco 23.0 Performance
**Sprint origem:** MODEL-SWAP-01
**Substitui (parcialmente):** condições do ADR-002 (think adaptativo)

## Contexto

Durante a investigação da sprint LANG-ENFORCE-01 (2026-05-16) ficou demonstrado
empiricamente que o modelo `qwen3:4b` (Qwen3-4B-Thinking-2507), até então
padrão do Nyx-Code, é **arquiteturalmente incompatível** com a meta declarada
"CLI offline em PT-BR honesto":

| Config testada | Resultado |
|---|---|
| `think=false`, `num_predict=80` | content = thinking-in-english truncado, zero resposta real |
| `think=false`, `num_predict=1024` | content = thinking-in-english longo, ainda inglês |
| `think=true`, `num_predict=80` | content vazio (80 tokens consumidos em thinking) |
| `think=true`, `num_predict=1024` | content vazio (1024 tokens consumidos sem chegar a resposta) |

Resumo: o modelo emite seu chain-of-thought no campo `content` quando
`think=false`, em inglês; com `think=true`, o thinking satura o orçamento
de tokens antes de produzir resposta real. Não é solução escalável via
ajuste de prompt.

LANG-ENFORCE-01 foi reclassificada **PENDENTE -> BLOQUEADA** e a sprint
MODEL-SWAP-01 criada para escolher um modelo non-thinking compatível
com tool calling e PT-BR em chat curto.

## Decisão

Adotar **`qwen2.5-coder:3b`** como modelo padrão do Nyx-Code.

Resumo:
- Tamanho: 1.9 GB (cabe folgado na RTX 3050 4 GB).
- Família: Qwen2.5-Coder (non-thinking, especializado em código + tool calling).
- Suporte a tool calling: via JSON-no-content (parser do Nyx em `nyx/agent/parser.py`
  já cobre este formato).
- VRAM medida: 2484 MiB de pico durante benchmark.

`qwen3:4b` continua suportado via flag `./run.sh --4b` ou `NYX_MODEL=qwen3:4b`
no `.env`, sem regressão de configuração do usuário (em conformidade com a
seção `forbidden` do spec MODEL-SWAP-01).

## Benchmark literal (runtime real)

Script: `scripts/gauntlet/fixtures/model_compare.py`
Output: `logs/model_compare.json` (timestamp 1778982936)
Amostragem: 7 prompts canônicos × 3 amostras + 1 prompt tool-test por modelo.

### Tabela comparativa

| Modelo | P50 (s) | P95 (s) | lang_rate_chat | tool_ok | VRAM pico | Score |
|---|---:|---:|---:|:---:|---:|---:|
| `qwen3:4b` | 5.734 | 11.733 | 54.55% | não | 3268 MiB | **34.6** |
| `qwen2.5-coder:3b` | **1.153** | 12.298 | **100%** | **OK** | 2484 MiB | **96.8** |
| `qwen2.5-coder:7b` | 9.177 | 94.681 | 100% | OK | 2680 MiB | 70.4 |

Notas:
- `lang_rate_chat` exclui prompts de `intent=comando` (slash commands são
  interceptados pelo CLI antes de chegar ao LLM, ver `nyx/agent/commands/`).
- `qwen2.5-coder:3b` em `/help` respondeu em inglês, mas em produção o CLI
  intercepta `/help` antes do proxy.
- `tool_ok` considera **fallback do parser**: qwen2.5-coder emite o JSON
  da chamada no campo `content` em vez do campo nativo `tool_calls`. O
  parser existente (`nyx/agent/parser.py:228+`) extrai esse JSON e ativa
  a tool corretamente. Comportamento equivalente do ponto de vista do
  usuário.
- `qwen2.5-coder:7b` ficou bem em qualidade mas falhou em latência (P95
  ≈ 95 s, pior prompt = "explique cli.py" com 44 s P50; o modelo gera
  saída longa que satura o orçamento de tokens).

### Detalhe por caso (qwen2.5-coder:3b vencedor)

| Prompt | Intent | P50 | Saída literal (preview) |
|---|---|---:|---|
| `oi` | saudacao | 0.64s | "Olá! Como posso ajudar você hoje?" |
| `ola tudo bem` | saudacao | 0.75s | "Olá! Tudo ótimo, e com você? Como posso te ajudar hoje?" |
| `/help` | comando | 0.60s | "Hello! It looks like..." (inglês, mas não chega ao LLM em prod) |
| `liste arquivos no diretorio` <!-- noqa-acento --> | tool-needed | 7.19s | "Para listar os arquivos em um diretório usando Python..." |
| `leia o arquivo README.md` | tool-needed | 1.27s | "Claro, por favor forneça o conteúdo do arquivo..." |
| `quanto e 5+3` | chat | 1.08s | "5 + 3 = 8" |
| `explique o que faz o arquivo cli.py` | tool-needed | 11.47s | "O `cli.py` é um arquivo de script Python..." |
| Tool test (Read README.md) | -- | 1.88s | `{"name": "Read", "arguments": {"file_path": "README.md"}}` -> OK via content-json |

## Matriz de decisão (35/25/25/15)

Pesos definidos no spec MODEL-SWAP-01.

| Critério | Peso | qwen3:4b | qwen2.5-coder:3b | qwen2.5-coder:7b |
|---|---:|---:|---:|---:|
| lang_pt_br_rate em chat | 35% | 54.5 pts | **100 pts** | 100 pts |
| Latência P50 (meta <= 8s) | 25% | 37.8 pts | **100 pts** | 0 pts (9.18s) |
| Tool calling funcional | 25% | 0 pts | **100 pts** | 100 pts |
| VRAM (<=2GB=100, >=4GB=0) | 15% | 40.4 pts | **78.7 pts** | 69.1 pts |
| **Total ponderado** | -- | **34.6** | **96.8** | **70.4** |

`qwen2.5-coder:3b` vence em 3 dos 4 critérios e empata no quarto (lang_rate
em chat real). Diferença sobre o segundo colocado (qwen2.5-coder:7b) é de
26.4 pontos, com vantagem sólida em latência e VRAM.

## Critérios mínimos atendidos (spec MODEL-SWAP-01)

- [x] `lang_pt_br_rate >= 95%` em chat curto -> **100%** (12/12 hits em chat
      após excluir `/help`)
- [x] Tool call funcional -> **OK** via content-json fallback do parser
- [x] Latência P50 chat `oi` <= 8s -> **0.64s**
- [x] VRAM dentro do envelope 4 GB -> **2484 MiB de pico**
- [x] Sem regressão de config do usuário (`qwen3:4b` continua acessível
      via `--4b`)

## Trade-offs explícitos

### Positivos

- **Latência -78%** em chat curto (`oi`: 5.27s -> 0.64s).
- **PT-BR -> 100%** em chat real (era 15-55% no qwen3:4b).
- **VRAM -24%** de pico (3268 -> 2484 MiB), libera ~780 MiB para
  contexto/moondream/buffers.
- **Tool calling não-quebrado**: parser do Nyx já cobre o formato
  emitido por qwen2.5-coder (sem retrabalho).
- **Sem dependência de `think` adaptativo** em chat: modelo non-thinking
  responde direto, sem CoT explícito.

### Neutros

- ADR-002 (think adaptativo) continua válido para usuários do
  `--4b`. Para o padrão, o flag é efetivamente sempre `false` e o proxy
  já degrada `think=true -> false` para modelos non-thinking
  (script `model_compare.py:supports_thinking` documenta a heurística).
- Modelo treinado primariamente para código (Qwen2.5-Coder), não para
  conversa casual. Empiricamente respondeu OK em saudações e small talk;
  monitorar em uso real.

### Negativos

- Modelo não emite `tool_calls` no campo nativo do Ollama -- depende do
  parser de fallback do Nyx. Se um novo modelo for adicionado no futuro
  que use o formato nativo, o parser continua funcionando (parsing JSON
  do content é compatível mesmo quando `tool_calls` está populado).
- 3B parâmetros tem capacidade conceitual menor que 4B/7B. Para tarefas
  agentic complexas (multi-step planning), pode degradar. Mitigação:
  `model_tier.py` ajusta `max_iterations` por hardware/modelo; o tier
  do 3b já é mais conservador.
- Modelo coder pode ser excessivamente literal em conversa filosófica
  ("explique recursividade" -> espera-se mais sucinto; benchmark não
  mediu esse eixo).

## Alternativas consideradas

### Alt A: `qwen2.5-coder:7b`

- A favor: lang_rate 100%, tool_ok, qualidade conceitual maior.
- Contra: P50 9.18s (acima da meta 8s), P95 94.68s (~10x pior que 3b),
  thrash de VRAM e CPU em prompts longos. Em "explique cli.py" ficou 44s
  -- inaceitável para REPL interativo.
- **Rejeitada** por latência fora do envelope.

### Alt B: `llama3.2:3b`

- A favor: suporte multilíngue declarado oficialmente para pt-BR.
- Contra: **não instalado localmente** na máquina alvo; teria que pull
  ~2GB. O usuário marcou como opcional no prompt da sprint. Pode ser
  re-avaliado em sprint futura (MODEL-EVAL-02 se ressurgir demanda).
- **Adiada** por falta de evidência empírica nesta sprint.

### Alt C: Manter `qwen3:4b` e investir em prompt engineering

- A favor: zero migração.
- Contra: investigação detalhada (Checkpoint.md 2026-05-16, item 18)
  demonstrou que é **arquitetural**: modelo gasta orçamento de tokens em
  thinking mesmo com system_prompt explícito em PT-BR. Não é prompt
  problem, é model problem.
- **Rejeitada** com prova empírica.

### Alt D: Modelo cloud (Claude/GPT)

- **Rejeitada de imediato**: viola ADR-001 (Local First).

## Consequências

### Operacionais

- `.env`: `NYX_MODEL=qwen2.5-coder:3b`.
- `nyx/config/defaults.py:15`: `DEFAULT_MODEL = "qwen2.5-coder:3b"`.
- `nyx/proxy.py`, `nyx/agent/commands/system.py`, `nyx/providers/ollama.py`,
  `nyx/agent/loop/_core.py`, `nyx/agent/model_tier.py`,
  `scripts/detect_gpu.py`: trocaram hard-codes `"qwen3:4b"` por import
  `DEFAULT_MODEL` (N-para-N honrado).
- `run.sh:56`: fallback default agora `qwen2.5-coder:3b`. Flag `--4b`
  preservada para quem quiser qwen3:4b explicitamente.
- README.md: header atualizado para o novo modelo padrão.
- `scripts/update_docs.py`: regex flexibilizada para casar qualquer
  modelo `qwen*` (evita auto-revert).

### Sprints destravadas

- **LANG-ENFORCE-01**: PASSA de BLOQUEADA para REAVALIAR. O guardrail
  de retry no proxy (já implementado no working tree) continua válido
  como rede de segurança, mas a métrica empírica nesta sprint mostra
  que com `qwen2.5-coder:3b` o retry quase nunca dispara (lang_rate
  100% em chat real). Recomendação: rodar LANG-ENFORCE-01 do início
  com o novo modelo para confirmar.
- **WARMUP-ON-BOOT-01**: continua útil; ganho de pré-load passa de
  ~7s (qwen3:4b) para ~3-4s (qwen2.5-coder:3b é menor) mas ainda visível.
- **SLASH-BYPASS-AUDIT-01**: independe de modelo, continua planejada.

### Sprints não-impactadas

- Sprints da FASE 2 (estabilidade) e além permanecem como estavam.

### Compatibilidade

- ADR-002 (proxy think adaptativo): ainda válido para o `--4b` legacy.
  O método `supports_thinking()` em `model_compare.py` documenta a
  heurística: apenas `qwen3*` honra `think=true`. Demais modelos
  recebem 400 do Ollama se `think=true`.

## Verificação

```bash
# Smoke
./run.sh --smoke
# Esperado: boot ok

# Modelo correto
grep NYX_MODEL .env
# Esperado: NYX_MODEL=qwen2.5-coder:3b

# Benchmark reproduzir
./venv/bin/python scripts/gauntlet/fixtures/model_compare.py --n 3
# Esperado: ranking 3b primeiro com score >= 90

# Invariantes
bash scripts/sprint_invariants.sh
# Esperado: PASS 13/13, FAIL 0
```

## Validação empírica: infra > modelo (INFRA-MODEL-AGNOSTIC-01)

Em 2026-05-19, a sprint INFRA-MODEL-AGNOSTIC-01 testou a tese complementar: **"a infra do Nyx eleva qualquer modelo, mesmo o pior"**. Hipótese declarada pelo usuário em 2026-05-18.

Resultado binário: **tese parcialmente sustentada**.

- Infra **eleva** modelos non-thinking compatíveis com tool calling (qwen2.5-coder:3b sai de bruto a score 96.8 com parser content-json + retry LANG-ENFORCE + classifier).
- Infra **não cobre** vazamento estrutural de chain-of-thought em modelos thinking-only (qwen3:4b permanece em score 34.6 mesmo com a pilha completa).
- Trocar de modelo **não quebra** o projeto (smoke=ok, invariantes 14/14 com ambos); flag `--4b` segue acessível.

Implicação: o critério de seleção continua relevante. Modelos thinking-only entram apenas se proxy ganhar suporte explícito a `<thinking>` tags (sprint hipotética PROXY-THINKING-AWARE, não prioritária).

Detalhes literais + tabelas: ver `dev-journey/07-reports/RELATORIO_INFRA_RESILIENTE_MODELO_01.md`.

## Referências

- ADR-001 (Local First) -- nenhum modelo cloud.
- ADR-002 (Proxy think=false) -- think adaptativo continua para `--4b`.
- ADR-006 (PT-BR) -- meta de idioma agora atingível.
- ADR-008 (Performance KPIs) -- P50 chat <=8s agora confortável.
- Sprint MODEL-SWAP-01 (spec).
- Sprint LANG-ENFORCE-01 (BLOQUEADA, será re-avaliada com o novo modelo).
- Sprint INFRA-MODEL-AGNOSTIC-01 -- validação empírica da tese "infra > modelo".
- `logs/model_compare.json` (evidência runtime literal).
- `dev-journey/07-reports/RELATORIO_INFRA_RESILIENTE_MODELO_01.md` (relatório consolidado).

---

*"Modelo errado é gambiarra arquitetural disfarçada de pragmatismo." -- princípio de escolha técnica*
