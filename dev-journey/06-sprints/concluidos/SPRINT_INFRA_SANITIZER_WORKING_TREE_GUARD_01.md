## 0. SPEC (machine-readable)

```yaml
sprint:
  id: INFRA-SANITIZER-WORKING-TREE-GUARD-01
  title: "Pre-commit local detecta diff que só remove U+25xx e bloqueia commit (defense-in-depth)"
  onda: 29
  prioridade: CRÍTICA
  tipo: Infra
  dependencias: [INFRA-SANITIZER-VECTOR-AUDIT-01, INFRA-SANITIZER-RECIDIVA-07]
  desbloqueia: []

  touches:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/pre-commit
      reason: "Hook local do projeto — adicionar bloco de detecção de sanitizer attack"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/check_sanitizer_attack.py
      reason: "Script Python dedicado para o check (testável isoladamente)"

  creates:
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/check_sanitizer_attack.py
      reason: "Detecta diff staged que apenas remove glifos U+25xx em arquivos protegidos pelo invariante #14"
    - path: /home/andrefarias/Desenvolvimento/Nyx-Code/scripts/hooks/test_check_sanitizer_attack.sh
      reason: "Testes ad-hoc do check (3 cenários: ataque puro, ataque parcial, mudança legítima)"

  forbidden:
    - "Modificar ~/.config/git/hooks/ (hook global do usuário — fora de escopo, requer autorização explícita)"
    - "Adicionar emoji"
    - "Quebrar invariante #14 ou smoke"
    - "Bloquear commits legítimos que tenham acidentalmente removido glifos (heurística deve ser CONSERVADORA — só bloqueia se diff é EXCLUSIVAMENTE remoção)"

  tests:
    - cmd: "bash scripts/hooks/test_check_sanitizer_attack.sh"
      timeout: 30
      deve_passar: true
    - cmd: "bash scripts/sprint_invariants.sh"
      timeout: 30
      deve_passar: true
    - cmd: "./run.sh --smoke"
      timeout: 60
      deve_passar: true

  acceptance_criteria:
    - "scripts/hooks/check_sanitizer_attack.py existe e é executável"
    - "Cenário 1 (ataque puro: remove U+25xx em 1+ arquivo protegido sem outras mudanças) → exit 1 + msg explícita"
    - "Cenário 2 (mudança legítima: edita lógica + adiciona/remove glifos como parte): exit 0"
    - "Cenário 3 (diff não toca arquivos protegidos): exit 0 silencioso"
    - "Pre-commit local invoca o check antes dos demais; se atacar, bloqueia commit"
    - "Smoke + invariantes 14/14 PASS"
```

---

# Sprint INFRA-SANITIZER-WORKING-TREE-GUARD-01 — Guarda final

**Status:** PENDENTE
**Data criação:** 2026-05-22
**Modelo obrigatório:** claude-opus-4-7 (sem subagentes)

---

## Contexto

> 3 recidivas do sanitizer em ~12h (2026-05-21 ~12h, 2026-05-21 ~17h, 2026-05-22 ~00h30). VECTOR-AUDIT-01 absolveu o sanitizer atual, mas o vetor real continua ativo e inrastreável sem HISTFILE persistente.
> Defense-in-depth: mesmo sem rastrear o vetor, o working tree NÃO PODE ser publicado corrompido. Esta sprint adiciona a última linha de defesa: pre-commit guard que detecta diff "só remove U+25xx" e bloqueia commit.

---

## Problema

O invariante #14 do `sprint_invariants.sh` DETECTA corrupção (PASS 13/14 quando atacado), mas o `git commit` não é gateado por isso automaticamente. Se o supervisor não rodar `bash scripts/sprint_invariants.sh` antes de commitar, pode publicar working tree corrompido para origin/main.

Os 3 ataques deste fim de semana foram detectados ANTES do commit porque sprints tocavam os arquivos atacados, mas em sessões futuras que NÃO toquem esses paths, a corrupção pode passar despercebida.

---

## Solução proposta

### Script Python dedicado

`scripts/hooks/check_sanitizer_attack.py`:

