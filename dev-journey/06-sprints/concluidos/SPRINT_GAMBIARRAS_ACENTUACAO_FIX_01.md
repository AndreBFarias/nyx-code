# SPRINT GAMBIARRAS-ACENTUACAO-FIX-01 — Correção de acentuação em GAMBIARRAS_POR_SPRINT.md

## 0. SPEC

```yaml
sprint:
  id: GAMBIARRAS-ACENTUACAO-FIX-01
  title: "Corrige 'funcao' → 'função' em GAMBIARRAS_POR_SPRINT.md:334"  # noqa-acento
  onda: 24
  bloco: 24.4 Higiene
  prioridade: BAIXA
  tipo: Fix
  dependencias: []
  desbloqueia: [pre-commit acentuação limpo em docs]
  origem: "Achado colateral durante NYX-NO-HALLUCINATE-TOOL-01 (2026-05-19). Pré-existente em commits anteriores."

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md
      reason: "Linha 334 contém 'funcao' sem acento"  # noqa-acento

  forbidden:
    - "Adicionar conteúdo novo"
    - "Tocar outras linhas"

  acceptance_criteria:
    - "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md retorna exit 0"
    - "Único diff: linha 334 'funcao' → 'função'"  # noqa-acento
```

---

# Sprint GAMBIARRAS-ACENTUACAO-FIX-01

**Status:** CONCLUIDA (2026-05-19)
**Data criação:** 2026-05-19 (achado colateral NYX-NO-HALLUCINATE-TOOL-01)
**Modelo obrigatório:** claude-opus-4-7

---

## Contexto

Durante NYX-NO-HALLUCINATE-TOOL-01, executor rodou validador de acentuação após editar GAMBIARRAS_POR_SPRINT.md. Resultado:

```
dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md:334: 'funcao' → 'função'  # noqa-acento
Total: 1 violação(ões)
exit=1
```

Violação pré-existente (não introduzida no diff da sprint atual). Anti-débito: vira sprint própria.

## Solução

Edit cirúrgico na linha 334:

```
- **Não testar o caminho positivo** (arquivo .md real com "funcao" sem acento deve disparar warning). Obrigatório verificar ambos caminhos.  <!-- noqa-acento -->
```

vira:

```
- **Não testar o caminho positivo** (arquivo .md real com "função" sem acento deve disparar warning). Obrigatório verificar ambos caminhos.
```

## Critério binário

- [x] `python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths dev-journey/08-templates/GAMBIARRAS_POR_SPRINT.md` retorna exit 0
- [x] Sprint movida → concluidos
- [x] Commit `fix(GAMBIARRAS-ACENTUACAO-FIX-01): funcao → função em :334`  <!-- noqa-acento -->

---

## Proof-of-work

- Pre-fix: `funcao` linha 334 (`exit=1`, 1 violação)  <!-- noqa-acento -->
- Post-fix: validar-acentuacao.py `exit=0`
- Diff: 1 linha alterada (linha 334 apenas)
- Acentuação: 0 violações em arquivo tocado
