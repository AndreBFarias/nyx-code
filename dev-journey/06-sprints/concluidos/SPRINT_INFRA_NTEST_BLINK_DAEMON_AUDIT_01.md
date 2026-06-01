# SPRINT 252 — INFRA-NTEST-BLINK-DAEMON-AUDIT-01

## 0. SPEC

```yaml
sprint:
  id: INFRA-NTEST-BLINK-DAEMON-AUDIT-01
  title: "Audit do daemon que ressuscita run.sh com NYX_BLINK_DEBUG=1"
  onda: 31
  prioridade: BAIXA
  tipo: Audit
  dependencias: []
  desbloqueia: []

  touches: []
  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/07-reports/AUDIT_NTEST_BLINK_DAEMON.md
      reason: "Documentar origem do daemon e protocolo de cleanup"
  removes: []
```

---

# Sprint 252 — INFRA-NTEST-BLINK-DAEMON-AUDIT-01

**Status:** CONCLUIDA
**Data criação:** 2026-05-25
**Data conclusão:** 2026-05-31

## Contexto

Executor da sprint 246 reportou:

> "Daemon `tmux ntest`/`kitty ntest_blink` ressuscita `run.sh` automaticamente — durante o cleanup pós-teste, três vezes consecutivas um processo externo (`tmux new-session -d -s ntest ... NYX_BLINK_DEBUG=1 ./run.sh` e `kitty --title=ntest_blink --hold ... NYX_BLINK_DEBUG=1 ./run.sh; sleep 600`) ressuscitou."

**Causa identificada pós-fato:** era o executor da sprint 243 (INFRA-BANNER-BLINK-INVESTIGATE-01) rodando em background paralelo, capturando frames empíricos via tmux/kitty com `NYX_BLINK_DEBUG=1`.

Apesar de identificada, há lição catalogável:

1. **Executores em paralelo podem conflitar** quando ambos manipulam Ollama/Nyx em runtime.
2. **Não há lock cooperativo** entre executores (apenas o lock single-instance do run.sh).
3. **Cleanup do executor 243 não foi imediato** — processos sobreviveram após sprint marcada CONCLUIDA.

## Investigação

1. Verificar se o executor 243 deixou processos vivos pós-conclusão.
2. Auditar `cli.py` por `NYX_BLINK_DEBUG` para confirmar que era apenas instrumentação não-invasiva.
3. Documentar protocolo: executor que cria sessões tmux/kitty deve registrar em `/tmp/nyx_test_sessions.lock` + cleanup obrigatório no `finally`.

## Aceitação

- [x] Relatório `dev-journey/07-reports/AUDIT_NTEST_BLINK_DAEMON.md` criado (investigação + lição).
- [x] Recomendação documentada (cleanup obrigatório no `finally` + lock cooperativo entre executores paralelos).
- [x] Smoke + invariantes (doc-only): boot ok, 14/14.

**CONCLUSÃO 2026-05-31:** `NYX_BLINK_DEBUG` sem rastro no código (instrumentação efêmera do executor 243); zero processos ntest vivos. Não era daemon — era o executor paralelo da sprint 243. Relatório completo no AUDIT_NTEST_BLINK_DAEMON.md.
