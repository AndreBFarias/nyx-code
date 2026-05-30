# SPRINT 295 — TUI-STATUS-LINE-PROCESSING-01

## 0. SPEC

```yaml
sprint:
  id: TUI-STATUS-LINE-PROCESSING-01
  title: "Decidir o destino do item de auditoria ONDA-34 'status line NyxCode: processando': o defeito-raiz (balão fantasma ◆ NyxCode vazio) já foi corrigido na SPRINT 283; resolver se o widget dedicado de status acima do input ainda se justifica ou é redundante com o toolbar"
  onda: 34
  prioridade: BAIXA
  tipo: Decisão
  dependencias: [TUI-NYXCODE-GHOST-LAZY-MOUNT-01, TUI-FOOTER-CAPITALIZATION-01]
  desbloqueia: []

  origem: "Item da matriz de auditoria ONDA-34 (plano redesign, linhas 53/79): proposta de um widget de status 'NyxCode: processando' entre #chat e input, com o objetivo de (a) eliminar o balão fantasma assistant-vazio e (b) dar feedback de processamento."

  touches: []
  creates: []
  removes: []

  forbidden:
    - "Adicionar um widget de status redundante com o indicador inflight do toolbar (GUIDE #2: nada especulativo)"
    - "Reabrir o balão fantasma já eliminado na 283 (lazy-mount)"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "Documentar que o objetivo (a) — eliminar fantasma — já foi 100% entregue pela SPRINT 283 (lazy-mount removeu o ChatMessage('assistant','') vazio)"
    - "Documentar que o objetivo (b) — feedback de processamento — já é coberto pelo toolbar (toolbar.py:184-186 mostra 'executando (Ctrl+C cancela)' quando inflight)"
    - "Decisão registrada: NÃO implementar o widget dedicado (redundante); revisitável se o usuário quiser placement mais proeminente"
```

## 1. DECISÃO (CONCLUIDA — 2026-05-30)

**Item de auditoria:** widget de status "NyxCode: processando" entre `#chat` e input,
com dois objetivos declarados no plano:

| Objetivo | Estado | Evidência |
|----------|--------|-----------|
| (a) Eliminar balão fantasma `◆ NyxCode` vazio | **JÁ ENTREGUE (SPRINT 283)** | `TUI-NYXCODE-GHOST-LAZY-MOUNT-01` removeu o `ChatMessage("assistant","")` montado no início do turno; o assistant só entra no `#chat` no 1º token truthy (lazy-mount em `_on_agent_token`). |
| (b) Feedback visual de "processando" | **JÁ COBERTO (toolbar)** | `toolbar.py:184-186`: quando `inflight=True`, o toolbar renderiza `"executando (Ctrl+C cancela)"` em `NYX_ACCENT`. O `watch_inflight` (L219) reage ao estado do turno. |

**Decisão: NÃO implementar o widget dedicado.** Um terceiro componente "NyxCode:
processando" entre `#chat` e input duplicaria o sinal de inflight que o toolbar já
fornece, contrariando GUIDE #2 (nada especulativo / sem componente para sinal já
existente). O defeito-raiz que motivou o item (fantasma) está resolvido.

**Reversibilidade:** decisão revisitável — se no uso real o placement do toolbar (rodapé)
se mostrar pouco visível, abrir sprint nova para mover/duplicar o indicador acima do input.
Sinal-alvo já existe (`toolbar.inflight`), então o custo de reverter é baixo.

**Validação:** sprint de decisão, zero código tocado. `bash scripts/sprint_invariants.sh`
14/14 (FAIL=0). Gauntlet N/A (nenhuma mudança de runtime).
