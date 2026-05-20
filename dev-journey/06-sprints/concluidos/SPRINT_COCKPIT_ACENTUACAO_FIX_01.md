# SPRINT COCKPIT-ACENTUACAO-FIX-01 — Acentuação em strings de microcopy do server.py

## 0. SPEC

```yaml
sprint:
  id: COCKPIT-ACENTUACAO-FIX-01
  title: "Corrigir acentos em microcopy do cockpit server.py"
  onda: 24
  bloco: 24.3 Cockpit
  prioridade: BAIXA
  tipo: Higiene
  dependencias: []
  desbloqueia: []
  origem: "Achado colateral durante COCKPIT-LIFECYCLE-FIX-01 (2026-05-19). Validador de acentuação reportou 5 violações pré-existentes em nyx/cockpit/server.py."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cockpit/server.py
      reason: "5 strings sem acentuação correta nas linhas 162, 261-264"

  forbidden:
    - "Alterar lógica do cockpit"
    - "Modificar API contracts (chaves do dict /api/microcopy)"

  acceptance_criteria:
    - "Linha 162: 'nao deve crashar' → 'não deve crashar' (comentário)"
    - "Linhas 261-264: 'nenhuma sessao', 'sessao salva', 'sessao restaurada', 'sessao limpa' → 'sessão ...'"
    - "Validador ~/.config/zsh/scripts/validar-acentuacao.py retorna 0 violações"
    - "Smoke + invariantes 14/14"
```

---

# Sprint COCKPIT-ACENTUACAO-FIX-01

**Status:** CONCLUIDA (header corrigido em MASTER-CLEANUP-02 2026-05-20; presença em concluidos/ implica CONCLUIDA conforme convenção do projeto)
**Data criação:** 2026-05-19 (achado colateral)
**Modelo obrigatório:** claude-opus-4-7

## Contexto

Durante COCKPIT-LIFECYCLE-FIX-01, varredura de acentuação (check #4 do BRIEF) detectou 5 violações pré-existentes em `nyx/cockpit/server.py`:

```
nyx/cockpit/server.py:162: 'nao' → 'não'
nyx/cockpit/server.py:261: 'sessao' → 'sessão'
nyx/cockpit/server.py:262: 'sessao' → 'sessão'
nyx/cockpit/server.py:263: 'sessao' → 'sessão'
nyx/cockpit/server.py:264: 'sessao' → 'sessão'
```

Linhas 261-264 são strings de microcopy expostas via `/api/microcopy` (consumidas pelo frontend). Mudança altera texto visível para usuário (positivamente: acentuação correta).

## Critério binário

- [ ] 5 violações corrigidas
- [ ] Validador exit 0 em server.py
- [ ] Smoke + invariantes 14/14
- [ ] Commit `fix(COCKPIT-ACENTUACAO-FIX-01): acentua strings de microcopy`

---

*"Acentuação correta é parte do contrato de qualidade." -- COCKPIT-ACENTUACAO-FIX-01*
