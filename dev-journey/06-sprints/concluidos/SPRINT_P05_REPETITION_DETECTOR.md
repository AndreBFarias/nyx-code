## 0. SPEC (machine-readable)

```yaml
sprint:
  id: P-05
  title: "Repetition detector (exact, semantic, cycle)"
  touches:
    - path: nyx/agent/repetition.py
      reason: "Detecção de loops: exact, semantic, cycle"
  acceptance_criteria:
    - "Exact: mesma ação com mesmos params -> skip"
    - "Semantic: mesma ação no mesmo path -> warning"
    - "Cycle: padrão A->B->A->B -> force_done"
```

---

# Sprint P-05 -- Repetition Detector

**Status:** PENDENTE
**Prioridade:** ALTA
**Dependências:** P-01

## Referência Luna

`src/skills/code_agent/repetition.py`:
- `is_exact_repeat()`: mesma ação + mesmos params
- `is_semantic_repeat()`: mesma ação no mesmo path (params diferentes)
- `detect_repetition()`: combina ambos + detecção de ciclo

Estratégias: CONTINUE, SKIP, FORCE_DONE.

---

*"Loucura é fazer a mesma coisa e esperar resultados diferentes." -- Rita Mae Brown*
