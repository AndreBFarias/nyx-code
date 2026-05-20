# SPRINT FEAT-C-03-TEST-01 — Cobrir feature C-03 com teste no Gauntlet

## 0. SPEC

```yaml
sprint:
  id: FEAT-C-03-TEST-01
  title: "Cobrir feature C-03 (.claude/settings.json respeita tema dark) com teste no Gauntlet"
  onda: 23
  bloco: 23.2 SBOM (auto-proposto)
  prioridade: BAIXA
  tipo: Test
  dependencias: [SBOM-REGISTRY-03]
  desbloqueia: []
  origem: "Auto-proposto por sbom_sync.py --propose-sprints; status era 'desconhecido' em REGISTRY.yaml."

  acceptance_criteria:
    - "Feature C-03 ganha entry de teste no Gauntlet"
    - "REGISTRY.yaml passa a ter status verde ou vermelho (não desconhecido) para C-03"
    - "Validação: 'theme=dark, language=pt-BR'"
```

---

**Status:** CONCLUIDA (2026-05-19, gauntlet 208/220, teste C-03 [OK])
**Data criação:** 2026-05-17
**Origem:** sbom_sync.py --propose-sprints
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)
