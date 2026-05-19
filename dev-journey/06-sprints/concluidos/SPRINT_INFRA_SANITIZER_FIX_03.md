# SPRINT INFRA-SANITIZER-FIX-03 — restaurar glifos canônicos em cli.py e output.py

## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-FIX-03
  title: "Restaurar glifos U+25CB U+25D0 U+25CF em nyx/cli.py e nyx/agent/output.py"
  onda: 24
  bloco: 24.4 Higiene de orquestração
  prioridade: ALTA
  tipo: Bugfix
  dependencias: [INFRA-SANITIZER-FIX-01, INFRA-SANITIZER-FIX-02]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/cli.py
      reason: "Restaurar glifos cold/warming/warm + sessão (UX-BUG-02B + UX-LAYOUT-01)"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/nyx/agent/output.py
      reason: "Restaurar glifo de build_warming_label (UX-LOOP-VISIBILITY-01)"
  creates: []
  removes: []

  forbidden:
    - "Afrouxar invariante 14 (checagem de codepoint em scripts/sprint_invariants.sh)"
    - "Substituir glifos por emoji ou texto"

  tests:
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 60
      deve_passar: "14/14"
    - cmd: "./run.sh --smoke"
      timeout: 30
      deve_passar: "boot ok"

  acceptance_criteria:
    - "nyx/cli.py contém ≥1 ocorrência de cada: U+25CB (○), U+25D0 (◐), U+25CF (●)"
    - "nyx/agent/output.py contém ≥1 ocorrência de U+25D0 (◐) em build_warming_label"
    - "Invariante 14 passa"
    - "Smoke ok"
```

---

# Sprint INFRA-SANITIZER-FIX-03

**Status:** CONCLUIDA
**Data conclusão:** 2026-05-19
**Data criação:** 2026-05-19
**Modelo obrigatório:** claude-opus-4-7
**Origem:** achado colateral durante execução de HELP-COVERAGE-FIX-02

---

## Contexto

Durante pós-validação de HELP-COVERAGE-FIX-02, `bash scripts/sprint_invariants.sh` reportou FAIL no check #14:

```
[FAIL] 14. glifos canônicos preservados (anti-sanitizer)
       nyx/cli.py: codepoints insuficientes (cb=0, d0=0, cf=0)
       nyx/agent/output.py: build_warming_label sem glifo ◐ (d0=0)
```

Investigação `git log -S` mostrou que os glifos foram **removidos** em algum commit anterior — não regressão de HELP-COVERAGE-FIX-02 (que tocou apenas `nyx/agent/commands/aesthetic.py`). Estado em HEAD antes desta sprint já apresentava `cb=0 d0=0 cf=0` em `nyx/cli.py`.

O check #14 foi criado por INFRA-SANITIZER-FIX-01 e endurecido por -02 (count de codepoint via Python ao invés de grep). Algum sanitizer (provavelmente `guardian.py` ou hook PreToolUse) silenciosamente removeu os caracteres em um commit recente sem disparar o check porque o invariante não foi rodado entre o commit-ofensor e os commits subsequentes.

---

## Estado atual (evidência)

```
$ python3 -c "from pathlib import Path; t=Path('nyx/cli.py').read_text(); \
    print(f'cb={t.count(chr(0x25CB))} d0={t.count(chr(0x25D0))} cf={t.count(chr(0x25CF))}')"
cb=0 d0=0 cf=0

$ python3 -c "from pathlib import Path; t=Path('nyx/agent/output.py').read_text(); \
    print(f'd0={t.count(chr(0x25D0))}')"
d0=0
```

Commit `5145cbb feat(TUI-REDESIGN-25-14): /quit com card de stats em grid` removeu várias linhas com glifos. Pode ter sido refactor que esqueceu de preservar.

---

## Solução proposta

1. `git show 5145cbb~1:nyx/cli.py` para recuperar contexto das linhas removidas com glifos.
2. Reintroduzir nas posições semanticamente corretas:
   - `_STATE_GLYPHS = {"cold": "○", "warming": "◐", "warm": "●"}` perto da definição da toolbar.
   - `"  |  ◐ executando (Ctrl+C cancela)"` no fragmento da toolbar reativa.
   - `output("ok", "● sessão limpa")` e variantes em handlers de slash command.
3. Em `nyx/agent/output.py`, restaurar `◐` em `build_warming_label`.

---

## Critério binário de aceite

- [ ] `nyx/cli.py` contém ≥1 ocorrência de cada glifo (○, ◐, ●)
- [ ] `nyx/agent/output.py` contém ≥1 ocorrência de ◐
- [ ] `bash scripts/sprint_invariants.sh` reporta 14/14
- [ ] `./run.sh --smoke` retorna `boot ok`
- [ ] Sprint movida `producao/` → `concluidos/`
- [ ] Commit `fix(INFRA-SANITIZER-FIX-03): restaura glifos canonicos em cli.py + output.py`

---

*"Sanitizer silencioso é o pior tipo de sanitizer." — INFRA-SANITIZER-FIX-03*
