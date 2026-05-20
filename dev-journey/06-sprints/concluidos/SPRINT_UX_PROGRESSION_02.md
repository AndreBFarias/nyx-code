# SPRINT UX-PROGRESSION-02 — Refactor amplo de microcopy (anti-débito)

## 0. SPEC

```yaml
sprint:
  id: UX-PROGRESSION-02
  title: "Refactor das ~50 mensagens user-facing conforme MICROCOPY.md (anti-débito de UX-PROGRESSION-01)"
  onda: 23
  bloco: 23.4 Gamedesigner
  prioridade: BAIXA
  tipo: Refactor
  dependencias: [UX-PROGRESSION-01]
  origem: "UX-PROGRESSION-01 entregou MICROCOPY.md + audit script; refactor amplo das mensagens em output.py/cli.py/commands fica para esta sprint."

  acceptance_criteria:
    - "Varredura em nyx/agent/output.py, nyx/cli.py, nyx/agent/commands/*.py"
    - "Substituir literais conforme MICROCOPY.md (atual -> proposta)"
    - "Atualizar tabela MICROCOPY.md com casos novos descobertos"
    - "audit_help_coverage + microcopy_audit ambos OK"
    - "ADR-027 sobe para ACEITO completo"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-05-17
**Origem:** anti-débito de UX-PROGRESSION-01
