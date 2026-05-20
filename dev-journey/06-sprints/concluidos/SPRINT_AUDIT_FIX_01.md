## 0. SPEC

```yaml
sprint:
  id: AUDIT-FIX-01
  title: "Remover service órfão `compact` (dead code)"
  onda: 22
  bloco: 1
  prioridade: CRÍTICA
  tipo: Refactor
  dependencias: []
  desbloqueia: []

  touches: []
  removes:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/compact.py
      reason: "AutoCompactService não tem consumidores — loop.py chama ContextBudget direto"

  forbidden:
    - "Remover sem confirmar que loop.py já faz o equivalente"

  tests:
    - cmd: "python -c 'from nyx.agent.loop import AgentLoop; print(\"ok\")'"
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      deve_passar: true

  acceptance_criteria:
    - "Arquivo nyx/agent/services/compact.py não existe mais"
    - "grep -r 'AutoCompactService' nyx/ retorna vazio"
    - "AgentLoop continua compactando normalmente (via ContextBudget.compact_history)"
    - "Gauntlet fase rapido passa 100%"
```

---

# Sprint AUDIT-FIX-01 — Remover service órfão `compact`

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-04-18

## Contexto (snapshot)

ADR-013 (Integração Obrigatória) exige que todo service tenha consumidor. `AutoCompactService` em `nyx/agent/services/compact.py` foi port do OpenClaude mas nunca foi plugado: `nyx/agent/loop.py:195-198` e `:503-504` chamam `self._budget.should_compact()` e `self._budget.compact_history()` diretamente, bypassando o service.

## Problema

`compact.py` existe, tem testes, mas é código morto.

## Solução

Deletar `nyx/agent/services/compact.py`. A lógica de deduplicação (não compactar 2x no mesmo nível) pode ser migrada para `ContextBudget` em sprint futura (DEBT) — mas hoje não é crítica.

## Ação

```bash
rm /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/services/compact.py
# Verificar nenhum import
grep -r "from nyx.agent.services.compact" /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/ /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/
```

## Verificação

```bash
./run.sh --gauntlet --only rapido
```

## Critério binário

- [ ] `nyx/agent/services/compact.py` não existe
- [ ] `grep -r AutoCompactService nyx/` vazio
- [ ] Gauntlet rapido passa
- [ ] Commit atômico `refactor: remove service compact orfao (ADR-013)`

---

*"O menor edifício é o que não precisou ser construído." -- Lao Tsé*
