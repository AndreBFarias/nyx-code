#!/usr/bin/env python3
"""UX-PROGRESSION-01: audit de microcopy em literais Python user-facing.

Varre nyx/**/*.py em busca de strings em literais que casam padrões
proibidos (inglês de UX, placeholders genéricos isolados). Exit 0 se
nada encontrado; 1 se há violação (em modo --check).

Falsos positivos: strings em código não-user-facing (ex.: nomes de tools,
keys JSON) podem aparecer; revisar manualmente.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ["nyx"]

# Padrões claramente em inglês UX (curtos, isolados). Não pegam termos
# técnicos legítimos (tool names, kwargs).
ENGLISH_UX = re.compile(
    r'"\s*(Loading\.\.\.|Saving\.\.\.|Done!|Yay!|Oops!|Click here|Press any key|'
    r'Hello, world|Good ?bye|Bye!)\s*"',
    re.IGNORECASE,
)

# Placeholders genéricos isolados (entre aspas, sozinhos)
PLACEHOLDER = re.compile(r'"\s*(Erro!|Ops!|Algo deu errado|Algo errado|Tchau!|Adeus)\s*"')

# UX-PROGRESSION-02: substantivos "festejando" sucesso sem contexto.
# Detecta strings só com confirmacao genérica em maiúscula + bang.
# Ex: "Sucesso!", "Pronto!", "Concluído!". OK quando seguido de ":" ou outras palavras.
SUCESSO_VAZIO = re.compile(
    r'"\s*(Sucesso|Pronto|Concluído|Ok|OK|Feito|Conclui)\s*[!.]?\s*"'
)


def scan_file(path: Path) -> list[tuple[int, str]]:
    """Retorna lista de (linha, snippet) com violações.

    Heurística anti-falso-positivo: pula linhas com `logger.`, `if `
    ternário ou tags internas de registro (`tag = "OK"` etc.), porque
    são contextos não user-facing.
    """
    hits: list[tuple[int, str]] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return hits
    for n, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        # Skip de contextos internos (logger, tags de registry, condicionais ternárias)
        if "logger." in stripped or stripped.startswith("tag ="):
            continue
        if " if " in stripped and " else " in stripped:
            # Linha tipo: tag = "OK" if success else "ERRO" -- interno
            continue
        if ENGLISH_UX.search(line) or PLACEHOLDER.search(line) or SUCESSO_VAZIO.search(line):
            hits.append((n, stripped[:120]))
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit de microcopy (UX-PROGRESSION-01)")
    parser.add_argument("--check", action="store_true", help="Exit 1 se há violações")
    args = parser.parse_args()

    total_hits = 0
    for dirname in SCAN_DIRS:
        root = REPO_ROOT / dirname
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            hits = scan_file(path)
            if hits:
                rel = path.relative_to(REPO_ROOT)
                print(f"[viol] {rel}:")
                for n, snip in hits:
                    print(f"    :{n}  {snip}")
                total_hits += len(hits)

    if total_hits == 0:
        print("[ok] microcopy audit: zero violações detectadas")
        return 0
    print(f"[fail] microcopy audit: {total_hits} violação(ões)")
    return 1 if args.check else 0


if __name__ == "__main__":
    sys.exit(main())
