# ADR-028 — SBOM canônico: REGISTRY.yaml é fonte única; FEATURE_MAP.md é renderização

**Status:** PROPOSTO
**Data:** 2026-05-15
**Contexto da Onda:** 23, Bloco 23.2, SBOM-REGISTRY-01/02/03

## Contexto

Até esta data, o "mapa de features" é `dev-journey/04-features/FEATURE_MAP.md`,
uma tabela markdown atualizada à mão. Sintomas:
- 62 features documentadas; apenas 18 verificadas pelo Gauntlet (29%).
- Status de feature divergente entre FEATURE_MAP.md, GAUNTLET_REPORT.md
  e a realidade do código (N-para-N).
- Não há rastreabilidade por feature (último teste, evidência, KPI).
- Features sem teste não geram débito visível.

## Decisão

Estabelecer **SBOM (Software Bill of Materials)** com 3 princípios:

### 1. Fonte única

`dev-journey/04-features/REGISTRY.yaml` é a única fonte da verdade sobre
features. Schema:

```yaml
version: 1
generated_at: <ISO>
features:
  - id: <ID>
    categoria: <infra|proxy|tool|qualidade|perf|interface|config|resiliencia>
    descricao: <text>
    tipo: <feature|kpi>
    status: <verde|amarelo|vermelho|desconhecido>
    ultimo_teste: <ISO|null>
    evidencia:
      gauntlet_report: <path|null>
      screenshot: <path|null>
    kpi: <dict>
    sprint_origem: <SPRINT-ID>
    tags: [<tag>...]
```

### 2. Gauntlet alimenta automaticamente

A cada execução do Gauntlet (`./run.sh --gauntlet`), `scripts/gauntlet/nyx_gauntlet.py`
atualiza a entrada correspondente em REGISTRY.yaml com:
- status (verde/amarelo/vermelho conforme resultado)
- timestamp do teste
- path do report JSON
- KPI medido

### 3. FEATURE_MAP.md é renderização

`scripts/sbom_sync.py` regenera `FEATURE_MAP.md` a partir de REGISTRY.yaml.
Header do FEATURE_MAP.md indica: `<!-- gerado por sbom_sync.py — NÃO editar manualmente -->`.

### 4. Débito visível

Features com `status: desconhecido` (sem teste no Gauntlet) viram sprints
stub no SPRINT_ORDER_MASTER via `sbom_sync.py --propose-sprints`.
Meta: <10 features `desconhecido` antes de VALIDATE-FINAL-01.

## Por que não tabela em banco SQLite?

- Local-first (ADR-001) — YAML é human-readable, versionável em git,
  sem dependência runtime.
- Diff legível em PRs.
- Renderização para markdown é trivial.

## Consequências

**Positivas:**
- Estado de features visível, auditável, versionado.
- Gauntlet vira fonte de verdade automática (não-mockada).
- Débito implícito (features sem teste) vira explícito.
- Cockpit (COCKPIT-03) consume REGISTRY.yaml diretamente — UI única.

**Neutras:**
- FEATURE_MAP.md não é mais editado manualmente. Quem quiser adicionar
  feature, edita REGISTRY.yaml + roda sbom_sync.py.

**Negativas:**
- Migração one-shot necessária (SBOM-REGISTRY-01).
- Gauntlet acoplado a YAML schema. Schema versionado (campo `version: 1`).

## Alternativas consideradas

**Alt A (manter FEATURE_MAP.md como fonte):** rejeitada — mantém o
problema atual; falta machine-readable.

**Alt B (JSON em vez de YAML):** rejeitada — YAML é mais legível para
diff humano; trade-off de quote/escape compensado.

**Alt C (SQLite local):** rejeitada — quebra versionamento git; adiciona
dependência runtime.

## Verificação

Sprints SBOM-REGISTRY-01/02/03 implementam.

## Referências

- ADR-001 (Local First), ADR-013 (Integração Obrigatória).
- ADR-014 (Testes via Gauntlet).
- FEATURE_MAP.md atual.

---

*"O mapa que se atualiza sozinho é o único que fica certo." -- anônimo*
