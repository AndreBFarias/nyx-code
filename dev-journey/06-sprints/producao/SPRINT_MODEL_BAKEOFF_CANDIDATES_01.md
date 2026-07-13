## 0. SPEC (machine-readable)

```yaml
sprint:
  id: MODEL-BAKEOFF-CANDIDATES-01
  numero_master: 442
  title: "Bake-off empirico de modelos candidatos ao piso (qwen3:1.7b vs atual vs qwen3:4b) no ambiente real do Nyx"
  onda: 49
  prioridade: ALTA
  tipo: Pesquisa/Avaliacao
  dependencias: []
  desbloqueia: [MODEL-MANAGER-CORE-01, MODEL-THINK-AUTODETECT-01, MODEL-FALLBACK-CHAIN-01, ADR-036]

  touches: []
  creates:
    - path: dev-journey/07-reports/PESQUISA_MODELO_2026_07.md
      reason: "anexar a seção Bake-off com os resultados empiricos (o relatorio ja existe; a sprint preenche o placeholder BAKEOFF_RESULTADOS)"
  removes: []

  forbidden:
    - "Efetivar troca de modelo: NÃO editar DEFAULT_MODEL em nyx/config/defaults.py"
    - "Editar codigo de produto (nyx/): o bake-off usa a env NYX_MODEL, que ja existe (run.sh:134, cli_boot.py:59)"
    - "Rodar dois modelos ao mesmo tempo na GPU (OLLAMA_MAX_LOADED_MODELS=1; um por vez)"
    - "Deixar processo orfao ou VRAM presa entre candidatos"
    - "Adicionar emoji; mencionar ferramenta de IA"

  acceptance_criteria:
    - "Cada candidato roda via NYX_MODEL=<id> ./run.sh --headless, sem tocar DEFAULT_MODEL"
    - "Os 6 probes (P1-P6) rodam identicos para todos os candidatos, em sessão acumulada (processo único)"
    - "Para cada probe/modelo registra: tool_call nativo emitido (sim/não), sucesso no disco/summary, PT-BR limpo, VRAM pico, tempo/TTFR, num_gpu"
    - "Tabela comparativa final anexada ao relatorio; recomendacao empirica confirma ou refuta o qwen3:1.7b como piso"
    - "Default qwen2.5-coder:3b intacto ao fim; zero processo orfao; VRAM liberada"
```

---

# Sprint MODEL-BAKEOFF-CANDIDATES-01 — bake-off empirico do piso de modelo

**Status:** PENDENTE
**Data criação:** 2026-07-13
**Origem:** recomendação da pesquisa `dev-journey/07-reports/PESQUISA_MODELO_2026_07.md` (benchmark público não prova comportamento no Nyx com PT-BR real e as tools reais — a troca de piso exige confirmação empírica antes de qualquer ADR).

---

## Contexto do projeto (snapshot)

> **ADRs:** ADR-031 (escolha de modelo — esta sprint prepara o sucessor), ADR-032/033/034 (a infra carrega o modelo; a cadeia nunca quebra; feito para a pior máquina), ADR-007 (Gauntlet).
> **A alma:** "nunca trocar o modelo por bug de infra" continua valendo. Este bake-off revisa o PISO a pedido do dono, sem contornar a filosofia — a decisão de trocar é do dono, após a evidência.
> **Override de modelo:** `NYX_MODEL` já existe e funciona (`run.sh:134` `MODEL="${NYX_MODEL:-qwen2.5-coder:3b}"`, `cli_boot.py:59`). O `run.sh` baixa o modelo se faltar (`run.sh:464`). Portanto o bake-off NÃO edita código de produto.

---

## Candidatos

| # | Modelo | Papel | Download |
|---|--------|-------|----------|
| baseline | `qwen2.5-coder:3b` | atual (ADR-031) | ~1,9 GB (já presente) |
| A | `qwen3:1.7b` | piso recomendado | ~1,4 GB |
| B | `qwen3:4b` | tier qualidade opt-in | ~2,5 GB |
| C (opcional) | `hhao/qwen2.5-coder-tools:3b` | drop-in conservador | ~1,9 GB |
| D (opcional) | `granite3.3:2b` | alternativa nativa | ~1,5 GB |

