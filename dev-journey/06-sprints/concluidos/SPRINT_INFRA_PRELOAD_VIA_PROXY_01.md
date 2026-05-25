# SPRINT 235 — INFRA-PRELOAD-VIA-PROXY-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-PRELOAD-VIA-PROXY-01
  title: "Remover pré-carga direta ao Ollama (delega ao warmup via proxy)"
  onda: 31
  prioridade: ALTA
  tipo: Refactor
  dependencias: [INFRA-PRELOAD-VRAM-CONSERVATIVE-01, INFRA-OOM-ULIMIT-EXPAND-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Bloco pré-carga (linhas 568-585) curl direto ao Ollama porta 11435 bypassava INFRA-OOM-RETRY-STEP-01 do proxy"
      linhas_alvo: "568-585"
  creates: []
  removes: []

  forbidden:
    - "Tocar em warmup_model (passa pelo proxy corretamente)"
    - "Mudar lógica do SKIP_PRELOAD (BOOT-VRAM-GUARD-01 preservado)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "Bloco curl direto removido"
    - "warmup_model (linhas 629+) preservado byte-a-byte"
    - "Próximo `./run.sh` interativo: SEM mensagem `Pré-carga falhou`"
    - "OOM no warmup absorvido silenciosamente pelo proxy"
    - "Smoke + invariantes preservados"
```

---

# Sprint 235 — INFRA-PRELOAD-VIA-PROXY-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

Sprints 222 (cap 12→6) e 234 (ulimit 8→16 GB) reduziram OOMs mas pré-carga ainda falhava com erro NOVO: `CUDA error: out of memory` em `ggml_cuda_pool_vmm5alloc` mesmo com 3.7 GiB de VRAM livre.

Causa nova: **fragmentação de VRAM**. Chrome + X11 + Spellbook ocupam VRAM em chunks pequenos espalhados; o pool VMM do CUDA não consegue alocar chunk contíguo grande.

Pergunta do usuário (definitiva): **"Pq automaticamente já não faz isso?"**

Resposta: porque o bloco `run.sh:568-585` faz `curl` direto no **Ollama** (porta 11435), **bypassando o proxy** (porta 11436) que JÁ tem `INFRA-OOM-RETRY-STEP-01` (sprint 125aa). O proxy degrada automaticamente 12→6→3→0 quando recebe OOM. Mas a pré-carga não passa por lá.

E o `warmup_model` (linhas 629-634) já faz essencialmente o mesmo que a pré-carga, **MAS** via proxy. Era redundância pura, com a versão sem proteção rodando primeiro.

## Solução estrutural

Remover o bloco `run.sh:568-585` totalmente. Manter `warmup_model` que já passa por toda a infra de resiliência. Substituir por comentário explicando a decisão e citando sprint 235.

Boot flow agora:
1. `auto_tune_gpu` → calcula num_gpu inicial (cap 6 para 4GB)
2. `start_ollama` → daemon roda
3. `start_proxy` → INFRA-OOM-RETRY-STEP-01 ativo
4. `warmup_model` → primeira chamada via proxy; OOM degrada silenciosamente

Resultado: **boot sem warning visível** em qualquer condição de VRAM. Latência da 1ª mensagem do usuário absorvida pelo warmup (que tolera fallback CPU).

## Fix aplicado

```bash
# Antes (linhas 568-585): 18 linhas com curl direto + log_warn visível
# Depois: comentário documentando a delegação ao warmup via proxy
```

Diff: +13/-18 (-5 líquidas).

## Proof-of-work

```
./run.sh --smoke    → boot ok exit 0
bash scripts/sprint_invariants.sh → PASS=14/14 FAIL=0

Próximo boot interativo esperado:
- SEM mensagem `Pré-carga falhou`
- `Aquecendo modelo qwen2.5-coder:3b (warmup duplo via proxy)...`
- `Modelo aquecido (warmup duplo, Ns)` ← independente de cair em CPU ou GPU
```

## Resposta à pergunta filosófica do usuário

"Pq automaticamente já não faz isso?" — agora faz. O design do projeto sempre teve a infra de resiliência (INFRA-OOM-01/02/RETRY-STEP/HISTORY/STATS-CLI), mas o caminho de pré-carga via curl direto era um buraco arquitetural que bypassava ela. Sprint 235 fecha esse buraco.

---

*"Resiliência só é resiliência quando está no caminho da requisição. Atalho não-resiliente vira ponto único de falha." — princípio arquitetural*
