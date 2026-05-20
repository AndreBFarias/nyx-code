# SPRINT FEAT-V-06-TEST-01 — Cobrir feature V-06 com teste no Gauntlet

## 0. SPEC

```yaml
sprint:
  id: FEAT-V-06-TEST-01
  title: "Cobrir feature V-06 (Fallback Dracula para tema inexistente) com teste no Gauntlet"
  onda: 23
  bloco: 23.2 SBOM (auto-proposto)
  prioridade: BAIXA
  tipo: Test
  dependencias: [SBOM-REGISTRY-03]
  desbloqueia: []
  origem: "Auto-proposto por sbom_sync.py --propose-sprints; status era 'desconhecido' em REGISTRY.yaml."

  acceptance_criteria:
    - "Feature V-06 ganha entry de teste no Gauntlet"
    - "REGISTRY.yaml passa a ter status verde ou vermelho (não desconhecido) para V-06"
    - "Validação: 'Cores Dracula retornadas'"
```

---

**Status:** CONCLUIDA (2026-05-19, gauntlet 208/220, teste V-06 [OK])
**Data criação:** 2026-05-17
**Origem:** sbom_sync.py --propose-sprints
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
