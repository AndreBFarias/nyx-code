# SPRINT GPU-FULL-OR-CPU-01 — causa raiz do OOM da GPU: ulimit -v (resolve 356)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: GPU-FULL-OR-CPU-01
  title: "GPU OOM com VRAM livre: causa raiz era o ulimit -v (não driver/GSP/ambiente). Resolve a 356"
  onda: 44
  bloco: "44 -- descoberta via comparação com a Luna (pedido do dono)"
  prioridade: ALTA
  tipo: Bugfix / Infra GPU
  dependencias: []
  desbloqueia: []
  resolve: [INFRA-GPU-VMM-OOM-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/bin/nyx-runtime-limits.sh
      reason: "CAUSA RAIZ: ulimit -v 16000000 (INFRA-OOM-01) limitava o espaço de endereço VIRTUAL. O CUDA UVA + pool VMM (cuMemAddressReserve) reservam um range virtual muito maior que 16GB -> cudaMalloc falha com OOM mesmo com VRAM livre. Removidos ulimit -v/-m; mantido oom_score_adj."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/detect_gpu.py
      reason: "Paridade Luna: full GPU quando o modelo cabe (FULL_GPU_LAYERS=999, full_mb por modelo). O cap de 4 layers (offload parcial) era baseado na premissa errada de que num_gpu alto OOMa."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Paridade Luna: KV cache f16 (era q8_0). Com full GPU, o modelo + KV f16 cabe folgado."
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Fonte única (ADR-013): --num-ctx default 8192 -> NUM_CTX (4096). O 8192 dobrava o KV cache vs o num_ctx real."

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Reintroduzir ulimit -v (quebra o CUDA)"
    - "Trocar de modelo/placa para 'resolver' (ADR-032/034 -- a infra carrega o modelo)"
    - "Adicionar emoji ou menção a IA externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS (smoke agora roda na GPU)"
    - cmd: "./run.sh --headless + 1 inferência"
      timeout: 240
      esperado: "VRAM ~2400 MiB em uso, offloaded 37/37, oom_recovery NÃO sobe, resposta correta"

  acceptance_criteria:
    - "A Nyx roda na GPU (não degrada para CPU) na RTX 3050 4GB com VRAM livre"
    - "oom_recovery_count estável (zero OOM) em execução normal"
    - "A 356 (INFRA-GPU-VMM-OOM-01) é resolvida; era config da própria infra, não ambiente"
```

---

**Status:** CONCLUIDA (2026-06-03)
**Data criação:** 2026-06-03
**Origem:** o dono pediu "vá na pasta da Luna, veja como funciona lá e traga a mesma solução pra cá". A Luna roda na GPU; o Nyx degradava para CPU (356). A comparação revelou a causa raiz.
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Problema

A 356 (INFRA-GPU-VMM-OOM-01) documentou: a GPU OOMa ao carregar o modelo MESMO com 3.7 GiB livres (`cudaMalloc` falha em `ggml_cuda_pool_vmm::alloc`). A 356 concluiu "regressão de ambiente (driver 580/CUDA 13); só reboot/reinstalar driver resolve". **O dono rebootou e o OOM persistiu.**

## Causa raiz (descoberta nesta sprint)

A causa NÃO é o ambiente — é o **`ulimit -v 16000000`** (16 GB de memória virtual) aplicado por `bin/nyx-runtime-limits.sh` (INFRA-OOM-01, expandido de 8→16 GB pela sprint 234). O CUDA UVA + pool VMM (`cuMemAddressReserve`) reservam um espaço de endereço **virtual** muito maior que 16 GB (dezenas/centenas de GB, sem consumir RAM/VRAM física). Com `ulimit -v` limitado, o `cudaMalloc` falha com "out of memory" mesmo com VRAM livre, e o Ollama degrada para CPU.

**Por que nenhuma onda anterior (nem a 356) achou:** todas testaram via `run.sh`, que aplica o ulimit. Testes diretos ao Ollama (curl) e a **Luna** (que não aplica ulimit) sempre funcionaram na GPU — mas a comparação nunca havia sido feita.

### Prova A/B (runtime real)

| Config | ulimit -v | Resultado |
|---|---|---|
| Ollama isolado (curl), full GPU + KV f16 | ausente | offloaded 37/37, GPU OK |
| Ollama isolado, MESMA config | `16000000` | **CUDA error: out of memory** |
| `run.sh` (antes) | `16000000` | OOM -> CPU (oom_recovery sobe) |
| `run.sh` (depois, ulimit removido) | ausente | **VRAM 2483 MiB, 37/37 GPU, oom_recovery estável** |

## Solução (4 mudanças, paridade Luna + fonte única)

1. **`bin/nyx-runtime-limits.sh`:** remove `ulimit -v`/`-m` (CAUSA RAIZ). Mantém `oom_score_adj` (alavanca correta para o OOM-killer, sem tocar no endereço virtual do CUDA).
2. **`scripts/detect_gpu.py`:** full GPU (`FULL_GPU_LAYERS=999`) quando o modelo cabe inteiro (`full_mb` por modelo). Offload parcial só quando não cabe.
3. **`run.sh`:** KV cache `f16` (era `q8_0`) — a config da Luna; com full GPU, cabe folgado.
4. **`nyx/proxy.py`:** `--num-ctx` default 8192 -> `NUM_CTX` (4096), fonte única (ADR-013).

## Proof-of-work (runtime real — executado)

```
bash scripts/sprint_invariants.sh    -> 14/14 PASS (smoke na GPU)
./run.sh --headless "quanto e 7 mais 5?"
  ollama.log: offloaded 37/37 layers to GPU; llama runner started in 0.86s
  nvidia-smi durante: VRAM 2475 -> 2483 MiB (GPU ATIVA)
  proxy.log: num_gpu=999 em todas as inferências; ZERO "Degradando para CPU"
  oom_recovery_count: 259 -> 259 (NÃO subiu = zero OOM)
  resposta: "O resultado de quanto e 7 mais 5 é 12." (correto, PT-BR)
```

## Notas

- Vindica a alma do projeto (ADR-032/034): não era hardware/driver "ruim" — era uma config da **própria infra** (uma proteção anti-OOM-killer que ironicamente causava o OOM da GPU). A infra carrega o modelo; o problema estava na infra, e foi corrigido na infra.
- A 356 fica **resolvida**; o diagnóstico dela (eliminação de VRAM/config/build/UVM) foi correto no que descartou, mas não chegou ao ulimit porque sempre rodou sob ele.

---

*"O limite que protegia contra um OOM causava outro. A solução estava em remover a 'proteção', não em trocar a placa." -- ADR-032 aplicado*
