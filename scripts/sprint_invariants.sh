#!/usr/bin/env bash
# Sprint Invariants -- proof-of-work de cada sprint da Onda 22+.
#
# Roda 14 checks que detectam as gambiarras mais comuns. Exit 0 = todos
# invariantes preservados. Exit != 0 = sprint NÃO pode ser marcada concluída.
# Check #13 (./run.sh --smoke) foi adicionado em 2026-04-19 via BOOT-FIX-01.
# Check #14 (glifos canônicos) foi adicionado em 2026-05-17 via INFRA-SANITIZER-FIX-01.
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
    r'[\u2600-\u27BF]'  # misc symbols + dingbats (inclui  U+26A1)
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
BAD_MENTIONS=$(grep -rn -E '(Claude|Anthropic|GPT-|Gemini|Copilot)' nyx/ --include='*.py' 2>/dev/null |  # noqa-anonimato
               grep -v 'OPENAI_\|ANTHROPIC_API_KEY\|# noqa: ai-mention' || true)
if [ -n "$BAD_MENTIONS" ]; then
    fail "2. menção a IA em .py (ADR-005)" "${BAD_MENTIONS}"
else
    ok "2. zero menção a IA proprietária em .py"   # noqa-anonimato
fi

# 3. Zero print() fora de nyx/cli*.py e nyx/agent/output.py (ADR-024 + INFRA-CLI-SPLIT-02).
# nyx/cli.py, nyx/cli_helpers.py, nyx/cli_keybindings.py, nyx/cli_handlers.py compõem
# o subsistema CLI (mesma camada de orquestração de REPL). output.py é render layer.
BAD_PRINT=$(grep -rn '^\s*print(' nyx/ --include='*.py' 2>/dev/null |
            grep -v 'nyx/cli\(_[a-z]*\)\?\.py\|nyx/agent/output.py' || true)
if [ -n "$BAD_PRINT" ]; then
    fail "3. print() fora de cli*.py/output.py (ADR-024)" "${BAD_PRINT}"
else
    ok "3. print() só em cli*.py e output.py"
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
# design_tokens_extended.py adicionado em VISUAL-LAYOUT-01 (Onda 24): porta
# 5 aesthetics + 7 entities de novo_layout/src/themes.js. Mesma natureza
# de fonte unica de tokens visuais que design_tokens.py.
BAD_HEX=$(grep -rn -E '#[0-9A-Fa-f]{6}' nyx/ --include='*.py' 2>/dev/null |
          grep -v -E 'nyx/themes/design_tokens(_extended)?\.py|nyx/themes/constants\.py' || true)
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

# 7. (removido 2026-04-21) Limite de 800 linhas descontinuado.
#     Split agora é decisão de coesão, não de contagem. Preservado como
#     no-op para manter numeração estável dos checks em relatórios antigos.
ok "7. limite de 800 linhas removido (split por coesão)"

# 8. Zero TODO / FIXME inline em código Python
BAD_TODO=$(grep -rn -E '#\s*(TODO|FIXME|XXX|HACK)\b' nyx/ --include='*.py' 2>/dev/null |
           grep -v '# noqa: TODO-ok' || true)
if [ -n "$BAD_TODO" ]; then
    fail "8. TODO/FIXME/XXX/HACK inline (GUIDE.md anti-burla)" "${BAD_TODO}"
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

