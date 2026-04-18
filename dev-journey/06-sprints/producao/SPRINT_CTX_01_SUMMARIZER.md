## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CTX-01
  title: "SessionSummarizer -- resumo vivo injetado em compactações pesadas"
  touches:
    - path: nyx/agent/summarizer.py
      reason: "Novo módulo: SessionSummarizer que consome HistoryEntry e atualiza resumo"
    - path: nyx/agent/session.py
      reason: "Hook on_turn_complete que chama summarizer se iteration % 5 == 0"
    - path: nyx/agent/context.py
      reason: "Nível 2/3 injeta summary em vez de history cru"
    - path: nyx/agent/persistence.py
      reason: "Salvar/carregar summary junto com session"
    - path: nyx/agent/prompt.py
      reason: "Placeholder {session_summary} no system prompt"
  n_to_n_pairs:
    - "Se summary lista 'decisões' então session.key_decisions também (não duplicar)"
  forbidden:
    - "Chamar LLM a cada turno (batching obrigatório: a cada 5)"
    - "Summary > 800 tokens"
    - "Recursão infinita (summarizer chama LLM que chama summarizer)"
  tests:
    - cmd: "./run.sh --gauntlet --only contexto"
      timeout: 180
    - cmd: "manual: 20 turnos, verificar ~/.nyx/sessions/*/summary.md coerente"
      timeout: 120
  acceptance_criteria:
    - "Após 5 turnos: ~/.nyx/sessions/<id>/summary.md existe"
    - "Regenerado a cada 5 turnos adicionais (batch)"
    - "Summary contém seções: Objetivo, Decisões, Arquivos, Estado"
    - "Summary < 800 tokens sempre"
    - "Context nível 2+ injeta summary no prompt"
    - "Summary persiste entre restarts do REPL"
    - "Acentuação PT-BR no resumo"
```

---

# Sprint CTX-01 -- Resumo incremental de sessão (GSD-A)

**Status:** PENDENTE
**Data:** 2026-04-17
**Prioridade:** ALTA
**Tipo:** Feature
**Dependências:** TUI-03 (checkpoint visual)
**Desbloqueia:** CTX-02, CTX-04

---

## Problema / Contexto

`ContextBudget` em `nyx/agent/context.py` compacta histórico em 4 níveis, mas no nível 2+ só joga fora entradas -- não sintetiza. Em sessões longas (>20 turnos), informação importante (decisões, objetivo corrente, arquivos em jogo) some ou é reduzida a `entry.ultra_compact()`.

Claude Code resolve isso com contexto da sessão sempre atualizado. Aqui a proposta: um `SessionSummarizer` que a cada 5 turnos re-escreve um resumo em markdown com seções fixas, injetado no system prompt quando compactação aperta.

Ordem de prioridade do sistema de contexto (discutido no brainstorming): **A** (este) > C (memória cross-session, CTX-02) > B (plano ativo, CTX-04).

## Implementação

### Fase 1 -- SessionSummarizer módulo standalone

- `nyx/agent/summarizer.py`:
  ```python
  class SessionSummarizer:
      def __init__(self, proxy_url, model, summarize_prompt_template): ...
      async def update(self, session: CodeSession) -> str: ...
  ```
- Prompt template pede ao LLM em PT-BR: "Gere um resumo desta sessão. Seções: Objetivo, Decisões, Arquivos tocados, Estado atual. Máximo 600 palavras."
- Batching: só roda se `session.iteration - session.last_summarized_at >= 5`.

### Fase 2 -- Anti-recursão

- Flag `summarize_mode=True` no AgentLoop: quando ativo, desabilita `tools`, força 1 iteração, sem streaming.
- Summarizer usa sua própria instância de cliente HTTP (não reusa AgentLoop principal) pra evitar interferir com sessão em andamento.

### Fase 3 -- Integração com ContextBudget

- `nyx/agent/session.py:CodeSession` ganha campo `summary: str | None`.
- `nyx/agent/context.py:_compact_heavy` (nível 2): se `session.summary`, incluir como `[RESUMO]\n{summary}\n\n`.
- `_compact_emergency` (nível 3): summary vira o grosso do contexto, histórico vira só última entrada.

### Fase 4 -- Persistência

- `nyx/agent/persistence.py:save_session`: incluir `summary` no JSON salvo.
- `load_latest_session`: carrega summary se existir, senão `None` (backward compat).
- Arquivo físico: `~/.nyx/sessions/<id>/summary.md` pra o dev inspecionar fora do REPL.

### Fase 5 -- Hook no loop

- `nyx/agent/loop.py`: após cada `run()` completar, checar `should_summarize(session)`. Se sim, disparar `summarizer.update(session)` async (fire-and-forget ok se der crash logar e seguir).

### Fase 6 -- Prompt

- `nyx/agent/prompt.py`: placeholder `{session_summary}` injeta o bloco se summary não-vazio: `### Sessão em andamento\n{summary}\n---\n`.

## Verificação

```bash
rm -rf ~/.nyx/sessions/*
./run.sh
# Fazer 6 turnos (pedir leitura de arquivos, discussão de decisões)
# Ctrl+D
ls ~/.nyx/sessions/*/summary.md
cat ~/.nyx/sessions/*/summary.md
# Esperado: 4 seções coerentes, < 800 tokens
./run.sh
# enviar: /status
# Esperado: "Sessão restaurada (N entradas)" -- summary também
# enviar: "do que falamos antes?"
# Esperado: Nyx responde citando summary, não history cru
./run.sh --gauntlet --only contexto
```

- [ ] summary.md criado após 5 turnos
- [ ] Batching confirmado (só 1 chamada LLM por bloco de 5)
- [ ] Seções fixas presentes
- [ ] Sem recursão (anti-loop funciona)
- [ ] Persistência cross-restart
- [ ] Nível 2/3 do ContextBudget usa summary
- [ ] Acentuação PT-BR
- [ ] Gauntlet contexto passa

---

*"Quem não se lembra do passado está condenado a repeti-lo." -- George Santayana*
