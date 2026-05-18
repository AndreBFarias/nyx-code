# SPRINT COCKPIT-03-GAUNTLET-PER-FEATURE-01 — Gauntlet aceita feature_id (não só fase)

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: COCKPIT-03-GAUNTLET-PER-FEATURE-01
  title: "Gauntlet --only aceita feature_id (ex: I-01); cockpit roda teste individual em vez da fase inteira"
  onda: 24
  bloco: 24.3 Cockpit
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [COCKPIT-03, SBOM-REGISTRY-02]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "--only passa a aceitar feature_id (I-01, P-03, etc) executando só esse teste"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "_fase_para() pode retornar feature_id direto agora; remover mapeamento categoria->fase quando dispensável"
  creates: []
  removes: []

  forbidden:
    - "Quebrar --only fase existente (infra/proxy/etc continuam funcionando)"
    - "Romper compatibilidade com run.sh --gauntlet --only rapido"

  tests:
    - cmd: "./run.sh --gauntlet --only I-01"
      timeout: 60
      deve_passar: "executa apenas o teste de I-01, exit 0 se passar"
    - cmd: "curl -X POST http://127.0.0.1:11437/api/features/I-01/run | jq .status"
      timeout: 60
      deve_passar: "status=running então ok/fail conforme teste"

  acceptance_criteria:
    - "scripts/gauntlet/nyx_gauntlet.py aceita feature_id como --only"
    - "Cockpit dispara teste individual (não fase inteira)"
    - "Compatibilidade: --only rapido/infra/proxy continuam funcionando"
    - "Output do gauntlet para 1 feature retorna em <30s tipicamente"
```

---

# Sprint COCKPIT-03-GAUNTLET-PER-FEATURE-01

**Status:** PENDENTE
**Data criação:** 2026-05-18 (anti-débito de COCKPIT-03)
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Durante COCKPIT-03 (2026-05-18), constatei que `./run.sh --gauntlet --only X` espera nome de **fase** (infra, proxy, tools, ...) e não feature_id (I-01, P-03, ...). Workaround temporário em cockpit/server.py: mapeia feature_id → categoria → fase. Mas isso roda fase INTEIRA quando usuário clica em 1 feature — caro e dispersivo.

### Sintoma observável

```
$ ./run.sh --gauntlet --only I-01
ERROR: Fase 'I-01' desconhecida. Opções: ['infra', 'proxy', 'tools', ...]
```

## Solução proposta

`scripts/gauntlet/nyx_gauntlet.py` distingue:
1. `--only <fase>` (comportamento atual)
2. `--only <feature_id>` (novo)

Quando `--only` casa `^[A-Z]-\d+$` (regex de feature_id no REGISTRY.yaml), busca o teste correspondente em REGISTRY.yaml -> `validacao_test` e executa só ele.

Após implementação, simplificar `_fase_para()` em cockpit/server.py: passar feature_id direto se gauntlet aceita.

## Critério binário de aceite

- [ ] `./run.sh --gauntlet --only I-01` executa apenas I-01
- [ ] Cockpit `_fase_para()` simplificada (passa feature_id direto)
- [ ] Compatibilidade preservada: rapido/infra/proxy/etc continuam funcionando
- [ ] Smoke + invariantes 14/14
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `feat(COCKPIT-03-GAUNTLET-PER-FEATURE-01): --only aceita feature_id`

---

*"Granularidade é controle." — COCKPIT-03-GAUNTLET-PER-FEATURE-01*