```python
#!/usr/bin/env python3
"""Bloqueia commits cuja diff staged apenas remove glifos U+25xx em arquivos
protegidos pelo invariante #14 do sprint_invariants.sh.

Heurística conservadora: só dispara se TODAS as mudanças em algum dos 7
arquivos protegidos forem APENAS remoção de glifos canônicos. Diffs com
adição de código, alteração de string, ou mudança lógica passam livres.

Exit codes:
  0  — diff é legítimo (passa)
  1  — diff parece ataque do sanitizer (bloqueia)
  2  — erro inesperado (passa por segurança, log warning)
"""

import subprocess
import sys
from pathlib import Path

PROTECTED = {
    "nyx/cli.py",
    "nyx/agent/repl_app.py",
    "nyx/agent/banner.py",
    "nyx/agent/output.py",
    "nyx/themes/design_tokens.py",
    "nyx/themes/design_tokens_extended.py",
    "scripts/sprint_invariants.sh",
}

CANONICAL_GLYPHS = {
    chr(0x25CB),  # ○
    chr(0x25D0),  # ◐
    chr(0x25CF),  # ●
    chr(0x25C6),  # ◆
}


def staged_files() -> list[str]:
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True, text=True, check=False,
    )
    return [f.strip() for f in out.stdout.splitlines() if f.strip()]


def diff_of(path: str) -> str:
    out = subprocess.run(
        ["git", "diff", "--cached", "--", path],
        capture_output=True, text=True, check=False,
    )
    return out.stdout


def is_sanitizer_attack(path: str) -> tuple[bool, str]:
    """True se diff staged do path parece ataque puro do sanitizer."""
    diff = diff_of(path)
    if not diff:
        return False, ""

    removed_glyphs = 0
    added_glyphs = 0
    non_glyph_changes = 0

    for line in diff.splitlines():
        if not line.startswith(("+", "-")) or line.startswith(("+++", "---")):
            continue
        body = line[1:]
        glyph_count = sum(body.count(g) for g in CANONICAL_GLYPHS)
        if line.startswith("-"):
            removed_glyphs += glyph_count
            # Verifica se a linha removida tem APENAS glifos + whitespace + ASCII trivial
            stripped = body
            for g in CANONICAL_GLYPHS:
                stripped = stripped.replace(g, "")
            # Se sobrou apenas whitespace + 3 chars trivias, é remoção pura
            if stripped.strip() and len(stripped.strip()) > 10:
                non_glyph_changes += 1
        else:  # "+"
            added_glyphs += glyph_count
            non_glyph_changes += 1

    if removed_glyphs > 0 and added_glyphs == 0 and non_glyph_changes == 0:
        return True, f"removeu {removed_glyphs} glifo(s) U+25xx sem outras mudanças"
    return False, ""


def main() -> int:
    suspicious = []
    for path in staged_files():
        if path not in PROTECTED:
            continue
        attacked, reason = is_sanitizer_attack(path)
        if attacked:
            suspicious.append((path, reason))

    if not suspicious:
        return 0

    print("[BLOQUEIO] Sanitizer attack detectado no diff staged:", file=sys.stderr)
    for path, reason in suspicious:
        print(f"  - {path}: {reason}", file=sys.stderr)
    print(file=sys.stderr)
    print("Os arquivos acima fazem parte do invariante #14 (Defesa", file=sys.stderr)
    print("anti-sanitizer). O diff apenas remove glifos canônicos U+25xx.", file=sys.stderr)
    print("Se é intencional, use --no-verify. Caso contrário:", file=sys.stderr)
    print("  git checkout HEAD -- <arquivo>", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

### Integração no pre-commit local

`scripts/hooks/pre-commit` (modificado — adicionar no topo, antes de outros checks):

```bash
#!/usr/bin/env bash
# ... preâmbulo existente ...

# INFRA-SANITIZER-WORKING-TREE-GUARD-01: bloqueia diffs que só removem U+25xx.
python3 scripts/hooks/check_sanitizer_attack.py || exit 1

# ... resto do pre-commit existente ...
```

### Testes

`scripts/hooks/test_check_sanitizer_attack.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
SCRIPT="scripts/hooks/check_sanitizer_attack.py"
TMPDIR=$(mktemp -d)
trap "rm -rf $TMPDIR" EXIT

