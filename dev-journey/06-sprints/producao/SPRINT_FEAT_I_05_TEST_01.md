# SPRINT FEAT-I-05-TEST-01 — Cobrir feature I-05 com teste no Gauntlet

## 0. SPEC

```yaml
sprint:
  id: FEAT-I-05-TEST-01
  title: "Cobrir feature I-05 (Warmup do modelo) com teste no Gauntlet"
  onda: 23
  bloco: 23.2 SBOM (auto-proposto)
  prioridade: BAIXA
  tipo: Test
  dependencias: [SBOM-REGISTRY-03]
  desbloqueia: []
  origem: "Auto-proposto por sbom_sync.py --propose-sprints; status era 'desconhecido' em REGISTRY.yaml."

  acceptance_criteria:
    - "Feature I-05 ganha entry de teste no Gauntlet"
    - "REGISTRY.yaml passa a ter status verde ou vermelho (não desconhecido) para I-05"
    - "Validação: 'Primeira inferência antes da TUI'"
```

---

**Status:** RASCUNHO
**Data criação:** 2026-05-17
**Origem:** sbom_sync.py --propose-sprints
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
