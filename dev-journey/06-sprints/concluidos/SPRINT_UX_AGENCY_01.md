# SPRINT UX-AGENCY-01 — Implementa ADR-026: affordances + tutorial-sem-tutorial

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-AGENCY-01
  title: "Aplica ADR-026: /? contextual, footer dinâmico, cursor signaling, cancel sempre disponível"
  onda: 23
  bloco: 23.4 Gamedesigner
  prioridade: ALTA
  tipo: Feature+UX
  dependencias: [UX-LOOP-01]
  desbloqueia: [UX-COCKPIT-EXPERIENCE-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_026_AGENCIA.md
      reason: "Status PROPOSTO → ACEITO ao concluir"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Comando /? contextual; footer dinâmico baseado em estado"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Prompt prefix dinâmico (nyx | / ? / !)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop.py
      reason: "Suporte a /cancel durante tool call (asyncio.CancelledError handled)"

  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Glyphs de prompt prefix (|, ?, !) só em design_tokens.py"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py

  forbidden:
    - "Modal tutorial obrigatório no first-run"
    - "Tooltip invasivo"
    - "Spawn de operação sem kill-switch claro (Ctrl+C ou /cancel)"
    - "Decisão automática silenciosa (toda decisão é nomeada)"

  tests:
    - cmd: "./run.sh --gauntlet --only agency"
      timeout: 300
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "/? em estado neutro: mostra 3 ações principais (/help, /memory, Ctrl+R)"
    - "/? durante tool call: mostra /cancel, /pause, /inspect"
    - "/? após erro: mostra actionable específico"
    - "Footer mostra atalhos relevantes do estado atual"
    - "Prompt prefix muda: 'nyx |' (neutro), 'nyx ?' (aguardando answer), 'nyx !' (bypass on)"
    - "Ctrl+C cancela tool call sem corromper REPL"
    - "/cancel pausa tool em curso"
    - "Mensagens de decisão automática nomeiam o que aconteceu ('Vou usar Read porque...')"
    - "ADR-026 ACEITO ao final"
    - "Acentuação PT-BR"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint UX-AGENCY-01

## Solução

Ver ADR-026 para detalhes. Implementação se concentra em:
1. `output.render_prompt(state)` com prefix dinâmico.
2. `cli.py` handler para `/?` que lê contexto e retorna opções.
3. `loop.py` aceita CancelledError graciosamente.
4. Footer (já existe via TUI-FIX-04 bypass toggle) ganha + atalhos.

---

*"Controle não se promete; se entrega em cada tecla." -- anônimo*