Ordem: baseline -> A -> B; C e D só se disco e tempo permitirem. Um por vez (GPU exclusiva).

## Probes (o cenário real, dos T1-T5 da holística + PT-BR)

Sessão acumulada por modelo (processo único `./run.sh --headless`), turnos JSON no stdin:

- **P1 (run_command):** "da um fastfetch" -> emitiu `run_command` nativo? specs reais sob `Resultado:`?
- **P2 (write_file):** "crie ~/Desktop/bakeoff_<modelo>.py com uma função soma(a, b) que retorna a+b" -> path certo no disco? content com a função?
- **P3 (list_files):** "liste os arquivos em ~/Desktop" -> chamou `list_files` (não `write_file`)? lista real?
- **P4 (search):** "busque por TODO em ~/Desktop" -> `search` com pattern real, sem eco?
- **P5 (edit_file / drift):** "adicione ao final desse arquivo uma função subtrai(a, b)" -> `edit_file` no path certo, sem overwrite nem drift para dentro do repo (o bug 437)?
- **P6 (PT-BR + identidade):** "explique em uma frase o que e recursao" -> PT-BR limpo, sem vazar identidade ("sou uma IA"/"meus treinamentos"), sem derivar para PT-PT?

## Métricas por (modelo, probe)

- **tool_call nativo:** o modelo emitiu `tool_use` estruturado, ou ecoou como texto e o proxy/parser teve que resgatar? (ler `~/.nyx/logs/nyx.log` + iterations)
- **sucesso final:** o resultado que o usuário veria está correto? (disco: arquivo/path/content; summary: dado real vs alucinado)
- **PT-BR limpo:** sim/não.
- **custo:** VRAM pico (nvidia-smi durante o turno), TTFR/tempo por turno, `num_gpu` (rodou na GPU ou degradou p/ CPU).

## Protocolo de execução

```bash
# por candidato (um por vez):
export NYX_MODEL="<id>"
# pull acontece dentro do run.sh; se preferir pre-baixar:
OLLAMA_MODELS="$PWD/models" ollama pull "$NYX_MODEL"   # (o run.sh tambem faz)
# subir headless com timeout generoso e mandar os 6 probes no mesmo processo:
NYX_OLLAMA_START_TIMEOUT=120 ./run.sh --headless < probes.jsonl > out_<id>.jsonl
# medir VRAM em paralelo (nvidia-smi --loop) e ler ~/.nyx/logs/nyx.log
# LIMPEZA obrigatoria entre candidatos: matar stack pelo PID (nunca pkill -f), confirmar VRAM livre
```

## Proof-of-work esperado

- `out_<id>.jsonl` de cada candidato + a tabela comparativa (6 probes x N modelos) colada na §Bake-off do relatório.
- Evidência de disco por P2/P5 (sha256 / conteúdo dos arquivos criados).
- `grep DEFAULT_MODEL nyx/config/defaults.py` ainda `qwen2.5-coder:3b` ao fim (zero troca efetivada).
- `nvidia-smi` com VRAM liberada e `pgrep ollama` vazio ao fim.
- Recomendação empírica de 1 parágrafo: o bake-off confirma ou refuta o qwen3:1.7b como piso.

## Não-objetivos (anti-débito)

- **Não** implementar o gerenciador de models (é a ONDA-49 propriamente: `MODEL-MANAGER-CORE-01`).
- **Não** escrever o ADR sucessor do ADR-031 aqui — o ADR vem DEPOIS do resultado, com a decisão do dono.
- **Não** otimizar KV-quant do qwen3:4b nesta sprint (medir o custo cru; a otimização é sprint própria se o 4b entrar na cadeia).

---

*"Benchmark publico diz quem e melhor no papel; o bake-off diz quem serve a Nyx na maquina real."*
