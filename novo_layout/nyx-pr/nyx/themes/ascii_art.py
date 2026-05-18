"""
Nyx Code — ASCII art canônica

Arte ASCII própria do projeto, usando Block Elements (U+2580..259F),
Braille (U+2800..28FF) e ASCII seguro. Fora da faixa de emoji (ADR-004).

Cada arte tem:
  - versão UTF-8 rica
  - fallback ASCII (degrada graciosamente)
  - meta-info: altura, largura, peso visual

Convenção: a arte é uma lista de strings (linhas). Largura sempre uniforme
em monospace. Renderer pode envelopar em cor via banner.py.
"""

from __future__ import annotations


# ════════════════════════════════════════════════════════════════════════════
# NYX — banner grande (estilo neofetch, 12 linhas)
# ════════════════════════════════════════════════════════════════════════════
# Composta com Block Elements (▓ ▒ ░ ▐ ▌) — fora da faixa de emoji.
# Largura: ~36 colunas. Use junto com system info ao lado.

NYX_BANNER_UTF8: tuple[str, ...] = (
    "                                    ",
    "   ███▄    █  ▓██   ██▓  ▒██   ██▒  ",
    "   ██ ▀█   █   ▒██  ██▒  ▒▒ █ █ ▒░  ",
    "  ▓██  ▀█ ██▒   ▒██ ██░  ░░  █   ░  ",
    "  ▓██▒  ▐▌██▒    ░ ▐██▓░  ░ █ █ ▒   ",
    "  ▒██░   ▓██░    ░ ██▒▓░ ░░  █   ░  ",
    "  ░ ▒░   ▒ ▒    ██▒▒▒     ░     ░   ",
    "  ░ ░░   ░ ▒░ ▓██ ░▒░    ░     ░    ",
    "     ░   ░ ░  ▒ ▒ ░░          ░     ",
    "           ░  ░ ░                   ",
    "              ░ ░                   ",
    "                                    ",
)

NYX_BANNER_ASCII: tuple[str, ...] = (
    "                                  ",
    "  ###   #  #     # #     #   #    ",
    "  ## #  #   #   #   #   # # #     ",
    "  #  # #     # #     # #   #      ",
    "  #   ##      #       #            ",
    "  #    #     # #     # #   #      ",
    "  #         #   #   #   #         ",
    "                                   ",
    "    nyx code — 100% offline        ",
    "                                  ",
)


# ════════════════════════════════════════════════════════════════════════════
# NYX — banner médio (6 linhas, compacto)
# ════════════════════════════════════════════════════════════════════════════

NYX_BANNER_MID_UTF8: tuple[str, ...] = (
    "                            ",
    "  ██▄  █ ▀▄ ▀▄ █▀▄    Nyx   ",
    "  █ █▄█  █▄█   █▄▀          ",
    "  █  ▀█  ▀█▀   █  ▀         ",
    "                            ",
)

NYX_BANNER_MID_ASCII: tuple[str, ...] = (
    "                            ",
    "  ##   #  #  #  #   #   Nyx ",
    "  # #  #   ##    ###        ",
    "  #  # #   ##    # #        ",
    "                            ",
)


# ════════════════════════════════════════════════════════════════════════════
# NYX — banner mínimo (1 linha, pra REPL prompt fancy)
# ════════════════════════════════════════════════════════════════════════════

NYX_BANNER_MINI_UTF8 = " Nyx "
NYX_BANNER_MINI_ASCII = "> Nyx >"


# ════════════════════════════════════════════════════════════════════════════
# SIGILO DE RITUAL — pedido pra comandos destrutivos
# ════════════════════════════════════════════════════════════════════════════
# Pequeno glifo desenhado em box drawing pra que o dev "tracejar" antes
# de confirmar comando destrutivo. Carrega peso visual mas zero emoji.

RITUAL_SIGIL_UTF8: tuple[str, ...] = (
    "╭───────╮",
    "│   ╱   │",
    "│  ╱ │  │",
    "│ ╱──┴─ │",
    "╰───────╯",
)

RITUAL_SIGIL_ASCII: tuple[str, ...] = (
    "+-------+",
    "|   /   |",
    "|  / |  |",
    "| /--+- |",
    "+-------+",
)


# ════════════════════════════════════════════════════════════════════════════
# CONSTELAÇÃO DE TOOL CALLS — usado em /constellation
# ════════════════════════════════════════════════════════════════════════════
# Glifos isolados pra montar grafos ASCII de sessão.

CONSTELLATION_NODES = {
    "read":   "",
    "edit":   "",
    "exec":   "",
    "memory": "",
    "error":  "",  # U+2715 — fora de Dingbats decorativos
    "done":   "",
}

CONSTELLATION_EDGES = {
    "h":      "─",
    "v":      "│",
    "tl":     "╭",
    "tr":     "╮",
    "bl":     "╰",
    "br":     "╯",
    "cross":  "┼",
    "ljoin":  "├",
    "rjoin":  "┤",
}


# ════════════════════════════════════════════════════════════════════════════
# HEARTBEAT — sparkline Braille pra pulso do modelo
# ════════════════════════════════════════════════════════════════════════════
# Cada frame é 1 char Braille; varia em "altura" sugerida.
# Use NyxHeartbeat (renderer) pra ciclar.

HEARTBEAT_FRAMES: tuple[str, ...] = ("⠁", "⠃", "⠇", "⡇", "⣇", "⣧", "⣷", "⣿", "⣷", "⣧", "⣇", "⡇", "⠇", "⠃")
HEARTBEAT_FRAMES_ASCII: tuple[str, ...] = (".", ".", ":", ":", "i", "I", "|", "I", "i", ":", ":", ".", ".", ".")


# ════════════════════════════════════════════════════════════════════════════
# HELPER — escolhe versão certa baseada em locale
# ════════════════════════════════════════════════════════════════════════════

def pick_banner(size: str = "large", *, force_ascii: bool = False) -> tuple[str, ...]:
    """Retorna a versão certa do banner.

    Args:
        size: "large" | "mid" | "mini"
        force_ascii: força fallback ASCII (default: detecta pelo locale)
    """
    from nyx.themes.glyphs import locale_supports_utf8

    use_ascii = force_ascii or not locale_supports_utf8()

    if size == "mini":
        return (NYX_BANNER_MINI_ASCII if use_ascii else NYX_BANNER_MINI_UTF8,)
    if size == "mid":
        return NYX_BANNER_MID_ASCII if use_ascii else NYX_BANNER_MID_UTF8
    # default: large
    return NYX_BANNER_ASCII if use_ascii else NYX_BANNER_UTF8


def banner_width(banner: tuple[str, ...]) -> int:
    """Largura visual do banner (max len de qualquer linha)."""
    return max(len(line) for line in banner) if banner else 0


__all__ = [
    "NYX_BANNER_UTF8", "NYX_BANNER_ASCII",
    "NYX_BANNER_MID_UTF8", "NYX_BANNER_MID_ASCII",
    "NYX_BANNER_MINI_UTF8", "NYX_BANNER_MINI_ASCII",
    "RITUAL_SIGIL_UTF8", "RITUAL_SIGIL_ASCII",
    "CONSTELLATION_NODES", "CONSTELLATION_EDGES",
    "HEARTBEAT_FRAMES", "HEARTBEAT_FRAMES_ASCII",
    "pick_banner", "banner_width",
]


# "A arte do terminal é dizer muito em poucos caracteres." — anônimo
