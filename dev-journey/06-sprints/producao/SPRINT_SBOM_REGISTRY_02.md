# SPRINT SBOM-REGISTRY-02 — Gauntlet alimenta REGISTRY.yaml + sync regenera FEATURE_MAP

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: SBOM-REGISTRY-02
  title: "Gauntlet escreve em REGISTRY.yaml; sbom_sync.py regenera FEATURE_MAP.md a partir dele"
  onda: 23
  bloco: 23.2 SBOM
  prioridade: ALTA
  tipo: Feature+Infra
  dependencias: [SBOM-REGISTRY-01]
  desbloqueia: [SBOM-REGISTRY-03, COCKPIT-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Após cada feature testada, atualizar entry correspondente em REGISTRY.yaml (status + timestamp + evidência)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/04-features/FEATURE_MAP.md
      reason: "Substituído por output gerado de sbom_sync.py (mantém formato markdown legível)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sbom_sync.py
      reason: "Regenera FEATURE_MAP.md a partir de REGISTRY.yaml; também valida REGISTRY"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_028_SBOM.md
      reason: "Decisão arquitetural: REGISTRY.yaml é fonte única; FEATURE_MAP.md é renderização"

  removes: []

  n_to_n_pairs:
    - descricao: "Status de feature aparece em FEATURE_MAP, GAUNTLET_REPORT e REGISTRY — fonte única passa a ser REGISTRY"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/04-features/REGISTRY.yaml

  forbidden:
    - "Editar FEATURE_MAP.md manualmente (vira override que sbom_sync sobrescreve)"
    - "Bloquear gauntlet se REGISTRY.yaml não existir (graceful: warning + segue)"
    - "Path absoluto hardcoded"

  tests:
    - cmd: "./run.sh --gauntlet --only infra"
      timeout: 300
      deve_passar: true
      nota: "Após gauntlet, REGISTRY.yaml deve refletir 5 features atualizadas (timestamps recentes)"
    - cmd: "python scripts/sbom_sync.py && diff <(git show HEAD:dev-journey/04-features/FEATURE_MAP.md) dev-journey/04-features/FEATURE_MAP.md"
      timeout: 30
      deve_passar: true
      nota: "Diff mostra apenas atualizações de status/timestamp; estrutura mantida"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "Gauntlet salva resultado por feature em REGISTRY.yaml (status, ultimo_teste, evidencia, kpi)"
    - "scripts/sbom_sync.py regenera FEATURE_MAP.md a partir de REGISTRY.yaml"
    - "ADR-028 criado com Status: PROPOSTO"
    - "Gauntlet rapido + infra passam 100%"
    - "REGISTRY.yaml tem 18+ features com status 'verde' após gauntlet (as cobertas hoje)"
    - "Features novas testadas viram amarelo/vermelho conforme resultado"
    - "Acentuação PT-BR correta"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint SBOM-REGISTRY-02

## Solução resumida

1. Em `scripts/gauntlet/nyx_gauntlet.py`, após cada `_run_feature(...)`:
   ```python
   def _update_registry(feature_id: str, status: str, kpi: dict, evidencia: dict):
       registry_path = ROOT / "dev-journey/04-features/REGISTRY.yaml"
       if not registry_path.exists():
           logger.warning("REGISTRY.yaml não existe; pulando atualização")
           return
       registry = yaml.safe_load(registry_path.read_text())
       for feat in registry["features"]:
           if feat["id"] == feature_id:
               feat["status"] = status
               feat["ultimo_teste"] = datetime.utcnow().isoformat() + "Z"
               feat["kpi"] = kpi
               feat["evidencia"] = evidencia
               break
       registry_path.write_text(yaml.safe_dump(registry, allow_unicode=True))
   ```

2. `scripts/sbom_sync.py` gera FEATURE_MAP.md a partir de REGISTRY.yaml (markdown render).

3. ADR-028 documenta a decisão.

## Verificação

```bash
./run.sh --gauntlet --only infra
python -c "import yaml; r=yaml.safe_load(open('dev-journey/04-features/REGISTRY.yaml')); print([(f['id'], f['status']) for f in r['features'] if f['status'] != 'desconhecido'][:5])"
python scripts/sbom_sync.py
```

---

*"Documento gerado vence documento mantido à mão." -- anônimo*
