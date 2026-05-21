#!/usr/bin/env python3
"""Sanitiza acentuação PT-BR em specs de sprint do Nyx-Code.

Aplica regex de substituição em 25 palavras-padrão sem acento para versão acentuada.
Idempotente: rodar duas vezes produz mesmo arquivo.

Uso:
    python3 scripts/sanitize_spec_acentuacao.py <spec1.md> <spec2.md> ...
    python3 scripts/sanitize_spec_acentuacao.py --check <spec.md>  # dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SUBSTITUICOES = {
    r"\bnao\b": "não",
    r"\bsessao\b": "sessão",
    r"\bexecucao\b": "execução",
    r"\bacao\b": "ação",
    r"\bcriacao\b": "criação",
    r"\bproximo\b": "próximo",
    r"\bultimo\b": "último",
    r"\bdiretorio\b": "diretório",
    r"\bdescricao\b": "descrição",
    r"\bvalidacao\b": "validação",
    r"\binformacao\b": "informação",
    r"\baplicacao\b": "aplicação",
    r"\boperacao\b": "operação",
    r"\bconexao\b": "conexão",
    r"\bexcecao\b": "exceção",
    r"\bsolucao\b": "solução",
    r"\binteracao\b": "interação",
    r"\bproducao\b": "produção",
    r"\binstalacao\b": "instalação",
    r"\bdocumentacao\b": "documentação",
    r"\bintegracao\b": "integração",
    r"\bcanonica\b": "canônica",
    r"\bautomacao\b": "automação",
    r"\bautomatica\b": "automática",
    r"\bpermissoes\b": "permissões",
}


def sanitize(content: str) -> tuple[str, int]:
    """Retorna (conteudo_novo, num_substituicoes)."""
    total = 0
    novo = content
    for padrao, sub in SUBSTITUICOES.items():
        novo, n = re.subn(padrao, sub, novo, flags=re.IGNORECASE)
        total += n
    return novo, total


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Sanitiza acentuação PT-BR em specs de sprint."
    )
    parser.add_argument(
        "paths", nargs="+", type=Path, help="Arquivos .md de spec"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Apenas reporta sem modificar (dry-run)",
    )
    args = parser.parse_args(argv)

    rc = 0
    for path in args.paths:
        if not path.exists():
            print(f"[erro] {path}: não existe", file=sys.stderr)
            rc = 2
            continue
        original = path.read_text(encoding="utf-8")
        novo, n = sanitize(original)
        if n == 0:
            print(f"[ok] {path}: zero violações")
            continue
        if args.check:
            print(f"[check] {path}: {n} substituições propostas")
            rc = 1
        else:
            path.write_text(novo, encoding="utf-8")
            print(f"[fix] {path}: {n} substituições aplicadas")
    return rc


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
