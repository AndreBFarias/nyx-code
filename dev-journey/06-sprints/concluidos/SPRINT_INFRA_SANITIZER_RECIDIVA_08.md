# SPRINT 230 — INFRA-SANITIZER-RECIDIVA-08

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-RECIDIVA-08
  title: "Restaurar glifos canônicos U+25xx em 5 arquivos protegidos (recidiva detectada na sprint 228)"
  onda: 31
  prioridade: CRÍTICA
  tipo: Bugfix
  dependencias: []
  desbloqueia: [INFRA-TUI-TESTS-MIGRATE-01]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "BULLETS sem glifos U+25xx — sintoma do vetor sanitizer histórico"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens_extended.py
      reason: "Glifo ◆ U+25C6 ausente"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Glifos ● U+25CF insuficientes (<4 esperado em _build_compact + _build_wide)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Glifo ● U+25CF ausente"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh
      reason: "Auto-proteção falhou — chr(0xNNNN) removidos das comparações ou comentários"
  creates: []
  removes: []

  n_to_n_pairs:
    - descricao: "Glifos canônicos consistentes em todos os 5 arquivos protegidos do check #14"  # noqa-acento
      paths:
        - nyx/themes/design_tokens.py
        - nyx/themes/design_tokens_extended.py
        - nyx/agent/banner.py
        - nyx/agent/repl_app.py
        - scripts/sprint_invariants.sh

  forbidden:
    - "git checkout HEAD~N -- ... CEGO (reverte mudanças legítimas das sprints 222-228)"
    - "Tocar em sprints 222-228 commitadas (já CONCLUIDAS)"
    - "Adicionar emoji (glifos U+25xx NÃO são emoji — ADR-004 exceção documentada)"
    - "Mencao a IA proprietaria em codigo/commit"   # noqa-anonimato

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 10
      deve_passar: true
    - cmd: "./run.sh --gauntlet --only rapido"
      timeout: 120
      deve_passar: true

  acceptance_criteria:
    - "Invariante #14 PASSA (PASS=14/14 FAIL=0 ou FAIL=1 se #10 ruff persiste)"
    - "Cada arquivo protegido tem >= 1 dos glifos canônicos U+25CB / U+25D0 / U+25CF / U+25C6"
    - "scripts/sprint_invariants.sh auto-proteção: cb>=3, d0>=3, cf>=3 (literais nos comentários)"
    - "Smoke boot ok"
    - "Gauntlet --only rapido APROVADO"
    - "Acentuação rc=0"
    - "Sprints 222-228 commitadas NÃO regredidas (semântica funcional preservada)"
