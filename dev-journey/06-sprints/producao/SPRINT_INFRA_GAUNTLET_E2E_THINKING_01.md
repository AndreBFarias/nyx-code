# SPRINT INFRA-GAUNTLET-E2E-THINKING-01 — E2E gated do thinking com qwen3:4b

## 0. SPEC

```yaml
sprint:
  id: INFRA-GAUNTLET-E2E-THINKING-01
  title: "P-09b E2E real do path proxyollamanyx_reasoning gated por flag + VRAM check"
  onda: 25
  bloco: "25.meta Anti-débito de pipeline"
  prioridade: MÉDIA
  tipo: Feature (test)
  dependencias: [TUI-REDESIGN-25-09-PARTE-3, INFRA-GAUNTLET-CLEANUP-BUNDLE-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Novo P-09b E2E (gated) que faz POST real ao proxy com model=qwen3:4b + tools e valida nyx_reasoning populado"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Flag `--with-qwen3` que propaga para gauntlet ativando P-09b"

  forbidden:
    - "Rodar qwen3:4b sem gating — risco de OOM no RTX 3050 4GB"
    - "Falhar P-09b se VRAM < 4GB livre (deve SKIP, não FAIL)"
    - "Tocar nyx/proxy.py ou _iteration.py (cobertura é só do gauntlet)"
    - "Emoji ou menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      assert: "PASS=14"
    - cmd: "./run.sh --gauntlet --only proxy"
      timeout: 60
      assert: "100% (default sem --with-qwen3: P-09b SKIPPED ou ausente)"

  acceptance_criteria:
    - "Novo P-09b em nyx_gauntlet.py com gating: roda APENAS quando env var ou flag `--with-qwen3` ativada"
    - "VRAM check via scripts/vram_check.py ou nvidia-smi: skip se < 4GB livre"
    - "Pull on-demand de qwen3:4b se ausente"
    - "Asserto: resposta do proxy tem `choices[0].message.nyx_reasoning` populado quando think=true"
    - "Default (sem flag): P-09b NÃO roda — gauntlet --only proxy continua 100%"
    - "Com --with-qwen3 e VRAM OK: P-09b roda end-to-end e PASS"
    - "Smoke + invariantes 14/14"
    - "Acentuação rc=0"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7

---

## Solução

1. Adicionar variável de ambiente / flag `NYX_GAUNTLET_WITH_QWEN3=1` em `run.sh --with-qwen3`.
2. Em `nyx_gauntlet.py`, dentro de `_phase_proxy`:
   - Se `os.environ.get("NYX_GAUNTLET_WITH_QWEN3") != "1"` → skip P-09b (não adiciona ao tally).
   - Else: verificar VRAM livre via `nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits` ou helper existente.
   - Se VRAM < 4096 MiB → registrar SKIPPED com motivo "VRAM insuficiente".
   - Else: `ollama pull qwen3:4b` (se ausente), POST chat com `model=qwen3:4b` + tools, validar resposta tem `nyx_reasoning`.

## Critério binário

- [ ] P-09b implementado com gating + VRAM check
- [ ] Default (sem flag): gauntlet --only proxy continua 100% (sem regressão)
- [ ] Com --with-qwen3 + VRAM OK: P-09b PASS (validação manual futura)
- [ ] Smoke + invariantes 14/14
- [ ] Acentuação rc=0
