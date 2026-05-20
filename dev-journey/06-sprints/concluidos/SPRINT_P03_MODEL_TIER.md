## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P-03
  title: "Model tier + auto-hardware (3B/7B, COMPACT/STANDARD/POWER)"
  touches:
    - path: nyx/agent/model_tier.py
      reason: "ModelTier dataclass + auto-detecção de hardware"
  acceptance_criteria:
    - "3 perfis: COMPACT (<4GB), STANDARD (4-8GB), POWER (8GB+)"
    - "Cada perfil define: modelo, num_gpu, num_ctx, max_iterations, prompt_strategy"
    - "Auto-detecção via nvidia-smi"
```

---

# Sprint P-03 -- Model Tier + Auto-Hardware

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Prioridade:** ALTA
**Dependências:** P-01
**Desbloqueia:** --

## Referência Luna

`src/skills/code_agent/model_tier.py` -- ModelTier com 3 perfis:

- **COMPACT:** qwen2.5-coder:3b, num_gpu=-1, num_ctx=8192, max_iterations=20
- **STANDARD:** qwen2.5-coder:7b, num_gpu=15, num_ctx=8192, max_iterations=20
- **POWER:** qwen2.5-coder:7b, num_gpu=-1, num_ctx=16384, max_iterations=30

## Adaptação Nyx

- **COMPACT (<4GB):** qwen3:4b, num_gpu=8, num_ctx=4096, max_iterations=15
- **STANDARD (4-8GB):** qwen3:4b, num_gpu=12, num_ctx=8192, max_iterations=30
- **POWER (8GB+):** qwen3:4b, num_gpu=-1, num_ctx=32768, max_iterations=50

---

*"Adapte-se ou morra." -- Charles Darwin*
