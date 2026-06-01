# SPRINT 251 — META-MASTER-AUDIT-245-UNCOMMITTED-01

## 0. SPEC

```yaml
sprint:
  id: META-MASTER-AUDIT-245-UNCOMMITTED-01
  title: "Auditar reconciliação MASTER vs working tree para sprints CONCLUIDAS sem commit"
  onda: 31
  prioridade: BAIXA
  tipo: Audit
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Linha 719 marcava UX-COCKPIT-FULLSCREEN-01 (sprint 245) CONCLUIDA enquanto +66L em terminal.html estavam uncommitted"
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/AUDIT_MASTER_UNCOMMITTED_245.md
      reason: "Relatório forense + protocolo"
  removes: []
```

---

# Sprint 251 — META-MASTER-AUDIT-245-UNCOMMITTED-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-31

## Contexto

Executor da sprint 246 reportou achado colateral:

> "nyx/cockpit/static/terminal.html traz +66L de UX-COCKPIT-FULLSCREEN-01 na working tree, NÃO commitadas. sprint 245 está marcada CONCLUIDA no MASTER (linha 719) mas o diff visível inclui medições de célula (measureCell), fitTerminal(), debounced resize, CSS viewport 100vw/100vh, mais 10 linhas com comentário UX-COCKPIT-FULLSCREEN-01."

Causa provável:
1. Sprint 245 foi executada por subagente que move spec para concluidos/ + atualiza MASTER ANTES de commitar.
2. Subagente não tem permissão de commit (instrução explícita "NÃO commitar").
3. Integrador (eu) coleta resultados em ordem aleatória; pode commitar sprints em batch onde algumas trabalham em arquivos sobrepostos.

A sprint 246 (que também tocou terminal.html) detectou a discrepância: MASTER dizia "245 CONCLUIDA" mas o trabalho estava só staged.

Resolveu-se na hora (commit e1d5706 incluiu ambas), mas o **protocolo está furado**.

## Audit

Para cada sprint da ONDA-31 (222-250):
- `git log --oneline -- <touches>` mostra commit?
- MASTER linha N tem CONCLUIDA?
- Se MASTER=CONCLUIDA && git log VAZIO → discrepância documentar.

## Solução protocolar

Adicionar à pré-validação de cada executor-sprint:
- `git diff HEAD --stat <touches>` deve ser ZERO antes de marcar CONCLUIDA.
- OU: spec marcada como `STAGED_FOR_COMMIT` em vez de CONCLUIDA até integrador commitar.

## Aceitação

- [x] Relatório `dev-journey/07-reports/AUDIT_MASTER_UNCOMMITTED_245.md` criado.
- [x] Protocolo sugerido (`git diff HEAD --stat <touches>` == 0 antes de CONCLUIDA, ou `STAGED_FOR_COMMIT`) + commit-por-sprint aplicado nesta sessão.
- [x] Smoke + invariantes preservados (doc-only): boot ok, 14/14.

**CONCLUSÃO 2026-05-31:** a discrepância da 245 foi resolvida em `e1d5706`; working tree sem código pendente (só drift do gauntlet). Relatório completo no AUDIT_MASTER_UNCOMMITTED_245.md.
