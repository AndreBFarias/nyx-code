# SPRINT TUI-REDESIGN-25-12 — TodoBlock visual a partir de markdown `- [ ]`

## 0. SPEC

```yaml
sprint:
  id: TUI-REDESIGN-25-12
  title: "Detectar markdown '- [ ]' e renderizar como TodoBlock com checkboxes glyph"
  onda: 25
  bloco: 25.4 Chain-of-thought, ferramentas e estrutura
  prioridade: MÉDIA
  tipo: Feature
  dependencias: [TUI-REDESIGN-25-08]
  desbloqueia: []
  origem: "Auditoria audit.jsx -- problema P11 (Sem estrutura no conteúdo / to-do)"

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Novo render_todo_block(items=[(done: bool, text: str), ...]) + detector de markdown"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/streaming.py (se existir; senão output.py)
      reason: "Pós-stream parser: detecta linhas '- [ ] X' e '- [x] X' e agrupa em TodoBlock"

  forbidden:
    - "Reescrever conteúdo do modelo (TodoBlock é renderização, não mutação semântica)"
    - "Quebrar fallback texto quando terminal não suporta Unicode"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "render_todo_block implementado"
    - "Detector reconhece '- [ ] X' e '- [x] X' (com ou sem indentação)"
    - "Checkbox done: '◼' (ou similar não-emoji); checkbox pending: '◻'"
    - "Texto done com strikethrough sutil (ANSI 9 ou ink_muted)"
    - "Smoke ok + invariantes 14/14"
```

---

# Sprint TUI-REDESIGN-25-12

**Status:** CONCLUIDA
**Data criação:** 2026-05-18
**Data conclusão:** 2026-05-18
**Modelo obrigatório:** claude-opus-4-7
**Nota:** Helpers (parser + renderer) implementados e validados. Integração com streaming (call automático a partir do agente quando detectar todo-block na resposta) fica para sprint futura quando necessário; helper já é callable manualmente.

## Contexto

P11: quando o modelo responde com lista markdown `- [ ] X` (típico em planejamento), o terminal mostra como bullet `*` ou texto literal. O redesenho propõe um TodoBlock visual com checkboxes.

## Solução proposta

1. Parser pós-streaming detecta runs consecutivas de linhas que casam regex `^\s*-\s*\[([x ])\]\s*(.+)$`.
2. Agrupa em lista e chama `render_todo_block(items)`.
3. Render:
   ```
       ◼ Tarefa 1 concluída
       ◻ Tarefa 2 pendente
       ◻ Tarefa 3 pendente
   ```
4. Glifos `◼` (U+25FC) e `◻` (U+25FB) — geometric shapes, não-emoji (ADR-004 ok).

## Critério binário

- [ ] Detector implementado
- [ ] render_todo_block emite checkboxes
- [ ] Strikethrough sutil em done
- [ ] Smoke + invariantes 14/14
- [ ] Commit `feat(TUI-REDESIGN-25-12): TodoBlock visual a partir de markdown`

## Invariantes

#14.

## Anti-débito

- Interação para marcar/desmarcar (Tab + setas) fica para sprint nova.
- Persistência entre turnos fica fora.

## Verificação

```bash
./run.sh
# pedir Nyx criar lista de tarefas em markdown
# avaliar: checkboxes visíveis
bash scripts/sprint_invariants.sh
```

## Rollback

`git reset --hard HEAD~1`

---

*"Estrutura é affordance; rótulos viram ações." -- TUI-REDESIGN-25-12*
