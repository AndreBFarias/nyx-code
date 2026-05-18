# SPRINT TUI-REDESIGN-25-14 — /quit com card de stats em grid + log de shutdown limpo

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-14
  title: "/quit gera card de estatísticas em grid + log de shutdown limpo (sem mistura com [nyx])"
  onda: 25
  bloco: 25.5 Comandos & encerramento
  prioridade: MÉDIA
  tipo: UX
  dependencias: [TUI-REDESIGN-25-02]
  desbloqueia: []
  origem: "Auditoria audit.jsx -- problema P13 (/quit sem fechamento real)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/commands/core.py
      reason: "cmd_quit (linha 66-73) emite stats agregados antes do sinal __quit__"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Shutdown loop renderiza grid de stats + caminho do save + 'até.' (não 'Desconectando...' misto)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/run.sh
      reason: "Log de shutdown ([nyx] Parando Ollama...) emitido APÓS o card, não no meio"

  forbidden:
    - "Mostrar caminho do save com path absoluto longo sem abreviar"
    - "Misturar card de stats com [nyx] log"

  tests:
    - cmd: "echo '/quit' | ./run.sh --headless --no-resume-prompt 2>&1 | grep -E 'iterações|arquivos|tokens|tempo'"
      timeout: 30
      deve_passar: ">= 1 match"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "/quit imprime card: iterações | arquivos lidos | arquivos modif | tempo total | tokens"
    - "Caminho do save abreviado (~/.nyx/sessions/<id>)"
    - "Mensagem final: 'até.' (curta, identidade Nyx)"
    - "Log do shutdown ([nyx] Parando Ollama...) vem APÓS o card"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-14

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P13: hoje a saída do REPL mistura caixa "[sessão] Iterações: ... Tempo: ..." com `[nyx] Desconectando...`, `[nyx] Fim.`, `[nyx] Parando Ollama (PID)...`. Falta polimento.

Redesenho:
```
   última sessão
   ──────────────
   iterações  3      arquivos lidos  2      arquivos modif  0
   tempo      1m32s  tokens         1487    sessão          abc12
   salvo em   ~/.nyx/sessions/abc12

   até.
   [nyx] parando Ollama (PID: 12345)...
   [nyx] fim.
```

## Solução proposta

1. `cmd_quit` agrega stats e retorna `__quit_with_stats__`.
2. Handler em `cli.py` renderiza card + mensagem final.
3. `run.sh` continua emitindo `[nyx] ...` para shutdown, mas APÓS o card (a sequência já está nessa ordem; só refinar).

## Critério binário

- [ ] Card grid 2x3 ou 3x2 com 5-6 métricas
- [ ] Caminho do save abreviado
- [ ] "até." como mensagem final
- [ ] Shutdown log separado
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-14): /quit com card de stats em grid`

## Invariantes

#2, #14.

## Anti-débito

- Histograma de duração por turno fica fora.
- Comparativo entre sessões fica em sprint nova.

## Verificação

```bash
./run.sh
# digitar /quit
# avaliar: card de stats + "até."
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Última impressão é a primeira lembrança." -- TUI-REDESIGN-25-14*
