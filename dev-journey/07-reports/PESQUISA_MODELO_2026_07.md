# PESQUISA DE MODELO 2026-07 -- qual piso hoje para o Nyx-Code

> Pedido do dono (2026-07-13): "qual melhor modelo pra usarmos hoje? O minimo pra tudo
> funcionar conforme nossa infra, por mais pesado que seja. Se tenho 3,5 de VRAM, algo
> que use 1,5. Desde que iniciei muita coisa nova surgiu; não vejo mal um requisito minimo."

## A tensao com a alma do projeto (declarada, não contornada)

O ADR-031 e a memoria do projeto dizem "nunca trocar o modelo/placa; crash de OOM = a
cadeia falhou, não o modelo". Isso existe para impedir que a gente resolva bug de infra
trocando de modelo -- e continua valendo. **O que esta pesquisa faz e diferente:** revisar
o PISO minimo a luz do que surgiu depois que o projeto comecou (Qwen3, abril/2025), mantendo
a infra como a alavanca. O próprio dono estabeleceu na origem do projeto: "se eu colocar um
modelo bom, a infra potencializa ele tambem". A recomendacao aqui **não efetiva troca
nenhuma** -- ela produz uma hipotese a ser confirmada por bake-off no ambiente real antes de
qualquer decisao de ADR. A decisao de trocar continua sendo do dono.

## Metodo

Pesquisa web orquestrada (10 agentes: 6 angulos de busca + sintese + 3 verificacoes
adversariais das top recomendacoes). Foco calibrado pela prioridade real do produto:
**tool-calling confiavel acima de tudo** (todo o contrato de execução 397-401 depende de o
modelo emitir tool_call bem-formado), depois qualidade de codigo, depois PT-BR. Restricao
dura: caber em ~1,5-2 GB de VRAM (Q4) na RTX 3050 4GB deixando folga para KV cache + desktop
cheio, e degradar para CPU.

## Achado central

O defeito nº1 do `qwen2.5-coder:3b` atual **e exatamente tool-calling**: ele emite tool_call
via prompt-hack (não via template nativo), entao alucina `function.name`, ecoa o comando como
texto e falha com descrições de tool com mais de 2-3 linhas ou multiplas tools. A literatura
confirma isso para toda a classe de modelos prompt-based. Os "coders" fortes de 2026
(Qwen3-Coder-Next, 30B/480B) sao MoE grandes e **não cabem em 4 GB** -- para codigo pequeno
com tool-calling nativo, o caminho e o Qwen3 dense generico, não um "coder" dedicado.

## Ranking (Q4_K_M, orcamento RTX 3050 4GB)

| Modelo | Params | VRAM Q4 total | Tool-calling | Codigo | PT-BR | No Ollama | Papel sugerido |
|--------|--------|---------------|--------------|--------|-------|-----------|----------------|
| **qwen3:1.7b** | 1.7B dense | ~2,2 GB (pesos 1,4) | nativo (template) | bom | bom (nativo) | sim | **PISO recomendado** |
| qwen3:4b | 4.0B dense | ~4,0 GB (pesos 2,5) | nativo, o mais robusto <4B | excelente (nivel Qwen2.5-72B) | bom | sim | tier "qualidade" opt-in, SO com KV quantizado |
| granite3.3:2b | 2B dense (IBM) | ~2,7 GB (pesos 1,5) | nativo (formato OpenAI) | medio | desconhecido | sim | candidato de bake-off |
| hhao/qwen2.5-coder-tools:3b | 3B fine-tune | ~3,6 GB | nativo (fine-tune) | bom (HumanEval ~84) | medio | sim | drop-in conservador (mesma base do atual) |
| qwen2.5-coder:3b (ATUAL) | 3B dense | ~3,6 GB | **fraco (prompt-hack)** | bom (HumanEval 84,1) | medio | sim | baseline |
| phi4-mini:3.8b | 3.8B dense | ~3,2 GB | nativo-ok | bom | desconhecido | sim | aperta budget, atras do qwen3:4b |
| llama3.2:3b | 3B dense | ~3,6 GB | **fraco (malformado)** | medio | medio | sim | rebaixado (mesmo defeito do atual) |
| qwen3:0.6b | 0.6B dense | ~1,2 GB | fraco (colapsa multi-turn) | fraco | medio | sim | último degrau da cadeia (CPU/emergencia) |
| gemma3:4b | 4B dense (Google) | ~4,5 GB | fraco (não treinado p/ tools) | medio | bom | sim | rebaixado (fura o requisito de tool-calling) |
| Tucano 2 (base Qwen3-4B) | 3.7B dense | sem GGUF | desconhecido | bom | **o melhor PT-BR** | não | reavaliar quando houver GGUF/Ollama |

