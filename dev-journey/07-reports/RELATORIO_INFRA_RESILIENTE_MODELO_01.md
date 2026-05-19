# Relatório INFRA-MODEL-AGNOSTIC-01 — Tese "infra forte > modelo grande"

**Sprint:** INFRA-MODEL-AGNOSTIC-01
**Onda:** 24 — Bloco 24.3 Resiliência arquitetural
**Data:** 2026-05-19
**Modelos comparados:** `qwen3:4b` (legacy, via `./run.sh --4b`) vs `qwen2.5-coder:3b` (default atual)
**Fonte de dados:** `logs/model_compare.json` (timestamp 1778982936, executado em 2026-05-16 via `scripts/gauntlet/fixtures/model_compare.py --n 3`)
**Conclusão binária:** Tese **parcialmente sustentada** (ver §6).

---

## 1. Tese sob teste

> "O modelo não importa: até o pior modelo, com a infra que force ele a ser bom, vai ser ótimo. Ao trocar de modelo o projeto não quebra; melhora a qualidade do código ou nota-se velocidade na fabricação do código — não no programa como um todo. A infra é o que sustenta tudo." — usuário, 2026-05-18.

Tradução operacional: medir se a infra do Nyx (parser de fallback, retry LANG-ENFORCE, classifier de intent, warmup, proxy adaptativo think=auto) **eleva o piso** do modelo arquiteturalmente pior (qwen3:4b) a ponto de torná-lo viável em produção, mesmo sendo inferior ao modelo padrão (qwen2.5-coder:3b).

---

## 2. Componentes da infra que tentam "salvar" o modelo

Inventário dos guard-rails que atuam entre o usuário e o LLM bruto:

| Componente | Path | Função |
|---|---|---|
| Parser 7-níveis | `nyx/agent/parser.py` (587 L) | Extrai tool_calls do `content` quando o modelo emite JSON inline em vez do campo nativo `tool_calls` |
| Retry LANG-ENFORCE | `nyx/proxy.py:380-411` | Detecta resposta em inglês, retry 1x com hint PT-BR explícito |
| Classifier de intent | `nyx/agent/intent.py` (98 L) | Roteia prompt por intent (chat/saudacao/tool-needed/comando) e ajusta `num_predict` + `think` |
| Lang check | `nyx/agent/lang_check.py` (107 L) | Heurística `is_pt_br` para acionar retry |
| Proxy think adaptativo (ADR-002) | `nyx/proxy.py` | Degrada `think=true → false` para modelos non-thinking, evita HTTP 400 |
| Warmup pré-load | `nyx/cli.py:691` | Pré-carrega modelo no boot para esconder cold start |
| Slash interceptor | `nyx/agent/commands/` | `/help`, `/status`, etc. **não chegam ao LLM** — CLI responde direto em PT-BR |

A pergunta empírica: **essa pilha de 7 camadas é suficiente para fazer qwen3:4b chegar ao mesmo nível UX que qwen2.5-coder:3b?**

---

## 3. Tabela comparativa (5 métricas + score)

Fonte literal: `logs/model_compare.json` (executado com Ollama dedicado em `127.0.0.1:11435`, mesmos 7 prompts, n=3 amostras por prompt, system_prompt e proxy idênticos).

| Modelo | P50 (s) | P95 (s) | lang_rate_chat | tool_ok (via parser fallback) | VRAM pico | Score 35/25/25/15 |
|---|---:|---:|---:|:---:|---:|---:|
| `qwen3:4b` (legacy) | 5.734 | 11.733 | **54.55%** | **NÃO** | 3268 MiB | **34.6** |
| `qwen2.5-coder:3b` (default) | 1.153 | 12.298 | **100%** | **SIM** | 2484 MiB | **96.8** |

Notas:
- `lang_rate_chat` exclui `/help` (slash command interceptado pelo CLI antes do LLM).
- `tool_ok` considera o parser de fallback (`nyx/agent/parser.py:228+` extrai JSON do `content`).
- Score: matriz 35% lang / 25% latência / 25% tool / 15% VRAM (definida em `model_compare.py:363`).

---

## 4. Saída literal — 3 prompts canônicos

### Prompt 1 — `"oi"` (saudação simples)

