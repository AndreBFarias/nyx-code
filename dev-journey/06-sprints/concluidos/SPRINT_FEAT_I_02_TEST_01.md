# SPRINT FEAT-I-02-TEST-01 — Cobrir feature I-02 com teste no Gauntlet

## 0. SPEC

```yaml
sprint:
  id: FEAT-I-02-TEST-01
  title: "Cobrir feature I-02 (Kill de processos anteriores) com teste no Gauntlet"
  onda: 23
  bloco: 23.2 SBOM (auto-proposto)
  prioridade: BAIXA
  tipo: Test
  dependencias: [SBOM-REGISTRY-03]
  desbloqueia: []
  origem: "Auto-proposto por sbom_sync.py --propose-sprints; status era 'desconhecido' em REGISTRY.yaml."

  acceptance_criteria:
    - "Feature I-02 ganha entry de teste no Gauntlet"
    - "REGISTRY.yaml passa a ter status verde ou vermelho (não desconhecido) para I-02"
    - "Validação: 'Porta livre antes de iniciar'"
```

---

**Status:** CONCLUIDA (2026-05-20, terceira sessão; SBOM-PROMOTE-BATCH-3; teste correspondente PASS no gauntlet completo 220/220 do commit cdcee20)
**Data criação:** 2026-05-17
**Origem:** sbom_sync.py --propose-sprints
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
