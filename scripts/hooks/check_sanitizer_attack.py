#!/usr/bin/env python3
"""Bloqueia commits cuja diff staged apenas remove glifos U+25xx em arquivos
protegidos pelo invariante #14 do sprint_invariants.sh.

Heuristica conservadora: so dispara se TODAS as mudancas em algum dos 7
arquivos protegidos forem APENAS remoção de glifos canônicos. Diffs com
adição de código, alteração de string, ou mudança lógica passam livres.

Exit codes:
  0  - diff é legítimo (passa)
  1  - diff parece ataque do sanitizer (bloqueia)
  2  - erro inesperado (passa por segurança, log warning)

INFRA-SANITIZER-WORKING-TREE-GUARD-01 (2026-05-22).
"""

import subprocess
import sys

PROTECTED = {
    "nyx/cli.py",
    "nyx/agent/repl_app.py",
    "nyx/agent/banner.py",
    "nyx/agent/output.py",
    "nyx/themes/design_tokens.py",
    "nyx/themes/design_tokens_extended.py",
    "scripts/sprint_invariants.sh",
}

# Glifos canônicos via chr() para evitar neutralização por sanitizer hostil
# (mesmo padrão usado em scripts/sprint_invariants.sh check #14).
CANONICAL_GLYPHS = {
    chr(0x25CB),  # círculo vazio
    chr(0x25D0),  # círculo metade
    chr(0x25CF),  # círculo cheio
    chr(0x25C6),  # diamante
}


def staged_files() -> list[str]:
    """Lista arquivos staged (added/modified)."""
    out = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        capture_output=True,
        text=True,
        check=False,
    )
    return [f.strip() for f in out.stdout.splitlines() if f.strip()]


def diff_of(path: str) -> str:
    """Diff staged unificado do path."""
    out = subprocess.run(
        ["git", "diff", "--cached", "--", path],
        capture_output=True,
        text=True,
        check=False,
    )
    return out.stdout


def _strip_glyphs(text: str) -> str:
    """Remove todos os glifos canônicos U+25xx do texto."""
    for g in CANONICAL_GLYPHS:
        text = text.replace(g, "")
    return text


def is_sanitizer_attack(path: str) -> tuple[bool, str]:
    """True se diff staged do path parece ataque puro do sanitizer.

    Padrão do ataque real: cada par -linha/+linha tem a forma
        - "ok": "<glifo>",
        + "ok": "",
    onde a linha "+" é idêntica à linha "-" APÓS remover todos os glifos
    canônicos U+25xx. Não há modificação lógica, apenas neutralização
    visual.

    Critérios para considerar ataque:
      1. Pelo menos 1 glifo canônico foi removido no diff.
      2. TODAS as linhas modificadas seguem o padrão "linha+ = linha- sem glifo".
      3. Nenhuma linha adicionada ou removida foge desse padrão
         (e.g. adição de função nova, mudança de string sem glifo).
    """
    diff = diff_of(path)
    if not diff:
        return False, ""

    # Coleta linhas + e - em pares posicionais (hunk-by-hunk)
    minus_lines: list[str] = []
    plus_lines: list[str] = []
    for line in diff.splitlines():
        if line.startswith(("+++", "---", "@@", "diff ", "index ")):
            continue
        if line.startswith("-"):
            minus_lines.append(line[1:])
        elif line.startswith("+"):
            plus_lines.append(line[1:])

    if not minus_lines and not plus_lines:
        return False, ""

    # Se quantidades não batem, o ataque não é pura substituição 1:1
    if len(minus_lines) != len(plus_lines):
        return False, ""

    removed_glyphs = 0
    for minus, plus in zip(minus_lines, plus_lines):
        glyphs_in_minus = sum(minus.count(g) for g in CANONICAL_GLYPHS)
        # A linha "+" tem que ser EXATAMENTE a linha "-" com glifos removidos
        if _strip_glyphs(minus) != plus:
            return False, ""
        # Se não houve remoção de glifo nesta linha, é modificação normal
        if glyphs_in_minus == 0:
            return False, ""
        removed_glyphs += glyphs_in_minus

    if removed_glyphs == 0:
        return False, ""

    return True, f"removeu {removed_glyphs} glifo(s) U+25xx via substituição puramente visual"


def main() -> int:
    try:
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
        print("Os arquivos acima fazem parte do invariante #14 (defesa", file=sys.stderr)
        print("anti-sanitizer). O diff apenas remove glifos canônicos U+25xx.", file=sys.stderr)
        print("Se a remoção é intencional, use `git commit --no-verify`.", file=sys.stderr)
        print("Caso contrário, restaure com:", file=sys.stderr)
        print("  git checkout HEAD -- <arquivo>", file=sys.stderr)
        return 1

    except Exception as exc:  # pragma: no cover
        print(f"[WARN] check_sanitizer_attack falhou: {exc}", file=sys.stderr)
        print("[WARN] Permitindo commit por segurança (fail-open).", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