# Setup repo temporário
git init -q "$TMPDIR/repo"
cd "$TMPDIR/repo"
mkdir -p nyx/themes
echo "BULLETS = {'ok': chr(0x25CB), 'work': chr(0x25D0), 'done': chr(0x25CF)}" > nyx/themes/design_tokens.py
git add . && git commit -q -m "init"

# Cenário 1: ataque puro (remove só glifos)
sed -i "s/chr(0x25CB)/\"\"/; s/chr(0x25D0)/\"\"/; s/chr(0x25CF)/\"\"/" nyx/themes/design_tokens.py
# Hmm, esse sed muda chr() para "" — não é remoção pura de glifo, é refactor.
# Melhor: simular sanitizer real que faz arquivo virar literal sem glifo.
echo "BULLETS = {'ok': '', 'work': '', 'done': ''}" > nyx/themes/design_tokens.py
git add nyx/themes/design_tokens.py
if python3 "$OLDPWD/$SCRIPT" 2>&1 | grep -q BLOQUEIO; then
    echo "Cenário 1 OK: ataque puro bloqueado"
else
    echo "Cenário 1 FAIL: ataque puro não foi bloqueado"
    exit 1
fi
git reset --hard -q

# Cenário 2: mudança legítima (adiciona código + remove glifo)
cat >> nyx/themes/design_tokens.py << 'PYEOF'

def get_bullets():
    return BULLETS
PYEOF
sed -i "s/chr(0x25CB)/chr(0x25CB)/" nyx/themes/design_tokens.py  # no-op
git add nyx/themes/design_tokens.py
if python3 "$OLDPWD/$SCRIPT"; then
    echo "Cenário 2 OK: mudança legítima passou"
else
    echo "Cenário 2 FAIL: mudança legítima foi bloqueada"
    exit 1
fi
git reset --hard -q

# Cenário 3: diff em arquivo não-protegido (passa silencioso)
echo "qualquer coisa" > /dev/null  # no-op
mkdir -p other && echo "code" > other/file.py
git add other/file.py
if python3 "$OLDPWD/$SCRIPT"; then
    echo "Cenário 3 OK: path não-protegido ignorado"
else
    echo "Cenário 3 FAIL: path não-protegido bloqueou"
    exit 1
fi

echo "TODOS OS TESTES PASSARAM"
```

---

## Diff esperado

```
+ 2 arquivos criados (check + test)
~ 1 arquivo modificado (pre-commit local)
+ ~150 linhas
```

---

## Critério binário de aceite

- [ ] `scripts/hooks/check_sanitizer_attack.py` existe + chmod 755
- [ ] `scripts/hooks/test_check_sanitizer_attack.sh` existe + executa OK
- [ ] Pre-commit local invoca o check no topo (antes de outras validações)
- [ ] Cenário 1 (ataque puro) → exit 1 + msg
- [ ] Cenário 2 (mudança legítima com glifo removido) → exit 0
- [ ] Cenário 3 (path não-protegido) → exit 0 silencioso
- [ ] `bash scripts/sprint_invariants.sh` PASS 14/14
- [ ] `./run.sh --smoke` boot ok
- [ ] Acentuação rc=0

---

## Riscos

| Risco | Mitigação |
|-------|-----------|
| False positive bloqueia trabalho legítimo do usuário | Heurística conservadora: bloqueia APENAS se diff é EXCLUSIVAMENTE remoção (zero adição + zero non-glyph change) |
| User precisa commit urgente com diff que parece ataque | `git commit --no-verify` permite escapar — documentado na msg |
| Hook local não é invocado pelo hook global (`~/.config/git/hooks/pre-commit`) | Verificar em runtime: testar `git commit` e confirmar que o hook local roda |
| Heurística pode escapar ataques mais sofisticados (sanitizer 2.0) | Aceito — defense-in-depth, não barreira definitiva |

---

*"Bloqueio na frente do hub é melhor que rastreio depois do prejuízo." -- princípio defense-in-depth.*