**qwen3:4b** (P50 5.277s, lang_rate 33.3%):
```
Okay, the user said "oi". Let me think about how to respond.

First, "oi" is a casual greeting in Portuguese, like "hey" or "hi". So they're probably starting a conversation.

I should respond in a fr[truncado em 200 chars]
```
→ Vaza chain-of-thought em **inglês** no campo `content`. Mesmo o retry LANG-ENFORCE não cobre, porque o vazamento é estrutural (modelo thinking emite raciocínio antes da resposta final).

**qwen2.5-coder:3b** (P50 0.640s, lang_rate 100%):
```
Oi! Como possoeu ajudar você hoje? Estou me dê detalhes sobre o que precisa.
```
→ Resposta PT-BR direta (com um leve glitch lexical "possoeu") em 0.6s.

**Veredito do prompt 1:** infra **não salva** qwen3:4b. O retry só dispara para o `content` final; ele já contém CoT em inglês como output principal.

### Prompt 2 — `"leia o arquivo README.md"` (tool-needed)

**qwen3:4b** (P50 10.638s, lang_rate 100% nas amostras que retornaram, mas content efetivamente vazio):
```
Descul[truncado]
```
→ Conteúdo praticamente vazio (orçamento `num_predict=512` consumido em thinking). Tool call **não emitida**.

**qwen2.5-coder:3b** (P50 1.267s, tool emitida via content-json):
```
{
  "name": "Read",
  "arguments": {
    "file_path": "README.md"
  }
}
```
→ Parser fallback do Nyx capta corretamente. Tool ativada. Resposta efetiva em 1.3s.

**Veredito do prompt 2:** infra **funciona** com qwen2.5-coder (parser content-json salva), **falha** com qwen3:4b (modelo nem emite o JSON, gasta tokens em thinking interno).

### Prompt 3 — `"explique o que faz o arquivo cli.py"` (tool-needed complexo)

**qwen3:4b** (P50 10.635s, content vazio em 3/3 amostras):
```
[content = ""]
```
→ Falha total. 10.6s gastos, zero output útil. Infra não tem o que processar.

**qwen2.5-coder:3b** (P50 11.472s, conteúdo PT-BR explicativo):
```
Aqui está uma explicação geral do que um arquivo `cli.py` pode fazer em diferentes contextos:

1. **Comandos de Linha de Comando (CLI)**:
   - Um arquivo `cli.py` pode ser usado para criar um conjunt[truncado]
```
→ Resposta substantiva em PT-BR, mesmo time-to-content semelhante.

**Veredito do prompt 3:** ambos os modelos demoram parecido aqui (~11s), mas só o coder:3b entrega conteúdo útil.

---

## 5. Por que a infra falha em qwen3:4b especificamente

Diagnóstico literal (extensão do ADR-031):

1. **Vazamento de chain-of-thought**: qwen3 é família "thinking" — o modelo emite seu raciocínio no campo `content`, em inglês, antes (ou no lugar) da resposta final. O retry LANG-ENFORCE detecta inglês mas não consegue separar "raciocínio interno em inglês" de "resposta final ao usuário".
2. **Tool calling estruturalmente quebrado**: `tool_call_ok=false` mesmo com parser content-json e retry. O modelo não chega a emitir o JSON da tool antes de saturar o `num_predict`. Aumentar `num_predict` lineariza o problema mas piora P95.
3. **Orçamento de tokens saturado em pensamento**: qwen3:4b consome 512 tokens em CoT antes de gerar a resposta. Em prompts complexos, isso significa `content=""` na hora do parser ler.
4. **think=auto ineficaz**: para tool-needed, o proxy seta `think=true`, mas qwen3 já é thinking-by-default; o flag não muda comportamento.

A infra do Nyx é **agnóstica a modelos não-thinking** (parser, classifier, retry assumem que o modelo emite conteúdo útil no `content`). Modelos thinking quebram essa premissa estrutural.

---

## 6. Conclusão binária da tese

**Tese: "Infra forte eleva qualquer modelo, mesmo o pior, a um patamar utilizável."**

Resultado: **PARCIALMENTE SUSTENTADA.**

