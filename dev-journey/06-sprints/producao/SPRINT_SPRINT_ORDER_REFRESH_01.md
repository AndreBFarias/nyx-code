# SPRINT SPRINT_ORDER-REFRESH-01 — Auditoria + update do MASTER defasado

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: SPRINT_ORDER-REFRESH-01
  title: "Reconciliar SPRINT_ORDER_MASTER.md (defasado 150+ dias desde 2026-04-05)"
  onda: 24
  bloco: 24.4 Higiene de orquestração
  prioridade: MÉDIA
  tipo: Docs
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Atualizar versão para v5.1 + data; reconciliar status das 11 sprints CONCLUIDAS pós-2026-05-17; adicionar bloco Onda 24"
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Inventário (tools, commands, services) bate com PROJECT_SNAPSHOT.md + ToolRegistry runtime"
      paths:
        - dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
        - dev-journey/08-templates/PROJECT_SNAPSHOT.md

  forbidden:
    - "Apagar histórico de sprints concluídas"
    - "Mudar inventário sem confirmação via sync.py"

  tests:
    - cmd: "./venv/bin/python scripts/sync.py | head -3"
      timeout: 30
      deve_passar: "Inventário literal coerente"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "SPRINT_ORDER_MASTER.md versão v5.1 com data 2026-05-18"
    - "Bloco Onda 24 (visual + infra + release) adicionado"
    - "13 sprints novas listadas em tabela"
    - "11 sprints CONCLUIDAS pós-2026-05-17 marcadas (commits 5bc4354..decd858)"
    - "Inventário runtime atualizado se houver mudança"
    - "62 RASCUNHOs documentados como categoria"
```

---

# Sprint SPRINT_ORDER-REFRESH-01 — Reconciliação do MASTER

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

`SPRINT_ORDER_MASTER.md` está marcado **v5.0 (2026-04-05)** — 43 dias antes da janela atual. Onda 23 vive em comentário, Onda 22 não foi atualizada, status divergentes nas BLOQUEADAS, 62 RASCUNHOs não citados, 11 sprints CONCLUIDAS pós-2026-05-17 (do Checkpoint.md anterior) não estão no MASTER.

### Sintoma observável

`grep -c "CONCLUIDA" SPRINT_ORDER_MASTER.md` retorna número inferior ao real. `grep -c "RASCUNHO" SPRINT_ORDER_MASTER.md` retorna 0 mesmo havendo 62 stubs em `producao/`.

---

## Solução proposta

1. Bump v5.0 → v5.1, data 2026-05-18.
2. Marcar como CONCLUIDA as sprints da janela 2026-05-17 (do Checkpoint_2026_05_17.md.bkp):
   UX-LOOP-VISIBILITY-01, INFRA-SANITIZER-FIX-02, VISION-01/02/03, SESSION-RESUME-01, DEPLOY-01A/01B, DEPLOY-02, ONBOARDING-01, HELP-EXAMPLES-01, UX-EXTRA-01, UX-PARITY-01, MCP-SERVER-01, PLUGINS-01, OUTPUT-STYLES-01, HOOKS-DYNAMIC-01, LANG-PROMPT-ACENT-01, SBOM-REGISTRY-01/02/03, COCKPIT-01, UX-LOOP-01, UX-AGENCY-01, UX-PROGRESSION-01, INFRA-CLI-SPLIT-01, MCP-SERVER-02 (parciais e completas).
3. Adicionar bloco **Onda 24: Visual + Infra + Release v1.0**:
   - VISUAL-LAYOUT-01..08
   - INFRA-OOM-01, INSTALL-SUDO-01, INFRA-MODEL-AGNOSTIC-01, SPRINT_ORDER-REFRESH-01, HELP-COVERAGE-FIX-01
4. Adicionar seção "62 RASCUNHOs (SBOM stubs)" documentando categoria.
5. Atualizar inventário se mudou (rodar `./venv/bin/python scripts/sync.py`).

---

## Critério binário de aceite

- [ ] Bump versão v5.0 → v5.1, data 2026-05-18
- [ ] 11 sprints CONCLUIDAS pós-2026-05-17 marcadas
- [ ] Bloco Onda 24 adicionado com 13 sprints novas
- [ ] 62 RASCUNHOs documentados como categoria
- [ ] Inventário coerente com `sync.py`
- [ ] Smoke ok
- [ ] Invariantes 14/14
- [ ] Commit `docs(SPRINT_ORDER-REFRESH-01): reconcilia MASTER pos-Onda-23 + Onda 24 visual+infra`

---

*"O mapa que não se atualiza vira armadilha." — SPRINT_ORDER-REFRESH-01*
