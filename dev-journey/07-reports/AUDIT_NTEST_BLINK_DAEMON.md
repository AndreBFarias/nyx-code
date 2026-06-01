# AUDIT — NTEST-BLINK-DAEMON (INFRA-NTEST-BLINK-DAEMON-AUDIT-01)

**Data:** 2026-05-31
**Sprint:** INFRA-NTEST-BLINK-DAEMON-AUDIT-01 (252, ONDA-31)
**Tipo:** Audit (doc-only)

## Relato de origem

O executor da sprint 246 reportou que um "daemon" ressuscitava `run.sh` durante o cleanup pós-teste — três vezes consecutivas, processos externos do tipo:

```
tmux new-session -d -s ntest ... NYX_BLINK_DEBUG=1 ./run.sh
kitty --title=ntest_blink --hold ... NYX_BLINK_DEBUG=1 ./run.sh; sleep 600
```

## Investigação (2026-05-31)

1. **`NYX_BLINK_DEBUG` no código:** `grep -rn "NYX_BLINK_DEBUG" nyx/ scripts/ run.sh` → **zero referências**. A flag era instrumentação **efêmera** (passada por env na linha de comando do executor 243), não cabeada no código. Confirma a natureza **não-invasiva**: não alterou comportamento de produção e não deixou rastro.
2. **Processos vivos:** `pgrep -af "ntest_blink|tmux.*ntest|kitty.*ntest"` → **nenhum**. Não há daemon ativo; nada ressuscita `run.sh` hoje.

## Conclusão

Não havia "daemon". A causa foi o **executor da sprint 243** (`INFRA-BANNER-BLINK-INVESTIGATE-01`) rodando **em paralelo**, capturando frames empíricos do blink do banner via `tmux`/`kitty` com `NYX_BLINK_DEBUG=1` e `sleep 600`/`--hold`. O `run.sh` "ressuscitado" eram novas sessões abertas por esse executor, não um processo auto-replicante. O cleanup do 243 não foi imediato (os processos com `sleep 600` sobreviveram à marcação CONCLUIDA), o que confundiu o executor 246.

## Lição e protocolo (recomendado)

1. **Executores em paralelo conflitam** quando ambos manipulam Ollama/Nyx em runtime; não há lock cooperativo (só o single-instance lock do `run.sh`).
2. Executor que cria sessões `tmux`/`kitty` deve:
   - registrar os sub-processos (ex.: em `/tmp/nyx_test_sessions.lock`) e
   - fazer **cleanup obrigatório no `finally`** (matar as sessões antes de marcar CONCLUIDA), confirmando com `pgrep`.
3. Sessões com `sleep N`/`--hold` longos são especialmente perigosas — preferir captura síncrona e encerrar imediato.

**Status atual:** sem pendência operacional (zero processos, zero rastro no código). Lição catalogada.
