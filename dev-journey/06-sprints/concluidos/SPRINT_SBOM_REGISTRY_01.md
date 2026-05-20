# SPRINT SBOM-REGISTRY-01 — FEATURE_MAP.md → REGISTRY.yaml (machine-readable)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: SBOM-REGISTRY-01
  title: "Cria REGISTRY.yaml machine-readable a partir do FEATURE_MAP.md (62 entries)"
  onda: 23
  bloco: 23.2 SBOM
  prioridade: ALTA
  tipo: Infra+Docs
  dependencias: []
  desbloqueia: [SBOM-REGISTRY-02, COCKPIT-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/04-features/FEATURE_MAP.md
      reason: "Marcar como gerado-de-REGISTRY no header"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/04-features/REGISTRY.yaml
      reason: "Fonte única de verdade machine-readable das 62 features"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sbom_init.py
      reason: "Conversão one-shot FEATURE_MAP.md → REGISTRY.yaml + ADR-028 referenciado"

  removes: []

  n_to_n_pairs:
    - descricao: "Lista de features existe em FEATURE_MAP.md e GAUNTLET_REPORT.md — REGISTRY.yaml passa a ser fonte única; FEATURE_MAP regenerado por sbom_sync (próxima sprint)"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/04-features/FEATURE_MAP.md
        - /home/andrefarias/Desenvolvimento/Nyx-Code/GAUNTLET_REPORT.md

  forbidden:
    - "Apagar FEATURE_MAP.md (regenerado por sbom_sync)"
    - "Inferir status sem evidência (deve permanecer 'desconhecido' se sem teste)"
    - "Path absoluto hardcoded; usar PROJECT_ROOT"
    - "Emoji, menção a IA"

  tests:
    - cmd: "python scripts/sbom_init.py --check"
      timeout: 30
      deve_passar: true
      nota: "Detecta divergências entre FEATURE_MAP.md e REGISTRY.yaml"
    - cmd: "python -c 'import yaml; r=yaml.safe_load(open(\"dev-journey/04-features/REGISTRY.yaml\")); print(len(r[\"features\"]))'"
      timeout: 10
      deve_passar: true
      nota: "Deve imprimir 62"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "REGISTRY.yaml criado com 62 entries (1 por feature do FEATURE_MAP.md)"
    - "Cada entry tem: id, categoria, descricao, tipo, status, ultimo_teste, evidencia, kpi, sprint_origem, tags"
    - "Features sem cobertura Gauntlet ficam com status: 'desconhecido' (não 'falha')"
    - "scripts/sbom_init.py é executável e idempotente"
    - "Header de FEATURE_MAP.md menciona 'gerado a partir de REGISTRY.yaml por sbom_sync.py'"
    - "Acentuação PT-BR correta"
    - "Gauntlet passa (não toca em fase nenhuma diretamente; rege futuro)"
```

---

**Status:** CONCLUIDA (2026-05-17, commit 4769f80; correção do header via MASTER-CLEANUP-02 em 2026-05-20)
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint SBOM-REGISTRY-01

## Solução

### Schema REGISTRY.yaml

```yaml
version: 1
generated_from: "FEATURE_MAP.md@<commit>"
generated_at: "<ISO timestamp>"
features:
  - id: I-01
    categoria: infraestrutura
    descricao: "Boot completo (Ollama + Proxy + TUI)"
    tipo: feature
    status: verde  # verde | amarelo | vermelho | desconhecido
    ultimo_teste: "2026-04-21T19:24:26"
    evidencia:
      gauntlet_report: "dev-journey/07-reports/gauntlet/<id>.json"
      screenshot: null  # path quando COCKPIT-04 estiver online
    kpi:
      boot_time_s: 22.0
    sprint_origem: "INFRA-INIT"
    tags: [boot, lifecycle, critical]
  - id: I-02
    categoria: infraestrutura
    descricao: "Kill de processos anteriores"
    tipo: feature
    status: desconhecido  # Não testado pelo Gauntlet
    ultimo_teste: null
    evidencia: null
    kpi: null
    sprint_origem: "INFRA-INIT"
    tags: [boot, cleanup]
  # ...62 entries no total
```

### Script sbom_init.py

```python
"""Converte FEATURE_MAP.md (tabela markdown) em REGISTRY.yaml machine-readable.

Execute uma vez para criar; sbom_sync.py (próxima sprint) mantém atualizado.
"""
import re, sys, yaml, json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
FEATURE_MAP = ROOT / "dev-journey/04-features/FEATURE_MAP.md"
REGISTRY = ROOT / "dev-journey/04-features/REGISTRY.yaml"

# Parse das tabelas markdown -> dict
# Categorias 1-8 do FEATURE_MAP.md
# Status default: 'desconhecido' se feature não está no GAUNTLET_REPORT.md
```

## Verificação

```bash
python scripts/sbom_init.py
test -f dev-journey/04-features/REGISTRY.yaml
python -c "import yaml; r=yaml.safe_load(open('dev-journey/04-features/REGISTRY.yaml')); print(len(r['features']))"
# Deve imprimir 62
```

---

*"O mapa não é o território; mas sem mapa, perdemos." -- anônimo*
