# SPRINT SBOM-REGISTRY-03 — Features sem teste viram sprint stub automaticamente

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: SBOM-REGISTRY-03
  title: "Features 'desconhecido' viram sprint stub no SPRINT_ORDER_MASTER (anti-débito automatizado)"
  onda: 23
  bloco: 23.2 SBOM
  prioridade: MÉDIA
  tipo: Infra+Tooling
  dependencias: [SBOM-REGISTRY-02]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sbom_sync.py
      reason: "Adiciona flag --propose-sprints que escreve specs RASCUNHO para features sem teste"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Adiciona bloco 23.2.1 'Features sem teste (auto-proposto)' que lista sprints stub"

  creates: []

  removes: []

  n_to_n_pairs: []

  forbidden:
    - "Marcar sprint stub como PENDENTE automaticamente (deve ficar RASCUNHO para review humano)"
    - "Apagar features do REGISTRY (mantém histórico)"
    - "Proposta automática sem dry-run (sempre exigir confirmação humana)"

  tests:
    - cmd: "python scripts/sbom_sync.py --propose-sprints --dry-run"
      timeout: 30
      deve_passar: true
      nota: "Imprime quantos sprints stubs propõe; não escreve"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "Flag --propose-sprints em sbom_sync.py funcional"
    - "Modo --dry-run lista quantos seriam criados sem escrever"
    - "Sem --dry-run cria specs RASCUNHO em producao/ com naming SPRINT_FEAT_<id>_TEST_01.md"
    - "44 features 'desconhecido' (estado hoje) ficam visíveis como débito"
    - "Meta: chegar a <10 features 'desconhecido' até VALIDATE-FINAL-01"
    - "Acentuação PT-BR; zero emoji"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint SBOM-REGISTRY-03

## Contexto

Hoje 44 das 62 features estão sem cobertura Gauntlet. Sem mecanismo, isso é débito invisível. Esta sprint torna esse débito **visível e acionável**.

## Solução

```python
# sbom_sync.py
def propose_sprints(registry, dry_run=True):
    candidates = [f for f in registry["features"] if f["status"] == "desconhecido"]
    print(f"{len(candidates)} features sem teste — propostas:")
    for feat in candidates:
        sprint_id = f"FEAT-{feat['id']}-TEST-01"
        path = ROOT / f"dev-journey/06-sprints/producao/SPRINT_FEAT_{feat['id']}_TEST_01.md"
        print(f"  {sprint_id} -> {path.name}")
        if not dry_run and not path.exists():
            path.write_text(_render_test_stub(feat))
```

## Verificação

```bash
python scripts/sbom_sync.py --propose-sprints --dry-run
# Esperar: "44 features sem teste — propostas: ..."
```

---

*"O débito que ninguém vê cresce mais rápido." -- anônimo*
