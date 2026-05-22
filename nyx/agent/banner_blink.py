"""Cursor blink async para o banner Nyx (TUI-REDESIGN-28-07).

Anima o cursor block '▌' do banner '$ nyx.code' por ~1.5s antes de ceder
ao prompt. Skip em ambientes não-TTY ou quando NYX_NO_ANIMATION=1.

Comportamento:
  - Em TTY real: alterna o glifo entre chr(0x258C) ▌ (full block) e
    chr(0x258F) ▏ (thin block) em roxo, 4 ciclos (~1.4s). Cursor SEMPRE
    visível — frame "OFF" (thin) pulsa intensidade ao invés de apagar.
  - Em pipe/CI/gauntlet: retorna imediatamente (noop).
  - Com NYX_NO_ANIMATION=1: retorna imediatamente.
  - asyncio.CancelledError (Ctrl+C / cancelamento de task): restaura
    sequências ANSI e propaga; nunca deixa o terminal corrompido.

Usa save/restore cursor (CSI s / CSI u) para reposicionar sobre o '▌'
da linha 1 do banner e voltar ao prompt sem perturbar layout.

TUI-BANNER-BLINK-SOFT-03: frame OFF passou de espaço (cursor sumia ~40%
do tempo, parecendo bug) para chr(0x258F) em roxo — cursor pulsa entre
full e thin block, oscilando intensidade sem desaparecer.
"""

from __future__ import annotations

import asyncio
import os
import sys

from nyx.agent.services.logging_service import get_logger
from nyx.themes.design_tokens import ANSI_PURPLE_FG, ANSI_RESET

logger = get_logger("nyx.agent.banner_blink")


def _should_skip() -> bool:
    """Retorna True se animação deve ser pulada (não-TTY ou env opt-out)."""
    if not sys.stdout.isatty():
        return True
    if os.environ.get("NYX_NO_ANIMATION") == "1":
        return True
    return False


async def blink_cursor_at(
    rows_up: int = 7,
    cols_right: int = 13,
    frames: int = 4,
    period_s: float = 0.18,
) -> None:
    """Pisca cursor '▌' por ``frames`` ciclos on/off.

    Args:
        rows_up: linhas acima da posição atual do cursor onde está o glifo
            '▌'. Default 7 corresponde ao layout wide do banner
            (linha vazia + base do box + 3 linhas + topo + block_line, com
            cursor já posicionado uma linha abaixo da linha vazia final
            via print).
        cols_right: coluna 1-indexed onde o '▌' está. Default 13 = 2 chars
            de padding "  " + "$ nyx.code" (10 chars), portanto col 13.
        frames: número de ciclos completos (cada ciclo = on + off).
        period_s: duração de cada metade do ciclo em segundos. Default
            0.18 → ciclo de 0.36s → 4 ciclos ≈ 1.44s total.

    Skip silencioso em:
      - ``sys.stdout.isatty() is False`` (gauntlet, CI, pipe).
      - ``os.environ.get('NYX_NO_ANIMATION') == '1'``.

    Não bloqueia stdin: prompt_toolkit drena buffer logo após o retorno.
    Em CancelledError, restaura cursor e propaga para shutdown limpo.
    """
    if _should_skip():
        return

    # Salvar posição corrente do cursor (logo após print do banner).
    sys.stdout.write("\033[s")
    sys.stdout.flush()

    try:
        for _ in range(frames):
            # ON: posiciona em (linha_atual - rows_up, col cols_right) e
            # escreve o glifo em roxo. CSI A move para cima, CSI G vai
            # para a coluna absoluta.
            sys.stdout.write(f"\033[{rows_up}A\033[{cols_right}G")
            sys.stdout.write(f"{ANSI_PURPLE_FG}▌{ANSI_RESET}")
            sys.stdout.flush()
            # Volta cursor para a posição original entre frames; assim,
            # se algo aparecer no stdout durante o sleep, fica coerente.
            sys.stdout.write("\033[u")
            sys.stdout.flush()
            await asyncio.sleep(period_s)

            # OFF: mesma posição, escreve thin block em roxo (cursor sempre
            # visível, oscila intensidade entre full e thin). chr(0x258F)
            # protegido contra sanitizer hostil — invariante #14 cobre.
            sys.stdout.write(f"\033[{rows_up}A\033[{cols_right}G")
            sys.stdout.write(f"{ANSI_PURPLE_FG}{chr(0x258F)}{ANSI_RESET}")
            sys.stdout.flush()
            sys.stdout.write("\033[u")
            sys.stdout.flush()
            await asyncio.sleep(period_s)

        # Estado final: cursor visível (igual ao banner original).
        sys.stdout.write(f"\033[{rows_up}A\033[{cols_right}G")
        sys.stdout.write(f"{ANSI_PURPLE_FG}▌{ANSI_RESET}")
        sys.stdout.flush()
    except asyncio.CancelledError:
        # Restaura glifo estável antes de propagar — evita deixar espaço
        # em branco caso o último frame foi OFF.
        try:
            sys.stdout.write(f"\033[{rows_up}A\033[{cols_right}G")
            sys.stdout.write(f"{ANSI_PURPLE_FG}▌{ANSI_RESET}")
            sys.stdout.flush()
        except Exception as exc:  # noqa: BLE001 -- best-effort no shutdown
            logger.debug("blink cleanup falhou no cancel: %s", exc)
        raise
    finally:
        # Sempre restaura cursor para a posição original (após o banner)
        # para que o prompt apareça no lugar certo.
        try:
            sys.stdout.write("\033[u")
            sys.stdout.flush()
        except Exception as exc:  # noqa: BLE001 -- best-effort no shutdown
            logger.debug("blink restore cursor falhou: %s", exc)


__all__ = ["blink_cursor_at"]


# "Pequenos sinais de vida tornam a interface viva." -- princípio TUI.
