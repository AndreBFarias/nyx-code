# SPRINT INFRA-SANITIZER-FIX-04 -- Recuperação cirúrgica do working tree + endurecimento invariante #14

## 0. SPEC

```yaml
sprint:
  id: INFRA-SANITIZER-FIX-04
  title: "Recuperação cirúrgica de 57 arquivos + endurecimento invariante 14 com auto-proteção"
  onda: 24
  bloco: 24.5 Release (anti-débito)
  prioridade: CRITICA
  tipo: Fix + Endurecimento
  dependencias: [INFRA-SANITIZER-SOURCE-01]
  desbloqueia: [INFRA-INSTALL-ZSTD-FALLBACK-01, GAUNTLET-FIXTURES-SANDBOX-01, K08-VRAM-RUNNER-ISOLATION-01, VALIDATE-VISUAL-MIDFRAME-01]

  touches:
    - path: nyx/cli.py
      reason: "Revert lote 1 (Python crítico): _STATE_GLYPHS restaurado"
    - path: nyx/agent/banner.py
      reason: "Revert lote 1: 6× ● restaurados em _build_compact + _build_wide"
    - path: nyx/agent/output.py
      reason: "Revert lote 1: ◼/◻/▶ restaurados em render_todo_block + render_thinking_block"
    - path: nyx/agent/repl_app.py
      reason: "Revert lote 1: 1× ● restaurado"
    - path: nyx/themes/design_tokens.py
      reason: "Revert lote 1: BULLETS + TOOL_GLYPHS restaurados (●=10 ○=4 ◐=2)"
    - path: nyx/themes/design_tokens_extended.py
      reason: "Revert lote 1: ◆ restaurado"
    - path: scripts/sprint_invariants.sh
      reason: "Revert lote 1 + endurecimento: cobertura ampliada + auto-proteção check 14"
    - path: nyx/cockpit/static/vendor/xterm.js
      reason: "Revert lote 2: 553KB lib vendored restaurada"
    - path: novo_layout/v2_referencias/app.jsx
      reason: "Revert lote 3: ▶ restaurado em Variações subtitle"
    - path: novo_layout/v2_referencias/audit.jsx
      reason: "Revert lote 3"
    - path: novo_layout/v2_referencias/nyx-session-render.jsx
      reason: "Revert lote 3"
    - path: novo_layout/v2_referencias/nyx-themes.jsx
      reason: "Revert lote 3"
    - path: Checkpoint.md
      reason: "Revert lote 4 + re-aplicação do write-through (linha de retomada atualizada)"
    - path: PROMPT_VALIDADOR_INTEGRADOR.md
      reason: "Revert lote 4"
    - path: dev-journey/03-decisions/ADR_027_PROGRESSAO_IDENTIDADE.md
      reason: "Revert lote 4"
    - path: dev-journey/03-decisions/ADR_029_LAYOUT_PARITY.md
      reason: "Revert lote 4"
    - path: dev-journey/05-guides/MICROCOPY.md
      reason: "Revert lote 4"
    - path: dev-journey/06-sprints/SPRINT_ORDER_MASTER.md
      reason: "Revert lote 4 + linhas 125c/125d adicionadas (INFRA-SANITIZER-SOURCE-01, INFRA-SANITIZER-FIX-04)"
    - path: "dev-journey/06-sprints/concluidos/SPRINT_*.md (várias)"
      reason: "Revert lote 4: 24 sprints concluídas com glifos restaurados"
    - path: "dev-journey/07-reports/*.md (5 arquivos)"
      reason: "Revert lote 4"

  creates:
    - path: dev-journey/06-sprints/concluidos/SPRINT_INFRA_SANITIZER_SOURCE_01.md
      reason: "Documentação do diagnóstico do vetor"
    - path: dev-journey/06-sprints/concluidos/SPRINT_INFRA_SANITIZER_FIX_04.md
      reason: "Este arquivo: registro da recuperação + endurecimento"

  removes: []

  forbidden:
    - "Modificar conteúdo dos arquivos revertidos além do git checkout HEAD"
    - "Bloquear universal-sanitizer.py (versão atual está correta)"
    - "Editar core.hookspath ou config global de git (settings.json deny ativo)"

  tests:
    - cmd: "./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: "PASS 14, FAIL 0 (real, com guards novos)"
    - cmd: "python3 -c 'from pathlib import Path; p=Path(\"nyx/cli.py\").read_text(); assert p.count(chr(9675))>=1 and p.count(chr(9680))>=1 and p.count(chr(9679))>=1'"
      timeout: 5
      deve_passar: "exit 0 (glifos canônicos restaurados em cli.py)"
    - cmd: "python3 -c 'from pathlib import Path; p=Path(\"scripts/sprint_invariants.sh\").read_text(); assert p.count(chr(9675))>=3 and p.count(chr(9680))>=3 and p.count(chr(9679))>=3'"
      timeout: 5
      deve_passar: "exit 0 (auto-proteção: 3+ de cada glifo no próprio script)"

  acceptance_criteria:
    - "git diff vazio (working tree limpo após revert + edits intencionais)"
    - "Smoke boot ok"
    - "Invariantes 14/14 PASS REAL (não falsificado)"
    - "scripts/sprint_invariants.sh com auto-proteção: ○>=3, ◐>=3, ●>=3 no próprio source"
    - "Cobertura ampliada do check 14: banner.py(●>=4), repl_app.py(●>=1), design_tokens_extended.py(◆>=1)"
    - "Checkpoint.md atualizado com diagnóstico + recuperação"
```

