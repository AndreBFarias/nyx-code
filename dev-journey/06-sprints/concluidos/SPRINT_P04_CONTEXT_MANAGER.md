## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P-04
  title: "Context manager (budget de tokens, 4 níveis compactação)"
  touches:
    - path: nyx/agent/context.py
      reason: "ContextBudget + compactação progressiva"
  acceptance_criteria:
    - "4 níveis: full (0-40%), partial (40-60%), compact (60-85%), truncate (85%+)"
    - "Estimativa de tokens via heurística (chars/4)"
    - "Histórico compacta automaticamente quando budget sobe"
```

---

# Sprint P-04 -- Context Manager

**Status:** PENDENTE
**Prioridade:** ALTA
**Dependências:** P-01

## Referência Luna

`src/skills/code_agent/context_manager.py`:
- Nível 0 (<40%): histórico completo
- Nível 1 (40-60%): últimas 3 entradas full + resto ultra-compact
- Nível 2 (60-85%): apenas key_decisions + files_context
- Nível 3 (>85%): truncar agressivamente + warning

---

*"A memória é uma ferramenta, não um arquivo." -- Joshua Foer*
