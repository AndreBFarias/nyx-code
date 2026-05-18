"""Helpers do CLI extraídos de nyx/cli.py (INFRA-CLI-SPLIT-01).

Mantém o ponto de entrada `run_repl` enxuto. Cada helper aqui é
puro/idempotente o suficiente para ser testado isoladamente. cli.py
re-exporta para compatibilidade.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nyx.agent.services.vision_service import VisionService


_IMAGE_INDEX_PATH = Path.home() / ".nyx" / "image_index.json"


def _persist_image_index(image_map: dict[int, str]) -> None:
    """Persiste image_map em ~/.nyx/image_index.json (VISION-02).

    Permite que /vision N consulte mesmo depois de o usuário avançar
    em outros turns na sessão.
    """
    import json as _json

    try:
        _IMAGE_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
        _IMAGE_INDEX_PATH.write_text(
            _json.dumps({str(k): v for k, v in image_map.items()}),
            encoding="utf-8",
        )
    except OSError as exc:
        import logging as _log

        _log.getLogger("nyx.cli").warning("image_index persist falhou: %s", exc)


def _shorten_description(desc: str, max_chars: int = 200) -> str:
    """Trunca descrição em duas primeiras frases ou max_chars (VISION-02)."""
    if len(desc) <= max_chars:
        return desc
    sentences = desc.split(". ")
    acc = ""
    for s in sentences[:2]:
        if len(acc) + len(s) > max_chars:
            break
        acc += s + ". "
    return (acc.strip() or desc[:max_chars]) + "…"


def _expand_images(
    user_input: str,
    image_map: dict[int, str],
    vision: "VisionService | None" = None,
) -> str:
    """Substitui `[Image #N]` pela descrição da imagem em image_map (VISION-02)."""
    import re

    from nyx.agent.services.vision_service import VisionService

    if not image_map:
        return user_input

    svc = vision if vision is not None else VisionService()

    def _repl(match: re.Match[str]) -> str:
        n = int(match.group(1))
        path_str = image_map.get(n)
        if not path_str:
            return f"[Imagem #{n}: referência inválida]"
        path = Path(path_str)
        if not path.is_file():
            return f"[Imagem #{n}: arquivo não encontrado]"
        desc = svc.describe(path)
        short = _shorten_description(desc)
        return f"[Imagem #{n}: {short}]"

    return re.sub(r"\[Image #(\d+)\]", _repl, user_input)


def maybe_offer_resume(agent: object, project_name: str = "", *, ansi_accent: str = "", ansi_reset: str = "") -> None:
    """Oferece /resume no boot se TTL <48h e >=3 turnos (SESSION-RESUME-01).

    Suprime prompt em pipe/CI (stdin não-tty), exceção, e sessões antigas.
    """
    import time as _time

    from nyx.agent.services.logging_service import get_logger
    from nyx.agent.persistence import load_index, load_session_by_id

    logger = get_logger("nyx.cli")

    if not sys.stdin.isatty():
        return
    idx = load_index()
    if not idx:
        return
    last = idx[-1]
    if project_name and last.get("projeto") and last["projeto"] != project_name:
        return
    age_s = _time.time() - last.get("ts_fim", 0)
    if age_s > 48 * 3600 or last.get("n_turnos", 0) < 3:
        return
    preview = last.get("primeiro_prompt", "") or last.get("id", "")
    try:
        resp = input(f"Retomar última sessão ({preview[:60]})? [s/N] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return
    if resp != "s":
        return
    loaded = load_session_by_id(last["id"])
    if loaded:
        agent._session = loaded  # type: ignore[attr-defined]
        sys.stdout.write(
            f"  {ansi_accent}[ok]{ansi_reset} {len(loaded.history)} turnos anteriores restaurados\n"
        )
        sys.stdout.flush()
        logger.info("sessão %s restaurada (%d entradas)", last["id"][:24], len(loaded.history))