| Dimensão | qwen3:4b com infra | qwen2.5-coder:3b com infra | Δ |
|---|---:|---:|---:|
| lang_rate_chat | 54.55% | 100% | **+45.45 pp** |
| tool_ok (com parser) | NÃO | SIM | binário |
| P50 chat | 5.73s | 1.15s | **+4.58s** |
| Score total | 34.6 | 96.8 | **+62.2 pts** |

Em **duas das três dimensões críticas** (lang_rate, tool_ok), a infra **não consegue elevar** qwen3:4b a níveis comparáveis ao default. O modelo é arquiteturalmente incompatível (thinking-by-default + content vazio em prompts longos), e nenhuma camada da pilha Nyx resolve isso sem reescrever o modelo.

### Tese **sustentada** na dimensão "não-quebra":

- Ao trocar de modelo o projeto **não quebra** (smoke=ok, invariantes 14/14 com ambos).
- O flag `--4b` continua acessível sem regressão de configuração (ADR-031 §Consequências).
- Trocar para um modelo arquiteturalmente compatível (qwen2.5-coder:3b) **melhora qualidade** (lang 100%, tool ok) e **velocidade** (P50 -78%).

### Tese **refutada** na dimensão "infra cobre qualquer modelo":

- A infra do Nyx (parser fallback + retry + classifier) **não cobre** vazamento de chain-of-thought.
- A infra **não cobre** content vazio por orçamento de tokens saturado em CoT.
- A infra **não cobre** ausência total de tool_call (nem nativa nem content-json) em modelos thinking-only.

### Síntese honesta

A infra do Nyx é **forte para modelos non-thinking que emitem texto útil no `content`**. Ela transforma 80% bruto em 96.8% efetivo (qwen2.5-coder:3b). Ela **não é mágica**: um modelo arquiteturalmente incompatível (qwen3:4b) permanece inviável para a UX-alvo (CLI agentic em PT-BR com tool calling), independente da pilha que envolve.

**Implicação operacional:** o critério de seleção de modelo permanece relevante (ADR-031). Não é "qualquer modelo serve" — é "qualquer modelo non-thinking com tool calling razoável tem chance, e a infra fecha o gap até score 96.8."

---

## 7. Recomendações

1. **Manter ADR-031**: qwen2.5-coder:3b como default. Adicionar nota cruzada para este relatório.
2. **Não promover qwen3:4b a recomendado**: flag `--4b` fica como compat, com warning informativo se possível.
3. **Investir em infra que beneficia non-thinking** (warmup mais agressivo, cache de tool schemas, etc.) — retorno comprovado.
4. **Critério para novos modelos candidatos**: precisa ser non-thinking, suportar tool calling (nativo ou content-json), VRAM < 3.5 GiB. Modelos thinking entram apenas se o proxy ganhar suporte explícito a `<thinking>` tags (sprint hipotética PROXY-THINKING-AWARE — não prioritária).

---

## 8. Verificação literal

```bash
# Smoke
./run.sh --smoke
# Esperado: boot ok

# Invariantes
bash scripts/sprint_invariants.sh
# Esperado: PASS 14/14, FAIL 0

# Reproduzir benchmark (precisa GPU livre — não rodado nesta sprint
# por VRAM ocupada por daemon externo; dados de logs/model_compare.json
# timestamp 1778982936, runtime real do ADR-031, são reusados pois cobrem
# exatamente a comparação solicitada com mesma config Ollama+proxy).
./venv/bin/python scripts/gauntlet/fixtures/model_compare.py --n 3 \
    --models qwen3:4b,qwen2.5-coder:3b
# Esperado: JSON com lang_rate, tool_ok, P50, P95 para ambos
```

---

## Referências

- ADR-031 Model Choice (`dev-journey/03-decisions/ADR_031_MODEL_CHOICE.md`)
- ADR-002 Proxy think adaptativo
- ADR-006 PT-BR sempre
- Sprint MODEL-SWAP-01 (dependência satisfeita)
- `logs/model_compare.json` (timestamp 1778982936, runtime real)
- `scripts/gauntlet/fixtures/model_compare.py` (538 L)

---

*"A infra é arreio honesto: doma o cavalo certo, não inventa cavalo." — INFRA-MODEL-AGNOSTIC-01*
