# SPRINT 264 — DOC-CONTEXT-LAYERS-CLARIFY-01

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: DOC-CONTEXT-LAYERS-CLARIFY-01
  title: "Clarificar as 3 camadas de 'contexto' (comentários cruzados)"
  onda: 31
  prioridade: BAIXA
  tipo: Docs
  dependencias: []
  desbloqueia: []
  conflito_arquivo: [INFRA-NUM-GPU-RECONCILE-01]   # ambos tocam defaults.py/proxy.py -> sequenciar

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/config/defaults.py
      reason: "Comentário em NUM_CTX cruzando com ContextBudget e num_predict"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/context.py
      reason: "Comentário em DEFAULT_MAX_TOKENS=12000 esclarecendo que é gatilho interno, não a janela do Ollama"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/proxy.py
      reason: "Comentário curto onde num_predict é resolvido (orçamento de saída != janela)"
  creates: []
  removes: []

  forbidden:
    - "Mudar QUALQUER valor numérico (NUM_CTX, DEFAULT_MAX_TOKENS, NUM_PREDICT_*)"
    - "Alterar comportamento; isto é doc-only (somente comentários)"
    - "Adicionar emoji / menção a IA externa"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true

  acceptance_criteria:
    - "Cada um dos 3 pontos tem comentário cruzando para os outros dois"
    - "Zero mudança de valor (git diff só adiciona comentários)"
    - "smoke boot ok + invariantes 14/14 + ruff limpo + acentuação rc=0"
```

---

**Status:** PENDENTE
**Data criação:** 2026-05-26
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> Achado da auditoria 2026-05-26. ADR-008 (Performance KPIs) + ADR-003 (VRAM).

## Problema

Existem três grandezas chamadas informalmente de "contexto", com valores diferentes, em camadas independentes — confunde quem lê o código pela primeira vez:

1. `nyx/config/defaults.py` `NUM_CTX = 4096` — **janela real do Ollama** (`num_ctx` enviado ao modelo).
2. `nyx/agent/context.py` `ContextBudget.DEFAULT_MAX_TOKENS = 12000` — **gatilho interno de compactação** (heurística ~4 chars/token; deliberadamente conservador para compactar histórico antes de estourar a janela real).
3. `nyx/config/defaults.py` `NUM_PREDICT_BY_INTENT` — **orçamento de saída** por intent (80 saudação -> 8192 plano), nada a ver com a janela de entrada.

Não há bug — são controles ortogonais. Mas a ausência de comentário cruzado faz parecer inconsistência.

## Solução (doc-only)

Adicionar comentários curtos cruzando as 3 camadas:

- Em `NUM_CTX`: "janela de ENTRADA do Ollama. Não confundir com ContextBudget.DEFAULT_MAX_TOKENS (gatilho de compactação interno) nem com NUM_PREDICT_* (orçamento de SAÍDA)."
- Em `DEFAULT_MAX_TOKENS`: "gatilho INTERNO de compactação (heurística ~4 ch/tok), conservador de propósito; != NUM_CTX (janela real Ollama em defaults.py)."
- Em `proxy.py` (onde `num_predict` é resolvido): "orçamento de SAÍDA por intent; independente da janela NUM_CTX e do budget de compactação."

Zero mudança de valor ou comportamento.

## Comandos de verificação

```bash
git diff --stat              # só os 3 arquivos, só adições de comentário
git diff | grep -E "^[-+]" | grep -vE "^[-+]\s*#|^[+-]{3}"   # NENHUMA linha de código mudada (só comentários)
/home/andrefarias/.local/bin/ruff check nyx/config/defaults.py nyx/agent/context.py nyx/proxy.py
./run.sh --smoke
bash scripts/sprint_invariants.sh
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/config/defaults.py nyx/agent/context.py nyx/proxy.py
```

## Critério binário de aceite

- [ ] 3 comentários cruzados adicionados
- [ ] `git diff` não muda nenhum valor numérico nem linha de lógica
- [ ] smoke + invariantes 14/14 + ruff + acentuação rc=0
- [ ] spec movida `producao/` -> `concluidos/`

## Proof-of-work

`git diff` mostrando só comentários + smoke + invariantes.

---

*"Nomear bem é metade de entender." -- paráfrase de Confúcio*
