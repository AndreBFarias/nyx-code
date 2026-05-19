# SPRINT MASTER-ACENTUACAO-FIX-01 — Corrigir 12 violações de acentuação pré-existentes em SPRINT_ORDER_MASTER.md

## 0. SPEC

```yaml
sprint:
  id: MASTER-ACENTUACAO-FIX-01
  title: "Corrigir 12 violações de acentuação pré-existentes em SPRINT_ORDER_MASTER.md"
  onda: 24
  bloco: 24.4 Higiene
  prioridade: BAIXA
  tipo: Fix
  dependencias: []
  desbloqueia: []
  origem: "Achado colateral 2026-05-19 durante NYX-AUTO-APPROVE-01: validar-acentuacao.py detectou 12 violações pré-existentes em SPRINT_ORDER_MASTER.md (linhas 307, 313, 338-343, 407, 439-446) introduzidas em commits 2ced6f8f (2026-05-17) e anteriores. Distintas das alterações da sprint corrente."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Aplicar correções literais: sessao->sessão, descricao->descrição, nao->não, verificacao->verificação, Diretorio->diretório, validacao->validação, acoes->ações"

  forbidden:
    - "Alterar conteúdo semântico das linhas (apenas trocar caracteres ASCII por acentuados)"
    - "Renomear IDs ou status de sprints (somente texto descritivo)"

  tests:
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths dev-journey/06-sprints/SPRINT_ORDER_MASTER.md"
      timeout: 30
      deve_passar: "Total: 0 violações"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"

  acceptance_criteria:
    - "validar-acentuacao.py retorna 0 violações em SPRINT_ORDER_MASTER.md"
    - "Smoke + invariantes 14/14"
```

---

# Sprint MASTER-ACENTUACAO-FIX-01

**Status:** PENDENTE
**Data criação:** 2026-05-19 (achado colateral durante NYX-AUTO-APPROVE-01)
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Durante a varredura periférica de acentuação da NYX-AUTO-APPROVE-01, `validar-acentuacao.py` detectou 12 ocorrências pré-existentes em `SPRINT_ORDER_MASTER.md` introduzidas por commits anteriores (`2ced6f8f` 2026-05-17 e outros). Conforme protocolo anti-débito (lição 5), não foram corrigidas inline na sprint corrente: viraram esta sprint dedicada.

### Violações catalogadas

```
linha 307: sessao -> sessão
linha 313: descricao -> descrição
linha 338: nao -> não, verificacao -> verificação, Diretorio -> diretório
linha 339: nao -> não
linha 343: validacao -> validação
linha 407: sessao -> sessão (2x)
linha 439: nao -> não
linha 440: nao -> não
linha 446: acoes -> ações
```

---

## Solução proposta

Aplicar correções literais via `Edit` (replace_all=false) para cada linha listada. Manter semântica e formatação.

---

## Critério binário

- [ ] `validar-acentuacao.py --paths dev-journey/06-sprints/SPRINT_ORDER_MASTER.md` retorna 0 violações
- [ ] Smoke + invariantes 14/14
- [ ] Sprint movida `producao/` -> `concluidos/`

---

*"Anti-débito: cada violação pré-existente vira sprint própria, não rejunte da sprint corrente." -- MASTER-ACENTUACAO-FIX-01*
