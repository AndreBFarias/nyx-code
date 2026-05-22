## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-RECIDIVA-07
  title: "Restaurar 4 arquivos atacados pela TERCEIRA recidiva do sanitizer (mesma sessão da audit-01)"
  onda: 29
  prioridade: CRÍTICA
  tipo: Hotfix
  dependencias: [INFRA-SANITIZER-RECIDIVA-06, INFRA-SANITIZER-VECTOR-AUDIT-01]
  desbloqueia: [TUI-BLINK-SOFT-REVERT-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "BULLETS dict literais ● removidos pelo sanitizer — restaurar via git checkout HEAD"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Glifos ◐ ◼ ◻ ▶ ▼ ● ◆ removidos em 5 funções de render — restaurar"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens_extended.py
      reason: "◆ removido — restaurar"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh
      reason: "Literais protetores removidos (auto-proteção neutralizada) — restaurar"

  forbidden:
    - "Aplicar git checkout fora desses 4 arquivos"
    - "Modificar conteúdo lógico — apenas restaurar glifos do HEAD"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true

  acceptance_criteria:
    - "bash scripts/sprint_invariants.sh -> PASS 14/14, FAIL 0"
    - "git diff dos 4 arquivos vs working tree pré-restauração mostra apenas reintrodução de U+25xx"
```

---

# Sprint INFRA-SANITIZER-RECIDIVA-07 — Terceira recidiva

**Status:** CONCLUIDA
**Data criação:** 2026-05-22
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> - INFRA-SANITIZER-RECIDIVA-06 (2026-05-21 ~17h, commit d84bf93) restaurou 7 arquivos protegidos pelo invariante #14 após segundo ataque do dia.
> - INFRA-SANITIZER-VECTOR-AUDIT-01 (2026-05-21 ~21h, commit dfdd5ae) absolveu o sanitizer global atual (`~/.config/zsh/scripts/universal-sanitizer.py` mtime 2026-05-20 19:27) via experimento empírico — SHA pré/pós da isca idênticos.
> - **TERCEIRA recidiva detectada agora (2026-05-22 ~00:30)**: durante execução da sprint TUI-BLINK-SOFT-REVERT-01, executor-sprint encontrou 4 arquivos com glifos novamente removidos.

---

## Problema

Após o audit que absolveu o sanitizer atual, terceira recidiva ocorreu. 4 arquivos atacados (subset dos 7 da recidiva-06):

```
[FAIL] 14. glifos canônicos preservados (anti-sanitizer)
  nyx/themes/design_tokens.py: BULLETS sem glifos
  nyx/agent/output.py: ◐ ◼ ◻ ▶ ▼ ● ◆ removidos
  nyx/themes/design_tokens_extended.py: ◆ ausente
  scripts/sprint_invariants.sh: auto-proteção neutralizada
```

Causa raiz permanece em aberto — VECTOR-AUDIT-01 absolveu o sanitizer atual via prova empírica, mas o ataque continua acontecendo. Hipóteses não-descartadas:
- Versão histórica do sanitizer ainda invocada por algum hook não-óbvio.
- Mass-edit operation via outra ferramenta.
- Sanitizer rodando dentro de algum agent/hook não capturável sem HISTFILE persistente.

---

## Solução aplicada

Restauração cirúrgica via `git checkout HEAD --` nos 4 paths atacados. Idêntico à recidiva-06.

```bash
git checkout HEAD -- \
    nyx/themes/design_tokens.py \
    nyx/agent/output.py \
    nyx/themes/design_tokens_extended.py \
    scripts/sprint_invariants.sh
```

---

## Proof-of-work

Pós-restauração:

```
bash scripts/sprint_invariants.sh
[OK] 14. glifos canônicos preservados (anti-sanitizer)
-- Resumo --
PASS: 14
FAIL: 0
```

---

## Achados colaterais

3 recidivas confirmadas em ~12h (2026-05-21 12h → 2026-05-21 17h → 2026-05-22 00h30). VECTOR-AUDIT-01 absolveu o sanitizer atual mas não conseguiu rastrear o vetor real. Padrão sugere:

1. **Vetor não-óbvio**: hook git auxiliar, watchdog, ou execução manual fortuita da versão histórica.
2. **Defense-in-depth ativo**: invariante #14 detecta e supervisor restaura — pipeline funciona como defesa.
3. **Pressão para implementar 1 das 3 sugestões da VECTOR-AUDIT-01**:
   - A) HISTFILE persistente do zsh com timestamps
   - B) Sprint INFRA-SANITIZER-ATTACK-TRAP-01 (honeytrap append-only)
   - C) Sprint INFRA-SANITIZER-WORKING-TREE-GUARD-01 (heurística no pre-commit local)

Recomendação: priorizar (C) — pre-commit guard que detecta diff "só remove U+25xx" e BLOQUEIA o commit. Mesmo sem rastrear o vetor, o working tree não pode ser publicado corrompido.

---

*"Reincidência confirma padrão. Padrão confirma defesa em camadas." -- princípio anti-sanitizer Nyx-Code.*
