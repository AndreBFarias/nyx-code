# SPRINT FEAT-T-10-TEST-01 — Cobrir feature T-10 com teste no Gauntlet

## 0. SPEC

```yaml
sprint:
  id: FEAT-T-10-TEST-01
  title: "Cobrir feature T-10 (Tool calling em cadeia (Read -> Edit)) com teste no Gauntlet"
  onda: 23
  bloco: 23.2 SBOM (auto-proposto)
  prioridade: BAIXA
  tipo: Test
  dependencias: [SBOM-REGISTRY-03]
  desbloqueia: []
  origem: "Auto-proposto por sbom_sync.py --propose-sprints; status era 'desconhecido' em REGISTRY.yaml."

  acceptance_criteria:
    - "Feature T-10 ganha entry de teste no Gauntlet"
    - "REGISTRY.yaml passa a ter status verde ou vermelho (não desconhecido) para T-10"
    - "Validação: 'Segundo turno usa resultado do primeiro'"
```

---

**Status:** RASCUNHO
**Data criação:** 2026-05-17
**Origem:** sbom_sync.py --propose-sprints
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
