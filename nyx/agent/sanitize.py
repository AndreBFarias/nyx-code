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


# LOOP-RESULT-NOT-AS-INPUT-01 (G3): markers que a própria infra injeta nos
# resultados de tool. Aparecendo num arg de ENTRADA, são assinatura de eco
# recursivo (o 3b copiou o resultado anterior). Lista conservadora: só strings
# que a infra gera, nunca conteúdo de usuário típico.
_RESULT_MARKERS = (
    "chame done()",
    "OK: Arquivo criado",
    "OK: Editado",
    "Exit code:",
    "[stderr]",
    "[resultado de",
    "regex invalido",  # noqa-acento -- marker literal: variante sem acento que o 3b ecoa
    "regex inválido",
    "Nenhum resultado para",
    "Bloqueado por",
    "Permissão negada",
    "Permissao negada",
    "Analise e execute",
    "linhas lidas",
)

# Args textuais onde o eco pode aparecer. file_path/path não entram (são curtos
# e já tratados por sanitize_tool_args).
_ECHOABLE_KEYS = ("content", "new_string", "command", "pattern")
# Args essenciais: se viram puro eco (vazios após limpar), a tool é inutilizável.
_ESSENTIAL_KEYS = ("command", "pattern")


def _line_is_echo(line: str, recent_lines: set[str], recent_blob: str) -> bool:
    """True se a linha é eco de um resultado recente -- SEMPRE amarrada ao output.

    Dois casos, ambos exigindo que a evidência tenha vindo de um resultado
    recente da sessão (zero falso-positivo):
    - marker: a linha carrega um marker de controle E esse marker também aparece
      num output recente. Marker-only puro NÃO basta -- senão conteúdo legítimo
      que cite 'Exit code:' (sem ter vindo de um resultado) viraria falso-positivo.
    - substancial: linha com >=30 chars idêntica a uma linha de output recente.
    """
    stripped = line.strip()
    if not stripped:
        return False
    for marker in _RESULT_MARKERS:
        if marker in line and marker in recent_blob:
            return True
    return len(stripped) >= 30 and stripped in recent_lines


def strip_result_echo(
    name: str, args: Any, recent_outputs: list[str]
) -> tuple[dict[str, Any], bool]:
    """Remove de args textuais as linhas que ecoam um resultado recente de tool.

    Retorna (args_limpos, should_reject). should_reject=True quando um arg
    ESSENCIAL (command/pattern) ficou vazio após remover o eco -- a tool virou
    puro eco e deve ser rejeitada + re-emitida. Puro/determinístico; só toca
    _ECHOABLE_KEYS; não muta o input (devolve cópia). Idempotente: re-rodar sobre
    o resultado não muda mais nada (as linhas de eco já foram removidas).
    """
    if not isinstance(args, dict) or not recent_outputs:
        return (args if isinstance(args, dict) else {}, False)
    recent_blob = "\n".join(out or "" for out in recent_outputs)
    recent_lines = {ln.strip() for ln in recent_blob.splitlines() if ln.strip()}
    cleaned = dict(args)
    should_reject = False
    for key in _ECHOABLE_KEYS:
        v = cleaned.get(key)
        if not isinstance(v, str) or not v.strip():
            continue
        kept = [
            ln for ln in v.splitlines()
            if not _line_is_echo(ln, recent_lines, recent_blob)
        ]
        new_v = "\n".join(kept).strip()
        if new_v != v.strip():
            cleaned[key] = new_v
            if not new_v and key in _ESSENTIAL_KEYS:
                should_reject = True
    return cleaned, should_reject


# "Limpar a ferramenta antes de usá-la é metade do trabalho." -- princípio de execução
