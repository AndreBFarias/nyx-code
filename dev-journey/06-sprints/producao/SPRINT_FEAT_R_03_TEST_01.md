# SPRINT FEAT-R-03-TEST-01 — Cobrir feature R-03 com teste no Gauntlet

## 0. SPEC

```yaml
sprint:
  id: FEAT-R-03-TEST-01
  title: "Cobrir feature R-03 (Porta já ocupada) com teste no Gauntlet"
  onda: 23
  bloco: 23.2 SBOM (auto-proposto)
  prioridade: BAIXA
  tipo: Test
  dependencias: [SBOM-REGISTRY-03]
  desbloqueia: []
  origem: "Auto-proposto por sbom_sync.py --propose-sprints; status era 'desconhecido' em REGISTRY.yaml."

  acceptance_criteria:
    - "Feature R-03 ganha entry de teste no Gauntlet"
    - "REGISTRY.yaml passa a ter status verde ou vermelho (não desconhecido) para R-03"
    - "Validação: 'Kill anterior e retry'"
```

---

**Status:** RASCUNHO
**Data criação:** 2026-05-17
**Origem:** sbom_sync.py --propose-sprints
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
