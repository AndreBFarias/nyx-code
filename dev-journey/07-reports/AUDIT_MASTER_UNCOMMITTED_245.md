# AUDIT — MASTER vs working tree (META-MASTER-AUDIT-245-UNCOMMITTED-01)

**Data:** 2026-05-31
**Sprint:** META-MASTER-AUDIT-245-UNCOMMITTED-01 (251, ONDA-31)
**Tipo:** Audit (doc-only)

## Relato de origem

O executor da sprint 246 detectou: `nyx/cockpit/static/terminal.html` trazia +66L de `UX-COCKPIT-FULLSCREEN-01` (sprint 245) na working tree **não commitadas**, enquanto a 245 já estava marcada **CONCLUIDA** no MASTER (linha ~719 à época). Ou seja: o MASTER afirmava "concluída" antes do `git commit`.

## Investigação (2026-05-31)

| Verificação | Resultado |
|---|---|
| 245 (`UX-COCKPIT-FULLSCREEN-01`) commitada? | **Sim** — commit `e1d5706` ("SPRINTS 243+244+245+246 banner GPU + fullscreen + PTY handover + blink instrumentado") inclui o `terminal.html`. |
| MASTER marca 245 CONCLUIDA? | Sim (linha 739). Consistente com o commit — **discrepância resolvida**. |
| Working tree hoje tem código uncommitted? | **Não** — só o drift do gauntlet (`checkpoint.json`, `baselines/`, `PROJECT_SNAPSHOT.md`), untracked de propósito. Zero código de sprint pendente. |

A discrepância pontual da 245 foi resolvida no `e1d5706` (que commitou 243+244+245+246 juntas). Não há, hoje, sprint marcada CONCLUIDA com trabalho pendente.

## Causa-raiz do furo de protocolo

1. Sprint executada por subagente **move a spec `producao/`→`concluidos/` e atualiza o MASTER ANTES de commitar** (o subagente tem instrução "NÃO commitar").
2. O integrador commita em **batch**, em ordem possivelmente não-determinística.
3. Entre a marcação CONCLUIDA e o commit do integrador existe uma **janela** em que MASTER diz CONCLUIDA mas `git log` está vazio — exatamente o que a 246 flagrou.

## Protocolo (recomendado / aplicado)

- **Regra dura:** `git diff HEAD --stat <touches>` deve ser **ZERO** antes de marcar CONCLUIDA; ou marcar a spec como `STAGED_FOR_COMMIT` (estado intermediário) até o integrador commitar.
- **Aplicado nesta sessão (ONDA-35 + backlog):** protocolo **commit-por-sprint** — cada sprint é validada → commit atômico → push **imediato**, eliminando a janela MASTER-vs-git. Verificável: cada sprint 303-309, a 247, a mouseup e a 257 têm commit próprio antes da próxima começar.

**Status atual:** sem discrepância ativa (working tree limpo, 245 commitada). Lição catalogada; protocolo commit-por-sprint recomendado como padrão.
