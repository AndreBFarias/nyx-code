#!/usr/bin/env bash
# Sprint Invariants -- proof-of-work de cada sprint da Onda 22+.
#
# Roda 13 checks que detectam as gambiarras mais comuns. Exit 0 = todos
# invariantes preservados. Exit != 0 = sprint NÃO pode ser marcada concluída.
# Check #13 (./run.sh --smoke) foi adicionado em 2026-04-19 via BOOT-FIX-01.
#
# Uso:
#   bash scripts/sprint_invariants.sh          # modo humano
#   bash scripts/sprint_invariants.sh --ci     # exit 1 no primeiro fail
#
# Este script é propositalmente binário e verboso: cada linha impressa
# é uma prova objetiva. IA que pular cola trecho, não o script inteiro.

set -u

CI_MODE=0
[[ "${1:-}" == "--ci" ]] && CI_MODE=1

PASS=0
FAIL=0
FAILED_CHECKS=()

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 2

ok() { printf "[OK] %s\n" "$1"; PASS=$((PASS+1)); }
fail() {
    printf "[FAIL] %s\n" "$1"
    if [ -n "${2:-}" ]; then
        printf "       %s\n" "$2"
    fi
    FAIL=$((FAIL+1))
    FAILED_CHECKS+=("$1")
    if [ $CI_MODE -eq 1 ]; then exit 1; fi
}

section() { printf "\n-- %s --\n" "$1"; }

section "Invariantes do código (nyx/)"

# 1. Zero emoji em Python (ranges Unicode emoji comuns)
# Emoji ranges: U+1F300-U+1FAFF (grande), U+2600-U+27BF (misc), U+1F000-U+1F9FF.
# Exceções: Box drawing U+2500-U+257F e Braille U+2800-U+28FF NÃO são emoji.
# A regex abaixo pega as faixas emoji típicas.
if python3 - <<'PY' 2>&1 | grep -q '^FOUND'; then
import re
import sys
from pathlib import Path

EMOJI_RE = re.compile(
    r'[\U0001F300-\U0001FAFF\U0001F000-\U0001F2FF\U0001F680-\U0001F6FF]|'  # pictographs
    r'[\u2600-\u27BF]'  # misc symbols + dingbats (inclui ⚡ U+26A1)
)
root = Path("nyx")
found = []
for p in root.rglob("*.py"):
    text = p.read_text(encoding="utf-8", errors="ignore")
    for m in EMOJI_RE.finditer(text):
        line = text.count("\n", 0, m.start()) + 1
        found.append(f"{p}:{line}:{m.group()}")
if found:
    print("FOUND")
    for f in found[:10]:
        print(f"  {f}")
    sys.exit(1)
PY
    fail "1. emoji em .py (ADR-004)" "rodar: python3 -c 'ver detalhes acima'"
else
    ok "1. zero emoji em nyx/**/*.py"
fi

# 2. Zero menção literal a IAs comerciais em .py (exceto env vars e strings técnicas documentadas)
BAD_MENTIONS=$(grep -rn -E '(Claude|Anthropic|GPT-|Gemini|Copilot)' nyx/ --include='*.py' 2>/dev/null |
               grep -v 'OPENAI_\|ANTHROPIC_API_KEY\|# noqa: ai-mention' || true)
if [ -n "$BAD_MENTIONS" ]; then
    fail "2. menção a IA em .py (ADR-005)" "${BAD_MENTIONS}"
else
    ok "2. zero menção a Claude/Anthropic/GPT/Gemini/Copilot em .py"
fi

# 3. Zero print() fora de nyx/cli.py e nyx/agent/output.py (ADR-024 autoriza só esses 2)
BAD_PRINT=$(grep -rn '^\s*print(' nyx/ --include='*.py' 2>/dev/null |
            grep -v 'nyx/cli.py\|nyx/agent/output.py' || true)
if [ -n "$BAD_PRINT" ]; then
    fail "3. print() fora de cli.py/output.py (ADR-024)" "${BAD_PRINT}"
else
    ok "3. print() só em cli.py e output.py"
fi

# 4. Zero 'except: pass' ou 'except Exception: pass' sem logger
BAD_EXCEPT=$(python3 - <<'PY' 2>&1
import ast
from pathlib import Path
violations = []
for p in Path("nyx").rglob("*.py"):
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            stmts = node.body
            # padrão: só Pass ou só Return com valor simples
            if len(stmts) == 1 and isinstance(stmts[0], (ast.Pass,)):
                violations.append(f"{p}:{node.lineno}:except pass (sem log)")
for v in violations:
    print(v)
PY
)
if [ -n "$BAD_EXCEPT" ]; then
    fail "4. except silencioso sem log" "${BAD_EXCEPT}"
else
    ok "4. zero except silencioso"
fi

# 5. Zero literais de porta 11435 / 11436 fora de config/defaults.py
BAD_PORTS=$(grep -rn -E '\b(11435|11436)\b' nyx/ --include='*.py' 2>/dev/null |
            grep -v 'nyx/config/defaults.py' || true)
if [ -n "$BAD_PORTS" ]; then
    fail "5. porta hardcoded (AUDIT-FIX-03)" "${BAD_PORTS}"
