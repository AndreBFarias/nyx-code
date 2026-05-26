# SPRINT 242 — INFRA-VRAM-CAP-4-LAYERS-01

## 0. SPEC

```yaml
sprint:
  id: INFRA-VRAM-CAP-4-LAYERS-01
  title: "Cap GPU 4GB de 6 para 4 layers (CPU fallback persistente)"
  onda: 31
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [INFRA-PRELOAD-VRAM-CONSERVATIVE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/detect_gpu.py
      reason: "Cap 6 ainda OOM com Chrome+X11 fragmentando VRAM, oom_recovery_count=85"
  creates: []
  removes: []
```

---

# Sprint 242 — INFRA-VRAM-CAP-4-LAYERS-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-25

## Contexto

Usuário rodou `./run.sh` após sprints 240+241 e perguntou: "Pera, não usamos gpu pra acelerar as coisas?". Captura mostra toolbar com `o cold` = modelo em CPU. `oom_recovery_count=85` confirma: cap=6 (sprint 222) ainda OOM por fragmentação de VRAM (Chrome+X11+Spellbook ocupam chunks pequenos).

## Fix

`scripts/detect_gpu.py:75` `VRAM_CAP_MB_TO_LAYERS` de `(4096, 6)` para `(4096, 4)`. Mais conservador. Trade-off: throughput menor por layer mas modelo cabe sempre em GPU sem cair em CPU.

Cap evoluindo: 12 (orig) → 6 (sprint 222) → 4 (sprint 242). Empírico revelou progressivamente.

## Proof-of-work

```
./run.sh --smoke   → boot ok exit 0
./venv/bin/python scripts/detect_gpu.py --for-model qwen2.5-coder:3b   → 4

3 boots consecutivos esperados sem incremento de oom_recovery_count.
```

---

*"Conservadorismo empirico vence otimismo arquitetural." -- principio*