```

---

# Sprint 230 — INFRA-SANITIZER-RECIDIVA-08

**Status:** PENDENTE
**Data criação:** 2026-05-25
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> **ADRs relevantes:**
> - ADR-004 Zero Emojis: glifos Geometric Shapes U+25xx são EXCEÇÃO documentada (não são emoji).
>
> **Estado do sistema:**
> - Invariante #14 (defesa anti-sanitizer) declarado em `scripts/sprint_invariants.sh:207-300`.
> - Último commit limpo: `1548c10` (Sprint 195 INFRA-SANITIZER-RECIDIVA-07, 2026-05-22).
> - Sprints 222-228 commitaram com FAIL=2 (incluindo #14) declarando "pré-existente". Recidiva ativa do vetor histórico.
> - 5 arquivos com glifos zerados:
>   - `nyx/themes/design_tokens.py`: BULLETS sem glifos
>   - `nyx/themes/design_tokens_extended.py`: ◆ U+25C6 ausente
>   - `nyx/agent/banner.py`: ● U+25CF insuficiente
>   - `nyx/agent/repl_app.py`: ● U+25CF ausente
>   - `scripts/sprint_invariants.sh`: chr(0xNNNN) removidos

---

## Problema

Working tree dos 5 arquivos protegidos pelo invariante #14 sofreu corrupção do vetor histórico do sanitizer (catalogado em `VECTOR-AUDIT-01` linha 95-104 do `VALIDATOR_BRIEF.md`). Glifos U+25CB/D0/CF/C6 foram substituídos por strings vazias ou neutralizados.

### Sintoma observável

```bash
$ python3 -c "from pathlib import Path; [print(f, p.count(chr(0x25CF)), p.count(chr(0x25CB)), p.count(chr(0x25D0)), p.count(chr(0x25C6))) for f in ['nyx/themes/design_tokens.py','nyx/themes/design_tokens_extended.py','nyx/agent/banner.py','nyx/agent/repl_app.py','scripts/sprint_invariants.sh'] for p in [Path(f).read_text()]]"
nyx/themes/design_tokens.py 0 0 0 0
nyx/themes/design_tokens_extended.py 0 0 0 0
nyx/agent/banner.py 0 0 0 0
nyx/agent/repl_app.py 0 0 0 0
scripts/sprint_invariants.sh 0 0 0 0
```

Zero glifos em todos. Invariante #14 detectaria mas a defesa também foi neutralizada (chr(0xNNNN) removidos do sprint_invariants.sh).

---

## Solução proposta

Restauração cirúrgica via referência a `git show 1548c10:<path>` para cada arquivo. Para cada arquivo:

1. Listar localizações dos glifos no commit limpo via `git show 1548c10:<path> | python3 -c "..."`.
2. Aplicar `Edit` pontual restaurando os glifos SEM tocar nas mudanças legítimas das sprints 222-228.
3. Re-validar `bash scripts/sprint_invariants.sh` PASS na linha #14.

**NÃO usar `git checkout 1548c10 -- <path>`**: reverteria as mudanças legítimas dos sprints intermediários. Ex.: `nyx/agent/banner.py` ganhou parâmetro `cursor` na sprint 225; `nyx/agent/repl_app.py` ganhou ScrollbarMargin nas sprints 226 e 228.

---

## Arquivos alvo (estratégia por arquivo)

### `nyx/themes/design_tokens.py` — BULLETS

`git show 1548c10:nyx/themes/design_tokens.py | grep -A8 "BULLETS"` revela:
```python
BULLETS = {
    "ready":   chr(0x25CF),      # ●
    "tool_ok": chr(0x25CF),      # ●
    "tool_err":chr(0x25CF),      # ●
    "working": chr(0x25CB),      # ○
    ...
}
```

Sprint 230 restaura via `chr(0xNNNN)` (resistente a sanitizer literal). Comparar com working tree atual e aplicar Edit nos valores corrompidos.

### `nyx/themes/design_tokens_extended.py` — ◆

Glifo `chr(0x25C6)` usado para "themes extended" (diamond). Restaurar via `git show 1548c10:nyx/themes/design_tokens_extended.py | grep "0x25C6\|◆"`.

### `nyx/agent/banner.py` — ●

Invariante exige >=4 ocorrências de ● em `_build_compact` + `_build_wide`. Atualmente zero. Mas sprint 225 mexeu nesse arquivo (cursor parameter). Restaurar glifos sem desfazer mudança da 225.

### `nyx/agent/repl_app.py` — ●

>=1 ocorrência de ●. Sprints 226 + 228 mexeram (ScrollbarMargin). Edit cirúrgico em local separado dos diffs das sprints.

### `scripts/sprint_invariants.sh` — chr(0xNNNN)

Auto-proteção precisa de >=3 de cada (`cb`, `d0`, `cf`). Restaurar literais nos comentários da seção [check 14]. Se sanitizer atacou o source, restaurar via `git show 1548c10:scripts/sprint_invariants.sh`.

---

## Diff esperado (resumo)

```
~ 5 arquivos modificados
+ ~30-50 linhas líquidas (glifos + comentários restaurados)
```

---

## Comandos de verificação

```bash
# 1. Snapshot ANTES (sanity check do sintoma)
python3 -c "
from pathlib import Path
for f in ['nyx/themes/design_tokens.py','nyx/themes/design_tokens_extended.py',
          'nyx/agent/banner.py','nyx/agent/repl_app.py','scripts/sprint_invariants.sh']:
    p = Path(f).read_text()
    print(f, 'cf=', p.count(chr(0x25CF)), 'cb=', p.count(chr(0x25CB)),
          'd0=', p.count(chr(0x25D0)), 'c6=', p.count(chr(0x25C6)))
