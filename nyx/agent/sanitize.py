"""Sanitização estrutural de args de tool_call (EXEC-CONTRACT-TOOLCALL-SANITIZE-01).

G1 do contrato de execução (ponto A): o 3b cola lixo de markdown no tool_call
(crase em volta do path, aspas penduradas, escapes `\\/`). A infra LIMPA a
estrutura antes de executar -- não confia que o 3b emita o arg limpo (ADR-032).
Puro/determinístico: valida estrutura, nunca semântica (sem dicionário de verbos).
"""

from __future__ import annotations

import re
from typing import Any

# Args que carregam um caminho de arquivo/diretório.
_PATH_KEYS = ("file_path", "path")

# Desescapa markdown-escapes comuns que o 3b cola num path: \/ \. \- \_
_UNESCAPE_RE = re.compile(r"\\([/._\-])")


def _clean_path_value(value: str) -> str:
    """Tira crase/aspas/espaço das pontas e desescapa o path. Idempotente."""
    s = value.strip()
    # Remove cercas de markdown / crases / aspas nas pontas (repete p/ aninhado).
    for _ in range(3):
        new = s.strip().strip("`").strip().strip("\"'").strip()
        if new == s:
            break
        s = new
    # Desescapa \/ -> / etc. (um path real não traz esses escapes).
    s = _UNESCAPE_RE.sub(r"\1", s)
    return s.strip()


def sanitize_tool_args(name: str, args: Any) -> dict[str, Any]:
    """Devolve uma CÓPIA dos args com os valores path-like limpos.

    Só toca `file_path`/`path` quando são strings não-vazias e a limpeza muda
    algo. Não remove chaves, não inventa valores, não valida sandbox (isso é do
    validate_path). Se `args` não é dict, devolve como veio.
    """
    if not isinstance(args, dict):
        return args
    cleaned = dict(args)
    for key in _PATH_KEYS:
        v = cleaned.get(key)
        if isinstance(v, str) and v.strip():
            nv = _clean_path_value(v)
            if nv and nv != v:
                cleaned[key] = nv
    return cleaned


# "Limpar a ferramenta antes de usá-la é metade do trabalho." -- princípio de execução