# 14. Glifos canônicos preservados (defesa anti-sanitizer, INFRA-SANITIZER-FIX-01/02/05)
#     Geometric Shapes U+25CB (○), U+25D0 (◐), U+25CF (●) são Unicode genéricos
#     permitidos pelo ADR-004 (NÃO são emoji). Carga útil de UX-BUG-02B + UX-LAYOUT-01
#     + UX-LOOP-VISIBILITY-01.
#
#     Tabela canônica (mantida em comentário para auto-proteção redundante;
#     INFRA-SANITIZER-FIX-05 substituiu as comparações operacionais por chr(),
#     então estes literais aqui são o segundo escudo do invariante):
#       ○  = U+25CB White Circle      (cold/empty)
#       ◐  = U+25D0 Circle Half Black (warming)
#       ●  = U+25CF Black Circle      (warm/ok)
#       ◆  = U+25C6 Black Diamond     (themes extended)
#       ○ ○ ◐ ◐ ● ● = redundância anti-sanitizer (>=3 cada conforme check abaixo)
#     Ocorrências literais nesta seção garantem >= 3 por glifo para o check de
#     auto-proteção abaixo, sem reintroduzir vulnerabilidade nas comparações.
#
#     Checagem via Python por contagem de codepoint (imune a strip textual).
#     INFRA-SANITIZER-FIX-02: substitui grep -F literal por count() de codepoints,
#     porque sanitizer pode remover só os bytes UTF-8 deixando aspas vazias
#     que ainda passam pelo grep textual mas perdem os caracteres.
#     INFRA-SANITIZER-FIX-05: codepoints construídos via chr(0xNNNN) em vez de
#     literais Unicode. Sanitizer hostil que remova literais em massa também
#     comeria as comparações da defesa (count(\"\") retorna len+1, sempre passa
#     falsamente). chr() resiste porque só AST-parser de Python o neutralizaria.
GLYPH_FAIL=$(python3 - <<'PY'
from pathlib import Path

# Codepoints canônicos via chr() — resiste a sanitizers que removem literais
# em massa. Qualquer ferramenta hostil teria que parsear AST Python para
# neutralizar, custo proibitivo. Referência: incidente 2026-05-20 23:36.
CB = chr(0x25CB)  # U+25CB White Circle (cold/empty state)
D0 = chr(0x25D0)  # U+25D0 Circle Half Black (warming/in progress)
CF = chr(0x25CF)  # U+25CF Black Circle (warm/ok)
DM = chr(0x25C6)  # U+25C6 Black Diamond (themes extended)

fails = []
cli = Path("nyx/cli.py").read_text(encoding="utf-8")
if cli.count(CB) < 1 or cli.count(D0) < 1 or cli.count(CF) < 1:
    fails.append(
        f"nyx/cli.py: codepoints insuficientes "
        f"(cb={cli.count(CB)}, d0={cli.count(D0)}, cf={cli.count(CF)})"
    )
dt = Path("nyx/themes/design_tokens.py").read_text(encoding="utf-8")
if dt.count(CF) < 4 or dt.count(CB) < 1:
    fails.append(
        f"nyx/themes/design_tokens.py: BULLETS sem glifos "
        f"(cf={dt.count(CF)}, cb={dt.count(CB)})"
    )
out = Path("nyx/agent/output.py").read_text(encoding="utf-8")
if out.count(D0) < 1:
    fails.append(
        f"nyx/agent/output.py: build_warming_label sem glifo {D0} "
        f"(d0={out.count(D0)})"
    )
# INFRA-SANITIZER-FIX-04: cobertura ampliada para arquivos que o sanitizer
# antigo destruiu mas o check #14 não cobria (banner.py, repl_app.py,
# design_tokens_extended.py).
bn = Path("nyx/agent/banner.py").read_text(encoding="utf-8")
if bn.count(CF) < 4:
    fails.append(
        f"nyx/agent/banner.py: glifos {CF} insuficientes "
        f"(cf={bn.count(CF)}, esperado>=4 em _build_compact + _build_wide)"
    )
repl = Path("nyx/agent/repl_app.py").read_text(encoding="utf-8")
if repl.count(CF) < 1:
    fails.append(
        f"nyx/agent/repl_app.py: glifo {CF} insuficiente "
        f"(cf={repl.count(CF)}, esperado>=1)"
    )
dte = Path("nyx/themes/design_tokens_extended.py").read_text(encoding="utf-8")
if dte.count(DM) < 1:
    fails.append(
        f"nyx/themes/design_tokens_extended.py: glifo {DM} insuficiente "
        f"(cf={dte.count(DM)}, esperado>=1)"
    )
# INFRA-SANITIZER-FIX-04: auto-proteção. O próprio sprint_invariants.sh
# precisa preservar os 3 glifos canônicos na definição deste check; sanitizer
# que neutralize o check seria pego aqui.
# INFRA-SANITIZER-FIX-05: agora o script usa chr(0xNNNN) nas comparações,
# então a auto-proteção verifica presença dos literais (○ ◐ ●) que sobrevivem
# apenas em comentários/mensagens — segundo escudo redundante.
inv = Path("scripts/sprint_invariants.sh").read_text(encoding="utf-8")
if inv.count(CB) < 3 or inv.count(D0) < 3 or inv.count(CF) < 3:
    fails.append(
        f"scripts/sprint_invariants.sh: auto-proteção falhou "
        f"(cb={inv.count(CB)}, d0={inv.count(D0)}, cf={inv.count(CF)}, "
        f"esperado>=3 cada para garantir check #14 não-neutralizado)"
    )
# INVARIANT-14-COVERAGE-DOCS-VENDOR-01: o check acima só cobria runtime e passou
# 14/14 com 65 docs + xterm.js estripados (auditoria 2026-05-25). Sub-check de
# regressão para um conjunto-sentinela (docs + vendored): a working tree não pode
# ter MENOS glifos da faixa Geometric Shapes (U+25A0-U+25FF: ○◐●◆◇▶▼ etc.) que o
# HEAD. Strip de glifo = working < HEAD -> FAIL. Custo: 3 `git show` (~150ms).
import subprocess
SENTINELS = [
    "dev-journey/05-guides/MICROCOPY.md",
    "nyx/cockpit/static/vendor/xterm.js",
    "dev-journey/03-decisions/ADR_027_PROGRESSAO_IDENTIDADE.md",
]
def _geo_count(text: str) -> int:
    # Conta codepoints da faixa Geometric Shapes (allowlist canônica). Range em
    # vez de literais: imune a sanitizer e cobre toda a allowlist de uma vez.
    return sum(1 for ch in text if 0x25A0 <= ord(ch) <= 0x25FF)
for _rel in SENTINELS:
    _p = Path(_rel)
    if not _p.exists():
        continue
    _work = _geo_count(_p.read_text(encoding="utf-8"))
    try:
        _head_txt = subprocess.run(
            ["git", "show", f"HEAD:{_rel}"],
            capture_output=True, text=True, timeout=5,
        ).stdout
    except Exception:  # noqa: BLE001 -- sem HEAD/arquivo novo: pula sentinela
        continue
    _head = _geo_count(_head_txt)
    if _work < _head:
        fails.append(
            f"{_rel}: glifos Geometric Shapes removidos "
            f"(working={_work} < HEAD={_head}) -- possível dano de sanitizer"
        )
print("; ".join(fails))
PY
)
if [ -n "$GLYPH_FAIL" ]; then
    fail "14. glifos canônicos preservados (anti-sanitizer)" "${GLYPH_FAIL}"
else
    ok "14. glifos canônicos preservados (UX-BUG-02B + UX-LAYOUT-01 + UX-LOOP-VISIBILITY-01)"
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