"

# 2. Aplicar Edits (estratégia por arquivo)

# 3. Snapshot DEPOIS (confirmar restauração)
python3 -c "..."  # mesmo comando

# 4. Invariante #14 deve PASSAR
bash scripts/sprint_invariants.sh
# Esperado: PASS=14 FAIL=0 (ou FAIL=1 se ruff #10 persiste em outro arquivo)

# 5. Smoke + gauntlet
./run.sh --smoke
./run.sh --gauntlet --only rapido

# 6. Acentuação
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths nyx/themes/design_tokens.py nyx/themes/design_tokens_extended.py nyx/agent/banner.py nyx/agent/repl_app.py scripts/sprint_invariants.sh

# 7. Cleanup VRAM
pkill -f "nyx/proxy.py" || true
pkill -f "ollama serve" || true
nvidia-smi
```

---

## Critério binário de aceite

- [ ] 5 arquivos com `>=1` glifo canônico U+25xx cada.
- [ ] `sprint_invariants.sh` auto-proteção: cb>=3, d0>=3, cf>=3 (literais).
- [ ] Invariante #14 PASS.
- [ ] FAIL_AFTER <= FAIL_BEFORE - 1 (defesa anti-sanitizer destravada).
- [ ] Smoke + gauntlet rapido OK.
- [ ] Sprints 222-228 NÃO regredidas (semântica funcional preservada — verificar via gauntlet).
- [ ] Spec movida producao/ → concluidos/.
- [ ] MASTER entry 230 PENDENTE → CONCLUIDA.

---

## Proof-of-work (4 passos)

```bash
# PASSO 1: snapshot ANTES
bash scripts/sprint_invariants.sh > /tmp/inv_before_230.txt 2>&1
FAIL_BEFORE=$(grep -c "^\[FAIL\]" /tmp/inv_before_230.txt)
echo "FAIL inicial: $FAIL_BEFORE"   # esperado 2

# PASSO 2: Edits cirúrgicos nos 5 arquivos

# PASSO 3: snapshot DEPOIS
bash scripts/sprint_invariants.sh > /tmp/inv_after_230.txt 2>&1
FAIL_AFTER=$(grep -c "^\[FAIL\]" /tmp/inv_after_230.txt)
echo "FAIL final: $FAIL_AFTER"   # esperado 0 ou 1 (se ruff #10 persiste)

# PASSO 4: regra binária
diff /tmp/inv_before_230.txt /tmp/inv_after_230.txt
```

---

## Riscos

| Risco | Mitigação |
|---|---|
| Restaurar via `git checkout` cego reverte sprints 225/226/228 | Usar Edit cirúrgico com `chr(0xNNNN)` em vez de glifo literal (resiste a sanitizer hostil) |
| Sanitizer re-ataca após o fix | Catalogar próximos passos: INFRA-SANITIZER-ATTACK-TRAP-01 (honeytrap) + WORKING-TREE-GUARD-01 já existe sprint 196 |
| Outras strings com U+25xx em arquivos não protegidos podem estar corrompidas (silenciosamente) | Spec foca nos 5 arquivos do invariante #14; varredura ampla fica para sprint futura |

---

*"Defesa que se neutraliza a si mesma é decorativa. Defesa que persiste é estrutural." — princípio anti-sanitizer*
