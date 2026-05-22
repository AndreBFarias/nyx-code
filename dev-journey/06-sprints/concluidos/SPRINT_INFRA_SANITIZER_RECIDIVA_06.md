## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-RECIDIVA-06
  title: "Restaurar 7 arquivos protegidos pelo invariante #14 após recidiva do sanitizer histórico"
  onda: 29
  prioridade: CRÍTICA
  tipo: Hotfix
  dependencias: []
  desbloqueia: [TUI-STATE-GLYPHS-SYNC-06, TUI-INPUT-DEADLOCK-01, TUI-BANNER-DEDUP-02, TUI-BANNER-BLINK-SOFT-03, TUI-CTRL-Q-OLLAMA-STOP-04, TUI-CTRL-D-PARITY-05, TUI-SIGINT-RECLAIM-07]

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Restaurar 3 glifos Geometric Shapes em _STATE_GLYPHS (U+25CB/D0/CF) corrompidos pelo sanitizer histórico"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/repl_app.py
      reason: "Restaurar glifo ● em _STATE_GLYPHS local + BULLET bypass_on"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/banner.py
      reason: "Restaurar glifos ● do _build_compact e _build_wide (>=4 ocorrências)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Restaurar glifo ◐ do build_warming_label"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens.py
      reason: "Restaurar BULLETS canônicos (○ ◐ ●)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/themes/design_tokens_extended.py
      reason: "Restaurar glifo ◆ (>=1 ocorrência)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/sprint_invariants.sh
      reason: "Restaurar auto-proteção do próprio defensor (>=3 ocorrências de cada glifo no source)"

  forbidden:
    - "Aplicar git checkout em arquivos fora desses 7 (escopo cirúrgico)"
    - "Modificar conteúdo lógico — apenas restaurar glifos canônicos do HEAD"
    - "Tocar specs/docs"
    - "Adicionar emoji"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "bash scripts/sprint_invariants.sh -> PASS 14/14, FAIL 0 (incluindo check #14)"
    - "smoke boot ok exit 0 antes e depois"
    - "git diff dos 7 arquivos mostra APENAS reintrodução dos glifos U+25CB/D0/CF/C6 — zero mudança lógica"
    - "Acentuação PT-BR rc=0 nos 7 arquivos"
```

---

# Sprint INFRA-SANITIZER-RECIDIVA-06 — Restauração emergencial

**Status:** PENDENTE
**Data criação:** 2026-05-21
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto do projeto (snapshot)

> - VALIDATOR_BRIEF.md §[CORE] Defesa anti-sanitizer documenta o vetor histórico de 2026-05-20 que corrompeu 57 arquivos via remoção em massa de glifos Geometric Shapes.
> - INFRA-SANITIZER-FIX-05 (2026-05-21) endureceu o defensor (check #14 do `scripts/sprint_invariants.sh`) usando `chr(0xNNNN)` em vez de literais — auto-neutralização do defensor pelo sanitizer eliminada.
> - **Recidiva detectada agora (2026-05-21, segunda ocorrência do dia):** working tree apresenta os mesmos 7 arquivos modificados (M) com glifos removidos. INFRA-SANITIZER-FIX-05 imunizou o DEFENSOR mas não os ARQUIVOS protegidos.

---

## Problema

`bash scripts/sprint_invariants.sh` retorna:

```
[FAIL] 14. glifos canônicos preservados (anti-sanitizer)
       nyx/cli.py: codepoints insuficientes (cb=0, d0=0, cf=0);
       nyx/themes/design_tokens.py: BULLETS sem glifos (cf=0, cb=0);
       nyx/agent/output.py: build_warming_label sem glifo ◐ (d0=0);
       nyx/agent/banner.py: glifos ● insuficientes (cf=0, esperado>=4);
       nyx/agent/repl_app.py: glifo ● insuficiente (cf=0, esperado>=1);
       nyx/themes/design_tokens_extended.py: glifo ◆ insuficiente (cf=0, esperado>=1);
       scripts/sprint_invariants.sh: auto-proteção falhou (cb=0, d0=0, cf=0).
```

`git status -s` confirma: os 7 arquivos protegidos estão com modificação no working tree, todos sem commit. Smoke ainda passa (boot não exercita invariante #14).

Estado é idêntico ao incidente documentado em Checkpoint.md:25 (sessão 2026-05-21 ~12:00) — restauração foi feita via `git checkout HEAD -- .`.

Esta sprint formaliza essa restauração como hotfix cirúrgico nos 7 arquivos específicos (não no working tree inteiro, escopo controlado).

---

## Solução proposta

Aplicar `git checkout HEAD -- <7 arquivos>` exatamente nos paths protegidos pelo invariante #14, restaurando os bytes do último commit (HEAD canônico).

---

## Implementação literal

```bash
cd /home/andrefarias/Desenvolvimento/Nyx-Code

