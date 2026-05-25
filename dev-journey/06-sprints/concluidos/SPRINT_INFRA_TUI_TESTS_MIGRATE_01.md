# SPRINT 229 — INFRA-TUI-TESTS-MIGRATE-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-TUI-TESTS-MIGRATE-01
  title: "Mover ou descartar test_*.py em tui/widgets/ (ADR-014)"
  onda: 31
  prioridade: BAIXA
  tipo: Refactor
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_banner_widget.py
      reason: "ADR-014 proíbe testes fora do Gauntlet (sprint 205 violou)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_input_widget.py
      reason: "ADR-014 proíbe testes fora do Gauntlet (sprint 202 violou)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_output_widget.py
      reason: "ADR-014 proíbe testes fora do Gauntlet (sprint 198 violou)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_toolbar_widget.py
      reason: "ADR-014 proíbe testes fora do Gauntlet (sprint 206 violou)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/gauntlet/nyx_gauntlet.py
      reason: "Adicionar fase 'widgets' que exerciza os 4 widgets headless (se migrar)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Adicionar nota de correção pós-conclusão nas entradas 198/202/205/206"
  creates: []
  removes:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_banner_widget.py
      reason: "Se decidir deletar (alternativa A da Solução)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_input_widget.py
      reason: "Se decidir deletar"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_output_widget.py
      reason: "Se decidir deletar"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/tui/widgets/test_toolbar_widget.py
      reason: "Se decidir deletar"

  forbidden:
    - "Alterar implementação dos widgets (só os tests)"
    - "Adicionar emoji"
    - "Mencao a IA proprietaria em codigo/commit"   # noqa-anonimato

  tests:
    - cmd: "find nyx/agent -name 'test_*.py'"
      timeout: 5
      deve_passar: true   # esperado: vazio
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      deve_passar: true

  acceptance_criteria:
    - "Decisão arquitetural documentada no spec (migrar vs deletar)"
    - "find nyx/agent -name 'test_*.py' retorna vazio"
    - "Se migrou: nova fase do gauntlet passa 100%"
    - "MASTER entries 198/202/205/206 ganham nota de correção pós-conclusão"
    - "Smoke + invariantes 14/14 PASS"
    - "ADR-014 preservado"
```

---

# Sprint 229 — INFRA-TUI-TESTS-MIGRATE-01

**Status:** PENDENTE
**Data criação:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-013 Integração Obrigatória. ADR-014 Testes via Gauntlet (sem pytest/unittest).
>
> **Estado do sistema:**
> - 4 arquivos `test_*.py` em `nyx/agent/tui/widgets/` totalizando ~400L.
> - Criados pelas sprints 198 (TEXTUAL-OUTPUT-WIDGET-01), 202 (TEXTUAL-INPUT-WIDGET-01), 205 (TEXTUAL-BANNER-WIDGET-01), 206 (TEXTUAL-TOOLBAR-01).
> - Todos CONCLUIDAS no MASTER. Achado colateral pós-conclusão.

---

## Problema

ADR-014 declara: "exclusivamente dentro do Gauntlet (scripts/gauntlet/nyx_gauntlet.py)". 4 arquivos `test_*.py` violam essa regra:

- `nyx/agent/tui/widgets/test_banner_widget.py` (112L)
- `nyx/agent/tui/widgets/test_input_widget.py` (93L)
- `nyx/agent/tui/widgets/test_output_widget.py` (78L)
- `nyx/agent/tui/widgets/test_toolbar_widget.py` (117L)

Achado colateral C1 catalogado pela validação de 2026-05-25.

---

## Solução proposta

**Decisão arquitetural na fase 1 da sprint:**

**Alternativa A — Deletar:**
- Remover os 4 arquivos.
- Atualizar MASTER entries com nota: "test_*.py removido em 229 — ADR-014".
- Cobertura preservada empiricamente pelo gauntlet existente (testes rodam Application headless via Textual Pilot quando aplicável).

**Alternativa B — Migrar para Gauntlet:**
- Criar fase `widgets` em `scripts/gauntlet/nyx_gauntlet.py`.
- Cada teste vira função `widget_banner_test()`, `widget_input_test()` etc., chamada via `_add` na fase.
- Importações de Textual rodam headless via `App.run_test()` ou similar.
- Deletar os 4 arquivos originais.

**Recomendação (a confirmar com usuário antes de executar):** Alternativa A (deletar). Os testes são úteis durante desenvolvimento mas não como suite contínua — paradigma do projeto é teste por integração via gauntlet, não isolamento de widget.

---

## Arquivos alvo

A definir na fase 1. Estimativa:

- **Se A (deletar):** 4 deleções + 4 notas no MASTER + invariantes preservados.
- **Se B (migrar):** 4 deleções + 1 fase nova em nyx_gauntlet.py (~80L) + atualizações no MASTER.

---

## Diff esperado (resumo)

```
- 4 arquivos removidos (~400L)
~ 1 arquivo modificado (MASTER, notas)
+ 0 a ~80 linhas (Gauntlet fase, condicional B)
```

---

## Comandos de verificação

```bash
# 1. Decisão arquitetural (manual)

# 2. Aplicar (A ou B)
# Se A:
git rm nyx/agent/tui/widgets/test_*.py
# Se B:
# Edit nyx_gauntlet.py adicionando fase widgets

# 3. Verificar zero tests fora do gauntlet
find nyx/agent -name 'test_*.py'
# Esperado: vazio

# 4. Smoke
./run.sh --smoke

# 5. Invariantes + gauntlet
bash scripts/sprint_invariants.sh
# Se B:
./run.sh --gauntlet --only widgets
# Sempre:
./run.sh --gauntlet --only rapido

# 6. Acentuação (se editou MASTER e/ou gauntlet)
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths dev-journey/06-sprints/SPRINT_ORDER_MASTER.md scripts/gauntlet/nyx_gauntlet.py
```

---

## Critério binário de aceite

- [ ] Decisão A ou B documentada no spec antes da execução.
- [ ] `find nyx/agent -name 'test_*.py'` retorna vazio.
- [ ] Se B: nova fase passa 100%.
- [ ] MASTER ganha nota retroativa em 198/202/205/206.
- [ ] Smoke + invariantes + gauntlet rapido OK.
- [ ] Spec movida producao/ → concluidos/.

---

## Proof-of-work (4 passos)

```bash
bash scripts/sprint_invariants.sh > /tmp/inv_before.txt 2>&1
# Decisão + Edit
find nyx/agent -name 'test_*.py'   # vazio
bash scripts/sprint_invariants.sh > /tmp/inv_after.txt 2>&1
diff /tmp/inv_before.txt /tmp/inv_after.txt
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| Sprints 198/202/205/206 estão CONCLUIDAS — apagar testes implica nota retroativa | Adicionar bullet "Erratum 2026-05-25: testes removidos por INFRA-TUI-TESTS-MIGRATE-01 — ADR-014" |
| Cobertura empírica dos widgets perdida se A | Aceitar trade-off; widgets são triviais; integração validada por gauntlet existente |
| Fase nova de gauntlet (se B) precisa Textual.Pilot | Verificar versão `textual` instalada suporta `App.run_test` |

---

*"Regra é regra. Sprint concluída não anula ADR." — princípio anti-débito*
