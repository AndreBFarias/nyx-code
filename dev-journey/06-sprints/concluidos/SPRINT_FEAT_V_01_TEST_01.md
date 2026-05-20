# SPRINT FEAT-V-01-TEST-01 — Cobrir feature V-01 com teste no Gauntlet

## 0. SPEC

```yaml
sprint:
  id: FEAT-V-01-TEST-01
  title: "Cobrir feature V-01 (Banner ASCII com cores Nyx) com teste no Gauntlet"
  onda: 23
  bloco: 23.2 SBOM (auto-proposto)
  prioridade: BAIXA
  tipo: Test
  dependencias: [SBOM-REGISTRY-03]
  desbloqueia: []
  origem: "Auto-proposto por sbom_sync.py --propose-sprints; status era 'desconhecido' em REGISTRY.yaml."

  acceptance_criteria:
    - "Feature V-01 ganha entry de teste no Gauntlet"
    - "REGISTRY.yaml passa a ter status verde ou vermelho (não desconhecido) para V-01"
    - "Validação: 'Cores #00D4AA no terminal'"
```

---

**Status:** CONCLUIDA (2026-05-20, terceira sessão; SBOM-PROMOTE-BATCH-3; teste correspondente PASS no gauntlet completo 220/220 do commit cdcee20)
**Data criação:** 2026-05-17
**Origem:** sbom_sync.py --propose-sprints
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
