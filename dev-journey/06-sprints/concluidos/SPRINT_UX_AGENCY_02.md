# SPRINT UX-AGENCY-02 — Cancel real em tool em curso + footer dinâmico + prefix mutável (anti-débito)

## 0. SPEC

```yaml
sprint:
  id: UX-AGENCY-02
  title: "Cancel asyncio em tool em curso + footer mutável por estado + prompt prefix dinâmico (nyx|/?/!)"
  onda: 23
  bloco: 23.4 Gamedesigner
  prioridade: ALTA
  tipo: Feature
  dependencias: [UX-AGENCY-01]
  origem: "Anti-débito de UX-AGENCY-01 — MVP entregue (/?, /cancel placeholder, ADR-026 ACEITO_PARCIAL) sem cancel real do asyncio + footer/prefix dinâmico."

  touches:
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/loop.py
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
    - /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py

  acceptance_criteria:
    - "/cancel pausa tool em curso via asyncio.CancelledError"
    - "Footer mostra atalhos do estado (neutro/tool-call/erro)"
    - "Prompt prefix: 'nyx |' / 'nyx ?' / 'nyx !' conforme estado"
    - "Ctrl+C cancela sem corromper REPL"
    - "ADR-026 sobe para ACEITO completo"
```

---

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data:** 2026-05-17
**Origem:** anti-débito de UX-AGENCY-01
