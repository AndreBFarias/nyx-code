# SPRINT CHECKPOINT-ACENTUACAO-FIX-01 -- Corrigir 21 violações de acentuação em Checkpoint.md

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: CHECKPOINT-ACENTUACAO-FIX-01
  title: "Acentuação: 21 violações em Checkpoint.md (anti-débito de VALIDATE-FINAL-01-PARTE-2)"
  onda: 24
  bloco: 24.5 Release
  prioridade: BAIXA
  tipo: Cleanup
  dependencias: []
  desbloqueia: [tag v1.0]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/Checkpoint.md
      reason: "Corrigir 21 violações pre-existentes em linhas 26, 32, 33, 34, 36, 40, 74, 77, 80, 92, 111, 132, 144, 203, 258"
  creates: []
  removes: []

  forbidden:
    - "Adicionar entradas novas em Checkpoint.md (escopo é APENAS o fix)"
    - "Reescrever palavras corretas"

  tests:
    - cmd: "python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths Checkpoint.md"
      timeout: 5
      deve_passar: "exit 0 (zero violação)"

  acceptance_criteria:
    - "validar-acentuacao.py --paths Checkpoint.md exit 0"
    - "Conteúdo semântico preservado (zero alteração além de acentos)"
```

---

# Sprint CHECKPOINT-ACENTUACAO-FIX-01

**Status:** PENDENTE
**Data criação:** 2026-05-19 (anti-débito de VALIDATE-FINAL-01-PARTE-2)

## Contexto

VALIDATE-FINAL-01-PARTE-2 (sessão 2026-05-19) detectou 21 violações de acentuação em `Checkpoint.md`. Todas pre-existem das sessões anteriores. Anti-débito: não corrigir inline, materializar sprint nova.

Violações catalogadas: `nao` → `não`, `sessao` → `sessão`, `proximo` → `próximo`, `historico` → `histórico`, `funcao` → `função`, `execucao` → `execução`, `descricao` → `descrição`, `Validacao` → `validação`.  <!-- noqa-acento -->  <!-- bloco de mapeamentos pedagógicos ASCII→acentuado -->

<!-- noqa-acento -->
<!-- noqa-acento -->
<!-- noqa-acento -->
<!-- noqa-acento -->
<!-- noqa-acento -->
<!-- noqa-acento -->
<!-- noqa-acento -->
<!-- noqa-acento -->

## Solução

```bash
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths Checkpoint.md --fix
# Verificar diff (preserva apenas acentos)
git diff Checkpoint.md
# Confirmar 0 violações
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths Checkpoint.md && echo "OK"
```

## Critério binário de aceite

- [ ] `validar-acentuacao.py --paths Checkpoint.md` exit 0
- [ ] Diff mostra apenas substituições de acentuação
- [ ] Sprint movida `producao/` → `concluidos/`

---

*"A constância da grafia é higiene mental." -- CHECKPOINT-ACENTUACAO-FIX-01*
