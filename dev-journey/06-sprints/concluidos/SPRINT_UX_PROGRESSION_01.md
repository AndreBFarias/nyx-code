# SPRINT UX-PROGRESSION-01 — Implementa ADR-027: progressão visível + identidade Nyx auditada

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: UX-PROGRESSION-01
  title: "Aplica ADR-027: MICROCOPY.md audit + sessions/recall melhorados + voz Nyx coerente"
  onda: 23
  bloco: 23.4 Gamedesigner
  prioridade: MÉDIA
  tipo: Refactor+UX
  dependencias: [UX-LOOP-01]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/03-decisions/ADR_027_PROGRESSAO_IDENTIDADE.md
      reason: "Status PROPOSTO → ACEITO"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Refactor de mensagens de erro/sucesso conforme MICROCOPY.md"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/memory.py
      reason: "/recall mostra snippets com timestamp legível"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Microcopy auditada nos handlers de slash commands"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/MICROCOPY.md
      reason: "Tabela canônica de microcopy: contexto, atual, proposta, motivação"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/microcopy_audit.py
      reason: "Audit script: detecta placeholders genéricos em strings user-facing"

  removes: []

  n_to_n_pairs:
    - descricao: "Microcopy aparece em output.py, cli.py, commands/*.py, tools/*.py — fonte única em MICROCOPY.md"
      paths:
        - /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/05-guides/MICROCOPY.md

  forbidden:
    - "Adicionar emoji"
    - "Inglês em microcopy user-facing ('Loading...', 'Done!')"
    - "Placeholder genérico ('ok', 'error', 'success' isolados)"
    - "Mensagem florida ('ótimo, perfeito!')"
    - "Voz inconsistente entre módulos (validador deve garantir)"

  tests:
    - cmd: "python scripts/microcopy_audit.py --check"
      timeout: 30
      deve_passar: true
      nota: "Zero placeholder genérico encontrado"
    - cmd: "./run.sh --gauntlet --only microcopy"
      timeout: 300
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "FAIL_AFTER <= FAIL_BEFORE"

  acceptance_criteria:
    - "MICROCOPY.md criado com audit das ~50 mensagens user-facing atuais"
    - "Refactor das mensagens conforme tabela (atual → proposta)"
    - "scripts/microcopy_audit.py detecta strings na lista negra ('ok', 'loading', 'error', 'done', 'success' isolados, qualquer inglês user-facing)"
    - "/recall mostra timestamps legíveis (\"há 2 minutos\", \"ontem\")"
    - "ADR-027 ACEITO"
    - "Acentuação PT-BR; zero menção a IA"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-15
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

# Sprint UX-PROGRESSION-01

## Solução resumida

1. Audit inicial: grep todas strings user-facing em `nyx/`.
2. MICROCOPY.md tabela: 4 colunas (contexto, atual, proposta, motivação).
3. Refactor incremental por arquivo.
4. `microcopy_audit.py` blacklist regex para detecção contínua.
5. Gauntlet fase `microcopy` testa que blacklist passa.

## Verificação

```bash
python scripts/microcopy_audit.py --report
./run.sh --gauntlet --only microcopy
```

---

*"Voz é o que a Nyx é quando ninguém está vendo." -- anônimo*
