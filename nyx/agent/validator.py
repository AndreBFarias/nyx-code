"""PostValidator -- Validação pós-execução de tools.

Contém também o detector de "sucesso forjado" (NYX-NO-HALLUCINATE-TOOL-01):
modelo afirma "Arquivo criado com sucesso" sem chamar tool de escrita no
turno corrente. Regex contra texto final + checagem do histórico recente.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from nyx.agent.models import ActionResult
from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.validator")

# Padrões de falsificação: frases que afirmam execução bem-sucedida.
# Usados por detect_forged_success() quando não houve tool real no turno.
FORGE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?i)arquivo\s+(?:criado|salvo|escrito|gerado|gravado)\s+com\s+sucesso"),
    re.compile(r"(?i)(?:criado|salvo|escrito|gerado|gravado)\s+com\s+sucesso"),
    re.compile(r"(?i)\bpronto[!.,]?\s*$"),
    re.compile(r"(?i)\bfeito[!.,]?\s*$"),
)

# Tools cuja execução real "valida" uma afirmação de sucesso.
SUCCESS_VALIDATING_TOOLS: frozenset[str] = frozenset(
    {"write_file", "edit_file", "create_file", "multi_edit", "patch"}
)


@dataclass
class ValidationResult:
    ok: bool = True
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def validate(tool_name: str, args: dict[str, Any], result: ActionResult) -> ValidationResult:
    """Valida resultado após execução de tool."""
    vr = ValidationResult()

    if not result.success:
        return vr

    if tool_name == "write_file":
        content = args.get("content", "")
        if not content:
            vr.warnings.append("Arquivo criado sem conteúdo")
        output = result.output or ""
        if "0 bytes" in output:
            vr.warnings.append("Arquivo vazio criado")

    if tool_name == "run_command":
        output = result.output or ""
        error_markers = ["error", "traceback", "exception", "fatal"]
        lower_out = output.lower()
        for marker in error_markers:
            if marker in lower_out:
                vr.warnings.append(f"Output contém '{marker}' -- verificar resultado")
                break

    if tool_name == "edit_file":
        output = result.output or ""
        if "0 substituição" in output or "0 substituições" in output:
            vr.warnings.append("Nenhuma substituição realizada")

    if vr.errors:
        vr.ok = False

    return vr


def detect_forged_success(last_assistant_text: str, recent_history: list[Any]) -> ValidationResult:
    """Detecta afirmação de sucesso sem tool de escrita correspondente.

    Critério (NYX-NO-HALLUCINATE-TOOL-01):
    - texto final do assistente casa um padrão FORGE; E
    - nas últimas 4 entradas do histórico não há tool em
      SUCCESS_VALIDATING_TOOLS que tenha terminado com sucesso (sem
      mensagens de bloqueio/erro no result).

    Resultado tem warning quando detecta falsificação; vazio quando ok.
    """
    vr = ValidationResult()
    text = (last_assistant_text or "").strip()
    if not text:
        return vr

    matched: str | None = None
    for pattern in FORGE_PATTERNS:
        if pattern.search(text):
            matched = pattern.pattern
            break
    if matched is None:
        return vr

    for entry in reversed(recent_history[-4:]):
        tool_name = getattr(entry, "tool_name", "") or ""
        if tool_name not in SUCCESS_VALIDATING_TOOLS:
            continue
        tool_result = (getattr(entry, "tool_result", "") or "").lower()
        if not tool_result:
            continue
        if "bloqueado" in tool_result or "permissão negada" in tool_result or "permissao negada" in tool_result:
            continue
        if tool_result.startswith("ok") or "ok:" in tool_result or "criado:" in tool_result or "editado:" in tool_result:
            return vr

    vr.warnings.append("modelo afirma sucesso sem tool call correspondente")
    logger.warning(
        "[forge] padrão de falsificação detectado: pattern=%s preview=%s",
        matched,
        text[:80],
    )
    return vr


# "Confiar mas verificar." -- Ronald Reagan
