# SPRINT CLI-REPL-REPLAY-ERROR-SENTINEL-LEAK-01 — REPL legado imprime __error__ cru

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CLI-REPL-REPLAY-ERROR-SENTINEL-LEAK-01
  title: "No REPL legado, render_replay/debug/progress retornam __error__msg||hint e o print mostra o marcador cru"
  onda: 44
  bloco: "44 -- achado colateral do exec 357 (TUI-SENTINEL-DISPATCH-UNIFY-01)"
  prioridade: BAIXA
  tipo: Bugfix / CLI
  dependencias: []
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli_handlers.py
      reason: "_handle_replay / _handle_debug_session / _handle_progress_tail fazem print(render_*(...)); quando o helper falha devolve a string __error__msg||hint e o REPL imprime o marcador cru (mesmo bug que a 357 corrigiu na TUI Textual)."
      linhas_alvo: "handlers de replay/debug/progress (grep _handle_replay)"

  creates: []
  removes: []
  n_to_n_pairs: []

  forbidden:
    - "Adicionar emoji ou menção a IA externa"
    - "Duplicar a normalização -- reusar o _handle_error existente do REPL"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 180
      esperado: "14/14 PASS"
    - cmd: "probe: handle do REPL para /replay <inexistente> não imprime string começando com __error__"
      timeout: 30
      esperado: "marcador normalizado em msg + hint legível"

  acceptance_criteria:
    - "No REPL, comandos cujo helper retorna __error__... renderizam msg/hint legível (não o marcador cru)"
    - "Espelha o tratamento que a 357 deu na TUI (_split_error_sentinel)"
    - "Invariantes 14/14"
```

---

**Status:** PENDENTE
**Data criação:** 2026-06-03
**Origem:** achado colateral reportado pelo executor da sprint 357 (ACHADO-COL-1). Não absorvido (protocolo anti-débito).
**Modelo obrigatório:** claude-opus (sem subagentes)

---

## Problema

A sprint 357 fechou o vazamento de sentinels na TUI Textual. Mas o host REPL legado (`nyx/cli_handlers.py`) tem o mesmo padrão para um subconjunto: `_handle_replay` (e possivelmente `_handle_debug_session`/`_handle_progress_tail`) fazem `print(render_replay(...))`. Quando `render_replay` falha, devolve `__error__msg||hint` — e o REPL imprime o marcador `__error__` cru, em vez de `msg\nhint`. A TUI já trata isso via `_split_error_sentinel` (357); o REPL não.

## Solução proposta

No REPL, quando o retorno de um helper começa com `__error__`, passar pelo `_handle_error` existente (que já normaliza `msg||hint`) em vez de imprimir cru. Reusar o mecanismo, não duplicar.

## Proof-of-work esperado

```bash
bash scripts/sprint_invariants.sh                       # 14/14 PASS
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/cli_handlers.py
# probe: o caminho REPL de /replay com arg inválido não emite string começando com __error__
```

## Critério binário de aceite

- [ ] REPL não imprime `__error__` cru nos handlers de replay/debug/progress
- [ ] Invariantes 14/14; spec movida para `concluidos/`

---

*"O mesmo buraco em duas paredes pede o mesmo reparo nas duas." -- anônimo*
