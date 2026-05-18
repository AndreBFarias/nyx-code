# SPRINT TUI-REDESIGN-25-08 — Header inline Nyx + meta (tempo + tokens)

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-08
  title: "Resposta Nyx ganha header inline: ◆ Nyx · 4.9s · 487 tokens + faixa lateral roxa"
  onda: 25
  bloco: 25.3 Diálogo
  prioridade: ALTA
  tipo: UX
  dependencias: [TUI-REDESIGN-25-03, TUI-REDESIGN-25-06]
  desbloqueia: [TUI-REDESIGN-25-09, TUI-REDESIGN-25-10]
  origem: "Auditoria audit.jsx -- problemas P07 (Sem indicação de duração) e P10 (Output Nyx sem ancoragem visual)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "render_assistant_start (linha 659) emite header inline + faixa lateral; render_assistant_end emite meta final (tempo, tokens)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop/_core.py
      reason: "Mede duração do turno (start_monotonic -> end_monotonic) + tokens (do response usage)"

  forbidden:
    - "Quebrar streaming (header precisa aparecer antes dos tokens streamarem)"
    - "Adicionar telemetria externa"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "Antes do streaming: 'Nyx' em accent + faixa lateral '│' purple inicia"
    - "Depois do streaming: linha 'Nyx · 4.9s · 487 tokens' em muted"
    - "Faixa lateral acompanha cada linha da resposta"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-08

**Status:** PENDENTE
**Data criação:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7

## Contexto

P07 + P10: resposta Nyx começa do nada, sem ancoragem visual, e sem feedback de custo (latência, tokens). O redesenho adiciona:

```
│
│ Nyx
│ Olá! Pode contar comigo.
│
│  Nyx · 4.9s · 487 tokens
```

(faixa lateral roxa + header + meta no rodapé)

## Solução proposta

1. `render_assistant_start` imprime `│ ` antes de cada linha durante streaming + header `Nyx` inicial.
2. `render_assistant_end` calcula meta a partir de `start_monotonic` (passado por `loop/_core.py`) e usage do response.
3. Faixa lateral usa `SIDE_RULE_NYX` token (definido em 25-02).

## Critério binário

- [ ] Faixa lateral roxa visível durante streaming
- [ ] Header `Nyx` no início
- [ ] Meta `Nyx · Ns · N tokens` no fim
- [ ] Streaming não quebra (latência <50ms extra)
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-08): header inline Nyx + meta (tempo + tokens)`

## Invariantes

#6, #14.

## Anti-débito

- Métricas agregadas (P50 / P95 ao longo da sessão) ficam em `/stats` (já existe).
- Comparativo entre modelos fora de escopo.

## Verificação

```bash
./run.sh
# digitar "oi" + Enter
# avaliar: faixa lateral + header + meta
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Custo visível, decisão informada." -- TUI-REDESIGN-25-08*
