# SPRINT 234 — INFRA-OOM-ULIMIT-EXPAND-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-OOM-ULIMIT-EXPAND-01
  title: "ulimit -v 8GB para 16GB (CUDA UVA mappa VRAM no virtual address space)"
  onda: 31
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [INFRA-PRELOAD-VRAM-CONSERVATIVE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/bin/nyx-runtime-limits.sh
      reason: "ulimit -v 8000000 (8GB) era restritivo: CUDA UVA mappa toda VRAM (4GB) no virtual address space + libs + buffer pools, estourando os 8GB"
      linhas_alvo: "15-19"
  creates: []
  removes: []

  forbidden:
    - "Remover ulimit totalmente (perde proteção INFRA-OOM-01)"
    - "Modificar oom_score_adj"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "ulimit -v elevado de 8000000 para 16000000 (16GB)"
    - "Comentário documenta motivação: CUDA UVA + libs cresce virtual space muito além do RSS"
    - "Próximo `./run.sh` interativo: pré-carga SUCESSO (sem `Pré-carga falhou`)"
    - "oom_recovery_count não incrementa após boot"
    - "Smoke boot ok + invariantes 14/14 PASS"
```

---

# Sprint 234 — INFRA-OOM-ULIMIT-EXPAND-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

Sprint 222 reduziu `num_gpu` cap de 12 para 6 e eliminou `cudaMalloc failed: out of memory`. Mas o usuário rodou `./run.sh` em 2026-05-25 ~20:00 e ainda viu `[nyx] Pré-carga falhou`.

Logs revelam erro DIFERENTE:

```
ggml_backend_cpu_buffer_type_alloc_buffer: failed to allocate buffer of size 276824064
alloc_tensor_range: failed to allocate CPU buffer of size 276824064
llama_init_from_model: failed to initialize the context: failed to allocate buffer for kv cache
```

**Não é OOM de VRAM** (3.7 GiB livres no momento). É falha de alocar **CPU buffer de 276 MB**.

`/proc/<ollama>/limits` mostra:
```
Max address space         8192000000           8192000000           bytes
```

= 7.63 GiB. Aplicado por `bin/nyx-runtime-limits.sh:16 ulimit -v 8000000`.

VmPeak do ollama runner: 4.66 GiB. Margem de 3 GiB parece suficiente, MAS:
- CUDA UVA mapeia toda VRAM (4 GiB) no virtual address space do processo
- libcuda.so + dependências + buffer pools internos consomem mais virt space
- KV cache de 288 MiB (num_ctx=8192 ignorando nosso num_ctx=4096) tenta alocar
- Estoura os 7.63 GiB

oom_recovery_count escalou de 23 (após sprint 222) para **69** em ~3 horas — 46 OOMs adicionais por causa do ulimit.

## Solução

Elevar `ulimit -v` de 8000000 (8 GB) para 16000000 (16 GB). RAM física da máquina = 14 GiB + swap 23 GiB, então 16 GB de virt address space é seguro. Preserva proteção contra runaway (sem ulimit, processo poderia consumir toda RAM e disparar OOM-killer kernel).

Comentário inline justifica: "CUDA UVA mappa VRAM no virt space + libs cresce muito além do RSS".

## Fix aplicado

```bash
# bin/nyx-runtime-limits.sh:15-19 antes:
ulimit -v 8000000 2>/dev/null || true
ulimit -m 8000000 2>/dev/null || true

# bin/nyx-runtime-limits.sh:15-19 depois:
# 16GB virt mem: CUDA UVA mappa VRAM (4GB) + libcuda + buffer pools
# fazem virt address space crescer muito além do RSS. 8GB original
# (sprint INFRA-OOM-01) era restritivo em sessão real, gerava 46
# OOMs em 3h após sprint 222 reduzir num_gpu cap.
ulimit -v 16000000 2>/dev/null || true
ulimit -m 16000000 2>/dev/null || true
```

## Proof-of-work

```bash
./run.sh --smoke    # boot ok exit 0
bash scripts/sprint_invariants.sh   # PASS=14/14 FAIL=0

# Próximo boot interativo esperado:
# - Sem mensagem `Pré-carga falhou`
# - `cat /proc/<ollama>/limits | grep address` → 16000000000
# - oom_recovery_count não incrementa
```

## Riscos

| Risco | Mitigação |
|---|---|
| 16 GB ainda insuficiente em alguma configuração | Pode subir para `unlimited` em sprint follow-up se reincidir |
| Sessão com Chrome + Spellbook + Nyx pode estourar 16 GB combinado | RAM física 14 GiB + swap 23 GiB; sistema absorve via swap antes de matar |
| Modifica comportamento de runtime de outros processos do shell | Apenas processos filhos do `run.sh` herdam o ulimit (não afeta o shell pai) |

---

*"Limite de proteção vira limite de execução quando o range muda. CUDA UVA mudou o range." — princípio empírico*