Verificação adversarial (top-3): disponibilidade no Ollama e tamanhos de download
CONFIRMADOS via página oficial. A "folga" de VRAM do qwen3:4b esta **inflada** -- ~4,0 GB
total com 8k de contexto estoura os 3,7 GB uteis com desktop cheio; so viavel com KV
quantizado (Q8_0) e contexto reduzido. Isso reforca o qwen3:1.7b como piso seguro.

## Recomendacao

**Trocar o piso para `qwen3:1.7b`.** E o único candidato que ataca o gargalo real
(tool-calling nativo via template, não prompt-hack) E cabe folgado (1,4 GB de pesos, ~2,2 GB
total), deixando espaco para KV + desktop cheio e rodando melhor no CPU fallback (menor que
o atual). Em benchmark independente de agencia marcou muito acima do atual. PT-BR e nativo
(119 idiomas), contra o foco so-codigo do 2.5-coder.

**Manter `qwen3:4b` como tier "qualidade" opt-in** -- melhor tool-calling sub-4B e codigo
nivel Qwen2.5-72B -- porem SOMENTE com KV quantizado + contexto reduzido, NUNCA como default
(estoura a VRAM com desktop cheio = violaria "OOM = a cadeia falhou").

**Cadeia de fallback para a ONDA-49 (gerenciador de models):**
`qwen3:4b` [se sobra VRAM + KV quant] -> `qwen3:1.7b` [default seguro, piso] -> `qwen3:0.6b`
[CPU/emergencia].

**Alternativa conservadora (menor risco de regressao de codigo):**
`hhao/qwen2.5-coder-tools:3b` -- mesma base do atual, tool-calling fine-tunado. Preserva a
forca de codigo (HumanEval ~84) e melhora tool-calling sem trocar de familia. O bake-off
mede se o salto do Qwen3 justifica sair da base atual.

## Ressalva honesta (isto reconcilia com a alma do projeto)

**Nenhum modelo <=4B e confiavel em tool-calling multi-turn** (qwen3:1.7b ~17%, qwen3:4b ~35%
no BFCL multi-turn). A troca **reduz mas não elimina** as malformacoes de tool_call -- a
camada de validação/sanitize/retry da infra (o contrato de execução 397-401) continua sendo
exatamente o que faz o piso parecer profissional. A pesquisa não muda a tese do projeto:
**a infra e a alavanca; um piso melhor apenas da menos trabalho para a infra corrigir.**

## Riscos (a confirmar no bake-off)

- **Template de tool-call do Qwen3 ja teve bug no Ollama/llama.cpp** (corrigido pela Unsloth).
  Se a versao do template estiver quebrada, o ganho de tool-calling evapora. FIXAR a versao.
- **qwen3:4b OOM** com desktop cheio sem KV quantizado -- nunca como default.
- **PT-BR pode derivar para PT-PT** em Qwen3/Gemma sem ancora de system prompt.
- **Modo thinking do Qwen3** interage com tool-calling; o proxy think-adaptativo ja trata
  (qwen3 precisa think=true com tools), mas validar think+tools no Gauntlet.
