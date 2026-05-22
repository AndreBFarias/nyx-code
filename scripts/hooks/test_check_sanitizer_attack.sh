#!/usr/bin/env bash
# Testes do check_sanitizer_attack.py em repo temporário isolado.
# 3 cenários obrigatórios:
#   1. Ataque puro (só remoção de U+25xx em arquivo protegido) -> exit 1
#   2. Mudança legítima (adiciona código + remove glifo)       -> exit 0
#   3. Diff em path não-protegido                              -> exit 0
#
# INFRA-SANITIZER-WORKING-TREE-GUARD-01 (2026-05-22).

set -euo pipefail

SCRIPT_REL="scripts/hooks/check_sanitizer_attack.py"
PROJECT_ROOT="$(git rev-parse --show-toplevel)"
SCRIPT_ABS="${PROJECT_ROOT}/${SCRIPT_REL}"

if [ ! -x "${SCRIPT_ABS}" ]; then
    echo "FAIL: ${SCRIPT_ABS} não existe ou não é executável"
    exit 1
fi

TMPDIR="$(mktemp -d)"
trap "rm -rf ${TMPDIR}" EXIT

# Glifos canônicos via chr() (defensivo contra sanitizer hostil)
G_CB="$(python3 -c 'print(chr(0x25CB))')"
G_D0="$(python3 -c 'print(chr(0x25D0))')"
G_CF="$(python3 -c 'print(chr(0x25CF))')"

# Setup repo temporário
git init -q "${TMPDIR}/repo"
cd "${TMPDIR}/repo"
git config user.email "test@local"
git config user.name "test"

mkdir -p nyx/themes nyx/agent other

# design_tokens.py com glifos canônicos no estado inicial
cat > nyx/themes/design_tokens.py <<PYEOF
BULLETS = {
    "ok": "${G_CB}",
    "work": "${G_D0}",
    "done": "${G_CF}",
}
PYEOF

git add . > /dev/null
# --no-verify: pula hook global de identidade (out-of-scope deste teste).
git commit -q --no-verify -m "init"

# ---------------------------------------------------------------------------
# Cenário 1: ATAQUE PURO -- remove os 3 glifos sem outras mudanças
# ---------------------------------------------------------------------------
echo "=== Cenário 1: ataque puro (só remove U+25xx) ==="
cat > nyx/themes/design_tokens.py <<'PYEOF'
BULLETS = {
    "ok": "",
    "work": "",
    "done": "",
}
PYEOF
git add nyx/themes/design_tokens.py

OUT1="$(python3 "${SCRIPT_ABS}" 2>&1 || true)"
EXIT1=$(python3 "${SCRIPT_ABS}" > /dev/null 2>&1; echo $?)

if [ "${EXIT1}" = "1" ] && echo "${OUT1}" | grep -q "BLOQUEIO"; then
    echo "  PASS: ataque puro bloqueado (exit=1, mensagem presente)"
else
    echo "  FAIL: ataque puro não foi bloqueado (exit=${EXIT1})"
    echo "  Output:"
    echo "${OUT1}" | sed 's/^/    /'
    exit 1
fi

git reset --hard -q
git checkout -q -- .

# ---------------------------------------------------------------------------
# Cenário 2: MUDANÇA LEGÍTIMA -- adiciona função nova (e remove um glifo)
# ---------------------------------------------------------------------------
echo "=== Cenário 2: mudança legítima (adiciona código + remove glifo) ==="
cat > nyx/themes/design_tokens.py <<PYEOF
BULLETS = {
    "ok": "${G_CB}",
    "work": "${G_D0}",
}


def get_bullets():
    return BULLETS
PYEOF
git add nyx/themes/design_tokens.py

OUT2="$(python3 "${SCRIPT_ABS}" 2>&1 || true)"
EXIT2=$(python3 "${SCRIPT_ABS}" > /dev/null 2>&1; echo $?)

if [ "${EXIT2}" = "0" ]; then
    echo "  PASS: mudança legítima passou (exit=0)"
else
    echo "  FAIL: mudança legítima foi bloqueada (exit=${EXIT2})"
    echo "  Output:"
    echo "${OUT2}" | sed 's/^/    /'
    exit 1
fi

git reset --hard -q
git checkout -q -- .

# ---------------------------------------------------------------------------
# Cenário 3: DIFF EM PATH NÃO-PROTEGIDO -- passa silencioso
# ---------------------------------------------------------------------------
echo "=== Cenário 3: diff em path não-protegido ==="
echo "qualquer coisa" > other/file.txt
git add other/file.txt

OUT3="$(python3 "${SCRIPT_ABS}" 2>&1 || true)"
EXIT3=$(python3 "${SCRIPT_ABS}" > /dev/null 2>&1; echo $?)

if [ "${EXIT3}" = "0" ] && [ -z "${OUT3}" ]; then
    echo "  PASS: path não-protegido ignorado (exit=0, output vazio)"
elif [ "${EXIT3}" = "0" ]; then
    echo "  PASS: path não-protegido não bloqueou (exit=0)"
else
    echo "  FAIL: path não-protegido foi bloqueado (exit=${EXIT3})"
    echo "  Output:"
    echo "${OUT3}" | sed 's/^/    /'
    exit 1
fi

echo ""
echo "TODOS OS 3 CENÁRIOS PASSARAM"
exit 0
