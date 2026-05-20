# SPRINT FEAT-Q-05-TEST-01 — Cobrir feature Q-05 com teste no Gauntlet

## 0. SPEC

```yaml
sprint:
  id: FEAT-Q-05-TEST-01
  title: "Cobrir feature Q-05 (Precisão de argumentos) com teste no Gauntlet"
  onda: 23
  bloco: 23.2 SBOM (auto-proposto)
  prioridade: BAIXA
  tipo: Test
  dependencias: [SBOM-REGISTRY-03]
  desbloqueia: []
  origem: "Auto-proposto por sbom_sync.py --propose-sprints; status era 'desconhecido' em REGISTRY.yaml."

  acceptance_criteria:
    - "Feature Q-05 ganha entry de teste no Gauntlet"
    - "REGISTRY.yaml passa a ter status verde ou vermelho (não desconhecido) para Q-05"
    - "Validação: 'Paths e parâmetros corretos'"
```

---

**Status:** CONCLUIDA (2026-05-19, gauntlet 208/220, teste Q-05 [OK])
**Data criação:** 2026-05-17
**Origem:** sbom_sync.py --propose-sprints
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