else
    ok "5. portas só em config/defaults.py"
fi

# 6. Zero hex de cor (#RRGGBB) em Python fora das fontes declaradas
BAD_HEX=$(grep -rn -E '#[0-9A-Fa-f]{6}' nyx/ --include='*.py' 2>/dev/null |
          grep -v 'nyx/themes/design_tokens.py\|nyx/themes/constants.py' || true)
# Nota: este check vira ATIVO após UX-DESIGN-01. Antes dessa sprint, esperar violações.
if [ -n "$BAD_HEX" ]; then
    if [ -f nyx/themes/design_tokens.py ]; then
        fail "6. hex hardcoded fora de design_tokens.py (UX-DESIGN-01)" "${BAD_HEX}"
    else
        ok "6. hex hardcoded presente, mas design_tokens.py ainda não existe (esperado pré UX-DESIGN-01)"
    fi
else
    ok "6. zero hex hardcoded fora de design_tokens.py"
fi

# 7. Zero arquivo .py > 800 linhas
BAD_SIZE=$(find nyx -name '*.py' -not -path '*/__pycache__/*' -exec wc -l {} + 2>/dev/null |
           awk '$1 > 800 && $2 != "total" { print }' || true)
if [ -n "$BAD_SIZE" ]; then
    fail "7. arquivo > 800 linhas (CLAUDE.md limite)" "${BAD_SIZE}"
else
    ok "7. nenhum .py > 800 linhas"
fi

# 8. Zero TODO / FIXME inline em código Python
BAD_TODO=$(grep -rn -E '#\s*(TODO|FIXME|XXX|HACK)\b' nyx/ --include='*.py' 2>/dev/null |
           grep -v '# noqa: TODO-ok' || true)
if [ -n "$BAD_TODO" ]; then
    fail "8. TODO/FIXME/XXX/HACK inline (CLAUDE.md anti-burla)" "${BAD_TODO}"
else
    ok "8. zero TODO/FIXME/XXX/HACK"
fi

# 9. Zero path absoluto hardcoded (/home/, /tmp/, /usr/, C:\) em código Python
BAD_PATHS=$(grep -rn -E "['\"](/home/|/tmp/|/usr/|C:\\\\)" nyx/ --include='*.py' 2>/dev/null |
            grep -v '__pycache__\|# noqa: abs-path' || true)
if [ -n "$BAD_PATHS" ]; then
    fail "9. path absoluto hardcoded" "${BAD_PATHS}"
else
    ok "9. zero path absoluto hardcoded"
fi

# 10. Ruff limpo em nyx/
if command -v python3 >/dev/null && python3 -m ruff --version >/dev/null 2>&1; then
    if python3 -m ruff check nyx/ >/dev/null 2>&1; then
        ok "10. ruff check nyx/"
    else
        RUFF_OUT=$(python3 -m ruff check nyx/ 2>&1 | tail -5)
        fail "10. ruff reclama" "${RUFF_OUT}"
    fi
else
    ok "10. ruff ausente (pulado)"
fi

# 11. Zero menção a 'os.environ.get("SKIP_' (flags de bypass sorrateiros)
BAD_SKIP=$(grep -rn -E 'os\.(environ|getenv).*SKIP_' nyx/ --include='*.py' 2>/dev/null || true)
if [ -n "$BAD_SKIP" ]; then
    fail "11. flag de skip suspeita" "${BAD_SKIP}"
else
    ok "11. zero flag SKIP_* em código"
fi

# 12. git status: sem arquivos de teste esquecidos no root
STRAY=$(ls -1 2>/dev/null | grep -E '^(test_|scratch_|debug_|temp_).*\.(py|md|txt|log)$' || true)
if [ -n "$STRAY" ]; then
    fail "12. arquivos de debug/teste no root" "${STRAY}"
else
    ok "12. root sem arquivos de teste/scratch esquecidos"
fi

# 13. ./run.sh --smoke retorna 0 e imprime exatamente 'boot ok' (boot integrity, BOOT-FIX-01)
SMOKE_OUT=$(timeout 5 ./run.sh --smoke 2>&1)
SMOKE_RC=$?
if [ $SMOKE_RC -eq 0 ] && echo "$SMOKE_OUT" | grep -qx "boot ok"; then
    ok "13. ./run.sh --smoke (boot integrity)"
else
    SMOKE_HEAD=$(echo "$SMOKE_OUT" | head -3 | tr '\n' '|')
    fail "13. ./run.sh --smoke (boot integrity)" "exit=${SMOKE_RC}, stdout=${SMOKE_HEAD}"
fi

section "Resumo"
printf "PASS: %d\n" "$PASS"
printf "FAIL: %d\n" "$FAIL"
if [ $FAIL -eq 0 ]; then
    printf "\nSprint invariantes OK.\n"
    exit 0
else
    printf "\nSprint NÃO pode ser marcada concluída. Checks falhos:\n"
    for c in "${FAILED_CHECKS[@]}"; do printf "  - %s\n" "$c"; done
    exit 1
fi

# "O que não se mede, não se pode garantir." -- W. Edwards Deming