- **Benchmark publico != comportamento no Nyx** com PT-BR real e as tools reais. Por isso o
  bake-off e obrigatorio antes de assinar (spec `MODEL-BAKEOFF-CANDIDATES-01`).

## Próximo passo (não efetivar sem evidencia)

1. Rodar o bake-off (`dev-journey/06-sprints/producao/SPRINT_MODEL_BAKEOFF_CANDIDATES_01.md`):
   `NYX_MODEL=<candidato> ./run.sh --headless` com os probes reais, medindo formato de
   tool_call, sucesso do probe no disco, PT-BR e VRAM. Resultados anexados na §"Bake-off" abaixo.
2. Se o bake-off confirmar, abrir a ONDA-49 (gerenciador de models) e escrever o
   **ADR sucessor do ADR-031** registrando a decisao (nada de debito implicito).

## Bake-off (resultados empiricos)

Executado 2026-07-13 no ambiente REAL do Nyx (`NYX_MODEL=<id> ./run.sh --headless`, sessão
acumulada por modelo, 6 probes idênticos, `DEFAULT_MODEL` intocado). 5 modelos, 81
inferências, full-GPU (num_gpu=999) em todas -- inclusive o qwen3:4b coube na 4GB sem cair
para CPU. VRAM praticamente idêntica (~2,49 GB) para todos: **o custo de VRAM não diferencia
os candidatos nesta máquina.**

### Tabela (classificação: SIM=nativo / RESGATE=proxy extraiu do texto / ECO=sem tool · OK/FALHA)

| Modelo | P1 run_command | P2 write_file | P3 list_files | P4 search | P5 edit_file | P6 PT-BR |
|---|---|---|---|---|---|---|
| baseline `qwen2.5-coder:3b` | RESGATE OK (+memoria parasita) | RESGATE FALHA (5 writes; drift p/ repo) | ECO FALHA (listagem alucinada) | ECO FALHA (fabricou) | ECO FALHA (sem subtrai) | OK |
| `qwen3:1.7b` | RESGATE OK (limpo) | RESGATE **OK** (1 write, soma correta) | ECO FALHA (alucinou) | ECO FALHA (fabricou) | RESGATE-errado FALHA (loop; sem drift) | OK (mais rápido, ~1,8s/turno) |
| `qwen3:4b` | RESGATE OK | RESGATE OK | ECO FALHA | RESGATE **OK** (busca REAL, 16,5s) | RESGATE FALHA **DESTRUTIVA** (sobrescreveu soma) | OK |
| `hhao/qwen2.5-coder-tools:3b` | RESGATE OK | RESGATE OK | ECO FALHA | ECO FALHA | ECO **FALHA ENGANOSA** (afirmou sucesso sem tool) | OK |
| `granite3.3:2b` | RESGATE OK | RESGATE OK | ECO FALHA | ECO FALHA | RESGATE **tool-CERTA** (único a escolher edit_file; loop) FALHA | FALHA (fugiu do tema) |

**Contagem de tool_call NATIVO no Nyx: 0 de 81 inferências.** Todo tool executado veio do
resgate texto->JSON do proxy (`_extract_tool_call_from_content`, `nyx/proxy.py:517-521`).

### A premissa parecia refutada -- mas o teste direto inverteu a conclusão

O resultado acima sugeria que "qwen3 tem tool-calling nativo" seria falso na prática. **Teste
direto isolado (chamada crua ao Ollama desta máquina, fora do Nyx)** provou o contrário:

```
POST /api/chat  model=qwen3:1.7b  think=true  tools=[list_files schema]
-> message.tool_calls = [{"function": {"name": "list_files", "arguments": {"path": "/tmp"}}}]
   NATIVO: SIM   thinking: SIM
```