# Restauração cirúrgica dos 7 arquivos protegidos.
git checkout HEAD -- \
    nyx/cli.py \
    nyx/agent/repl_app.py \
    nyx/agent/banner.py \
    nyx/agent/output.py \
    nyx/themes/design_tokens.py \
    nyx/themes/design_tokens_extended.py \
    scripts/sprint_invariants.sh

# Confirmar restauração via byte-level check.
python3 -c "
from pathlib import Path
for f in [
    'nyx/cli.py', 'nyx/agent/repl_app.py', 'nyx/agent/banner.py',
    'nyx/agent/output.py', 'nyx/themes/design_tokens.py',
    'nyx/themes/design_tokens_extended.py', 'scripts/sprint_invariants.sh',
]:
    t = Path(f).read_text()
    cb, d0, cf, dm = chr(0x25CB), chr(0x25D0), chr(0x25CF), chr(0x25C6)
    print(f'{f}: cb={t.count(cb)}, d0={t.count(d0)}, cf={t.count(cf)}, dm={t.count(dm)}')
"

# Invariantes integrais.
bash scripts/sprint_invariants.sh

# Smoke.
./run.sh --smoke
```

---

## Diff esperado

```
~ 7 arquivos restaurados
+ ~30 caracteres líquidos (glifos Geometric Shapes reintroduzidos)
- 0 linhas (sem mudança lógica)
```

`git diff` deve mostrar apenas reintrodução dos glifos U+25CB, U+25D0, U+25CF, U+25C6 em posições específicas.

---

## Comandos de verificação

```bash
# 1. Pré: invariantes failing
bash scripts/sprint_invariants.sh | tail -5
# esperado ANTES: FAIL 1 (check #14)

# 2. Restauração (acima)

# 3. Pós: invariantes OK
bash scripts/sprint_invariants.sh | tail -5
# esperado DEPOIS: PASS 14, FAIL 0

# 4. Smoke
./run.sh --smoke
# esperado: boot ok exit 0

# 5. Acentuação dos 7 arquivos
python3 ~/.config/zsh/scripts/validar-acentuacao.py --paths \
    nyx/cli.py nyx/agent/repl_app.py nyx/agent/banner.py \
    nyx/agent/output.py nyx/themes/design_tokens.py \
    nyx/themes/design_tokens_extended.py scripts/sprint_invariants.sh
# esperado: exit 0

# 6. Diff mostra apenas glifos reintroduzidos (zero mudança lógica)
git diff HEAD~1 -- nyx/cli.py | head -30
```

---

## Critério binário de aceite

- [ ] `bash scripts/sprint_invariants.sh` retorna PASS 14, FAIL 0
- [ ] `./run.sh --smoke` retorna `boot ok` exit 0
- [ ] `git diff` dos 7 arquivos vs HEAD pré-sprint mostra apenas glifos U+25CB/D0/CF/C6 reintroduzidos
- [ ] Acentuação PT-BR rc=0 nos 7 arquivos
- [ ] Nenhuma violação de forbidden[]

---

## Achados colaterais (anti-débito obrigatório)

Esta é a **segunda recidiva no mesmo dia** (2026-05-21). INFRA-SANITIZER-FIX-05 imunizou o DEFENSOR mas o vetor que ataca os ARQUIVOS protegidos continua ativo. Catalogar como achado **CRÍTICO**:

- **Sprint nova sugerida:** `INFRA-SANITIZER-VECTOR-AUDIT-01` — rastrear de onde vem o ataque (hook git, sanitizer global, operação de mass-edit, etc.) e neutralizar definitivamente. Ações: audit completo de `~/.config/git/hooks/*`, `~/.config/zsh/scripts/*sanitizer*`, e qualquer outro automatismo que toque o working tree.

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| `git checkout HEAD --` perde mudanças legítimas | Sanity-check via `git diff` antes — confirmado: zero mudança lógica nesses 7 arquivos |
| Recidiva imediata após restauração | Aceitar como evento documentado; INFRA-SANITIZER-VECTOR-AUDIT-01 endereça a causa raiz |
| Restauração introduzir desync com docs | Os glifos restaurados vêm do HEAD — docs já refletiam esse estado |

---

*"Restaurar é necessário; rastrear o vetor é dever." -- princípio anti-débito Nyx-Code.*