---

**Status:** CONCLUIDA (2026-05-19)
**Data:** 2026-05-19
**Modelo:** claude-opus-4-7 (sessão validador/integrador/despachador)

## Contexto

Anti-débito derivado de INFRA-SANITIZER-SOURCE-01. As 57 modificações destrutivas do working tree (resíduo histórico do `universal-sanitizer.py` versão antiga) recuperadas em 4 lotes cirúrgicos. Invariante #14 endurecido para cobrir os arquivos que o sanitizer antigo destruiu mas o check não cobria, mais auto-proteção contra futura neutralização do próprio script.

## Recuperação cirúrgica (4 lotes)

**Lote 1 — 7 Python crítico:**
```
git checkout HEAD -- nyx/cli.py nyx/agent/banner.py nyx/agent/output.py \
  nyx/agent/repl_app.py nyx/themes/design_tokens.py \
  nyx/themes/design_tokens_extended.py scripts/sprint_invariants.sh
```
- Verificação: `nyx/cli.py: ○=1 ◐=1 ●=1` (3 glifos no `_STATE_GLYPHS`)
- `nyx/themes/design_tokens.py: ●=10 ○=4 ◐=2` (BULLETS + TOOL_GLYPHS íntegros)
- `nyx/agent/banner.py: ●=6` (build_compact + build_wide)
- `scripts/sprint_invariants.sh: ○=5 ◐=6 ●=5` (defesa restaurada)

**Lote 2 — vendor lib:**
```
git checkout HEAD -- nyx/cockpit/static/vendor/xterm.js
```
- Verificação: 283.405 bytes (tamanho original)

**Lote 3 — JSX layout:**
```
git checkout HEAD -- novo_layout/v2_referencias/app.jsx \
  novo_layout/v2_referencias/audit.jsx \
  novo_layout/v2_referencias/nyx-session-render.jsx \
  novo_layout/v2_referencias/nyx-themes.jsx
```
- Verificação: ▶ restaurado em app.jsx (1 ocorrência)

**Lote 4 — 45 docs/sprints/.md:**
```
git diff --name-only -- '*.md' | xargs git checkout HEAD --
```
- 45 arquivos revertidos
- Side-effect: Checkpoint.md retornou ao 8101062, perdendo o write-through pré-recuperação. Re-aplicado em edit explícito posterior.

## Endurecimento invariante #14

Modificações em `scripts/sprint_invariants.sh:240` (após o bloco `out = Path("nyx/agent/output.py")`):