O `qwen3:1.7b` **emite tool_calls nativo perfeitamente** no mesmo Ollama (0.24.0), com o
mesmo template. O template não está bugado; o modelo funciona.

### Causa-raiz (o achado central desta sessão)

O nativo funciona no Ollama e **é suprimido pelo pipeline do Nyx.** O pipeline foi construído
em torno da limitação do `qwen2.5-coder:3b` (que de fato não faz nativo, ADR-031):
- `nyx/agent/prompt.py` descreve as tools em texto e dá **few-shot do formato JSON-no-content**
  ("Chame write_memory com:", "Chame run_command com:" -- linhas 117/130).
- `nyx/proxy.py:517` só lê `message.tool_calls`; se vazio, **extrai do content** (o resgate).

Com um modelo capaz de nativo (qwen3), o few-shot do prompt o empurra para o formato texto,
competindo com e vencendo o mecanismo nativo -- por isso 0/81 nativo dentro do Nyx, apesar de
o proxy passar `tools` nativas e `think=true` (confirmado pela lógica: o resgate em
`proxy.py:517` só roda com `has_tools_request=True`, e para qwen3 isso força `think=true` em
`proxy.py:284`; o confound do think está descartado).

### Veredito empírico revisado

1. **Trocar o modelo SOZINHO não entrega o ganho.** O bake-off prova: com o pipeline atual,
   nenhum modelo (nem o qwen3, nem o tool-tuned, nem o granite) usa nativo -- todos dependem do
   resgate, e o gargalo real vira o modelo **parar de chamar tools e alucinar sucesso** (P3/P4/P5
   falharam em quase todos) e o **overwrite/drift no edit** (P5 = 5/5 falha; o qwen3:4b foi
   DESTRUTIVO; o baseline vazou para o repo = bug 437).
2. **O desbloqueio real é usar o tool-calling nativo quando o modelo suporta** -- novo achado,
   sprint `MODEL-NATIVE-TOOLCALL-PIPELINE-01` (446). Sem ele, a troca de modelo é cosmética.
3. **Com o pipeline nativo, o `qwen3:1.7b` é o piso certo:** já é o mais limpo e rápido no
   resgate (um único write correto onde o baseline disparou 5 caóticos; ~1,8s/turno) e o teste
   direto prova que emite nativo -- o que elimina a maior fonte de erro (o JSON malformado que o
   resgate tenta consertar). O `qwen3:4b` compra mais disposição para buscar de verdade, mas
   custa latência e teve o overwrite destrutivo; fica como tier qualidade opt-in.
4. **A ordem correta muda:** 446 (pipeline nativo) ANTES de decidir o piso. Reavaliar o
   bake-off com o pipeline nativo ligado -- é aí que a diferença entre os modelos aparece de
   verdade. O ganho de código puro do baseline (HumanEval 84,1) não se materializou em nenhum
   probe agêntico; a agência é o que importa aqui.

### A alma do projeto, confirmada pela evidência

O bake-off reforça a tese em vez de contrariá-la: **o gargalo não é o modelo em si, é o
pipeline (infra).** Um modelo melhor sem o pipeline nativo não muda nada; o mesmo pipeline
consertado destrava vários modelos de uma vez. A alavanca continua sendo a infra -- exatamente
o ADR-032/034. A troca de piso é secundária ao conserto do pipeline.

### Custo e limpeza

Disco usado pelos pulls: **+2,71 GiB** (qwen3:1.7b +1,36; granite3.3:2b +1,44;
hhao/coder-tools:3b +14 KB por dedup; qwen3:4b já existia). Deixados em `models/` para o dono
decidir remover. `DEFAULT_MODEL` intacto (`qwen2.5-coder:3b`), zero código de produto tocado,
VRAM liberada (64/3706 MiB), zero órfão. Evidência bruta por modelo em
`/tmp/claude-1000/.../scratchpad/bakeoff_<slug>.{jsonl,_turns.json,_meta.json}` (efêmera).
