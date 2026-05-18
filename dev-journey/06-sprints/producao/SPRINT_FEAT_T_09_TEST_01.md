# SPRINT FEAT-T-09-TEST-01 — Cobrir feature T-09 com teste no Gauntlet

## 0. SPEC

```yaml
sprint:
  id: FEAT-T-09-TEST-01
  title: "Cobrir feature T-09 (Buscar texto em arquivos) com teste no Gauntlet"
  onda: 23
  bloco: 23.2 SBOM (auto-proposto)
  prioridade: BAIXA
  tipo: Test
  dependencias: [SBOM-REGISTRY-03]
  desbloqueia: []
  origem: "Auto-proposto por sbom_sync.py --propose-sprints; status era 'desconhecido' em REGISTRY.yaml."

  acceptance_criteria:
    - "Feature T-09 ganha entry de teste no Gauntlet"
    - "REGISTRY.yaml passa a ter status verde ou vermelho (não desconhecido) para T-09"
    - "Validação: 'Linhas com match retornadas'"
```

---

**Status:** RASCUNHO
**Data criação:** 2026-05-17
**Origem:** sbom_sync.py --propose-sprints
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