```python
# INFRA-SANITIZER-FIX-04: cobertura ampliada para arquivos que o sanitizer
# antigo destruiu mas o check #14 não cobria (banner.py, repl_app.py,
# design_tokens_extended.py).
bn = Path("nyx/agent/banner.py").read_text(encoding="utf-8")
if bn.count("●") < 4:
    fails.append(f"nyx/agent/banner.py: glifos ● insuficientes (cf={bn.count('●')}, esperado>=4 em _build_compact + _build_wide)")

repl = Path("nyx/agent/repl_app.py").read_text(encoding="utf-8")
if repl.count("●") < 1:
    fails.append(f"nyx/agent/repl_app.py: glifo ● insuficiente (cf={repl.count('●')}, esperado>=1)")

dte = Path("nyx/themes/design_tokens_extended.py").read_text(encoding="utf-8")
if dte.count("◆") < 1:
    fails.append(f"nyx/themes/design_tokens_extended.py: glifo ◆ insuficiente (cf={dte.count('◆')}, esperado>=1)")

# INFRA-SANITIZER-FIX-04: auto-proteção. O próprio sprint_invariants.sh
# precisa preservar os 3 glifos canônicos na definição deste check; sanitizer
# que neutralize o check seria pego aqui.
inv = Path("scripts/sprint_invariants.sh").read_text(encoding="utf-8")
if inv.count("○") < 3 or inv.count("◐") < 3 or inv.count("●") < 3:
    fails.append(f"scripts/sprint_invariants.sh: auto-proteção falhou (cb={inv.count('○')}, d0={inv.count('◐')}, cf={inv.count('●')}, esperado>=3 cada para garantir check #14 não-neutralizado)")
```

## Proof-of-work

```
[pre]
git status --short | wc -l → 57 (modificações destrutivas pendentes)
bash scripts/sprint_invariants.sh → 14/14 PASS (falso — check #14 neutralizado)

[lote 1]
git checkout HEAD -- [7 arquivos]
python3 -c "from pathlib import Path; p=Path('nyx/cli.py').read_text(); print(p.count(chr(9675)), p.count(chr(9680)), p.count(chr(9679)))" → 1 1 1
bash scripts/sprint_invariants.sh → 14/14 PASS (real)

[lote 2]
git checkout HEAD -- nyx/cockpit/static/vendor/xterm.js
wc -c nyx/cockpit/static/vendor/xterm.js → 283405

[lote 3]
git checkout HEAD -- novo_layout/v2_referencias/*.jsx
grep -c "▶" novo_layout/v2_referencias/app.jsx → 1

[lote 4]
git diff --name-only -- '*.md' | xargs git checkout HEAD --
git status --short | wc -l → 1 (apenas SPRINT_INFRA_SANITIZER_SOURCE_01.md untracked)

[endurecimento]
Edit scripts/sprint_invariants.sh: +3 blocos de cobertura ampliada + 1 bloco auto-proteção
python3 -c "from pathlib import Path; inv=Path('scripts/sprint_invariants.sh').read_text(); print(inv.count(chr(9675)), inv.count(chr(9680)), inv.count(chr(9679)))" → 7 8 13 (auto-proteção OK)
bash scripts/sprint_invariants.sh → 14/14 PASS (REAL com guards novos)
./run.sh --smoke → boot ok

[final]
git status --short → "M scripts/sprint_invariants.sh"+ Checkpoint.md + ?? SPRINT_INFRA_SANITIZER_*.md (esperado)
```

## Lições aprendidas

1. **Write-through de Checkpoint.md deve ser FEITO APÓS operações destrutivas em massa.** O lote 4 reverteu o Checkpoint que já tinha edit do write-through inicial; teve que re-aplicar.
2. **Auto-proteção é essencial em scripts de invariante.** Se o próprio script de defesa pode ser sanitizado, a defesa vira no-op silenciosa. Solução: o check valida que seu próprio source tem os glifos esperados.
3. **Cobertura por arquivo importa.** O invariante #14 cobria `cli.py + design_tokens.py + output.py` mas deixava `banner.py + repl_app.py + design_tokens_extended.py` desprotegidos — exatamente onde o sanitizer atacou primeiro.

## Anti-débito derivado

- **INFRA-SANITIZER-PROJECT-HOOK-01** (opcional, BAIXA): adicionar pre-commit local no projeto que recusa diff staged com remoção de Unicode Geometric Shapes (U+25A0-U+25FF). Bloqueado por `core.hookspath` apontando para `~/.config/git/hooks/` (config global, settings.json deny edição). Solução possível: documentar em README + criar `scripts/check_glyphs_pre_commit.sh` invocável manualmente.

---

*"Defesa em camadas: cada camada também precisa de defensor." -- INFRA-SANITIZER-FIX-04*
