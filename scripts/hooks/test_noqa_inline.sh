#!/usr/bin/env bash
# Teste end-to-end da heuristica noqa inline do scripts/hooks/pre-commit.
# INFRA-PRE-COMMIT-HOOK-NOQA-INLINE-01 (2026-05-22).
#
# Cobertura:
#   1) Linha com `<!-- noqa-acento -->` contendo "validacao" -> exit 0 (passa) # noqa-acento
#   2) Linha sem noqa contendo "validacao" -> exit 1 (bloqueia FAIL Acentuacao) # noqa-acento
#   3) Linha ASCII puro sem violacao -> exit 0 silencioso # noqa-acento
#
# Estrategia: criar repo git temp com hook instalado em .git/hooks/pre-commit,
# stagear arquivos sinteticos, invocar git commit --dry-run via o hook
# diretamente (sem precisar de modelo, configs, etc).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
HOOK_SRC="$PROJECT_ROOT/scripts/hooks/pre-commit"

if [ ! -f "$HOOK_SRC" ]; then
    echo "[FAIL] hook nao encontrado em $HOOK_SRC" # noqa-acento
    exit 1
fi

PASS_COUNT=0
FAIL_COUNT=0
TMPDIR=$(mktemp -d -t noqa_inline.XXXXXX)
trap "rm -rf $TMPDIR" EXIT

# Setup repo git temp
cd "$TMPDIR"
git init -q
git config user.email "test@example.com"
git config user.name "test"
mkdir -p .git/hooks
cp "$HOOK_SRC" .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

_assert_exit() {
    local label="$1"
    local expected="$2"
    local actual="$3"
    if [ "$expected" = "$actual" ]; then
        echo "  [PASS] $label (exit=$actual)"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo "  [FAIL] $label (esperado exit=$expected, real exit=$actual)"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

_run_hook_isolated() {
    # Roda o hook num subrepo temp dedicado por cenario, com o arquivo
    # stageado em uma copia limpa. Captura exit code sem matar este script.
    local file="$1"
    local marker_file="$2"
    rm -rf "$TMPDIR/subrepo"
    mkdir -p "$TMPDIR/subrepo/scripts/hooks"
    cd "$TMPDIR/subrepo"
    git init -q
    git config user.email "test@example.com"
    git config user.name "test"
    # Copia o sanitizer attack checker (dependencia do hook).
    if [ -f "$PROJECT_ROOT/scripts/hooks/check_sanitizer_attack.py" ]; then
        cp "$PROJECT_ROOT/scripts/hooks/check_sanitizer_attack.py" scripts/hooks/check_sanitizer_attack.py
    fi
    # Copia o update_docs.py stub para evitar quebra na fase 7 do hook.
    # Se nao existir, criamos um stub trivial que retorna 0 em --check. # noqa-acento
    if [ -f "$PROJECT_ROOT/scripts/update_docs.py" ]; then
        mkdir -p scripts
        cp "$PROJECT_ROOT/scripts/update_docs.py" scripts/update_docs.py
    else
        mkdir -p scripts
        cat > scripts/update_docs.py <<'PYEOF'
import sys
sys.exit(0)
PYEOF
    fi
    cp "$marker_file" "$file"
    git add "$file"
    # Roda o hook diretamente (sem rodar git commit, que dispararia outras
    # validacoes/hooks globais alheios a este teste). # noqa-acento
    set +e
    bash "$HOOK_SRC" >/dev/null 2>&1
    local rc=$?
    set -e
    cd "$TMPDIR"
    echo "$rc"
}

echo ""
echo "  test_noqa_inline.sh -- 3 cenarios"
echo "  =================================="
echo ""

# Cenario 1: linha com noqa-acento NAO bloqueia
cat > "$TMPDIR/file1.md" <<'EOF'
# Cenario 1
Texto com validacao do hook <!-- noqa-acento -->
EOF
RC1=$(_run_hook_isolated "file1.md" "$TMPDIR/file1.md")
_assert_exit "Cenario 1 (noqa-acento -> passa)" "0" "$RC1"

# Cenario 2: linha sem noqa BLOQUEIA
# Palavra de teste construida em runtime via printf %s para que o
# validar-acentuacao.py do projeto não detecte literal no source deste
# script — apenas o hook quando o file2.md fica staged no subrepo temp.
_FNAC="valida""cao"  # noqa-acento
{
    printf '# Cenario 2\n'
    printf 'Texto com %s sem marcador\n' "$_FNAC"
} > "$TMPDIR/file2.md"
RC2=$(_run_hook_isolated "file2.md" "$TMPDIR/file2.md")
_assert_exit "Cenario 2 (sem noqa -> bloqueia)" "1" "$RC2"

# Cenario 3: linha ASCII puro sem violacao PASS silencioso
cat > "$TMPDIR/file3.md" <<'EOF'
# Cenario 3
Texto sem nada de errado.
EOF
RC3=$(_run_hook_isolated "file3.md" "$TMPDIR/file3.md")
_assert_exit "Cenario 3 (ASCII limpo -> passa)" "0" "$RC3"

echo ""
echo "  -- Resumo --"
echo "  PASS: $PASS_COUNT"
echo "  FAIL: $FAIL_COUNT"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi
exit 0
