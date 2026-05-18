"""ASCII art da assinatura Nyx, para boots estilo neofetch.

Composto APENAS com Block Elements (U+2580-U+259F) e ASCII seguro — fora
das faixas de emoji proibidas (ADR-004). Renderizado lado-a-lado com info
de sistema (kernel, GPU, memória) no banner.
"""

from __future__ import annotations


# 12 linhas × 36 cols. Espelha o logotipo do projeto.
# Block Elements: ▀ ▁ ▂ ▃ ▄ ▅ ▆ ▇ █ ▉ ▊ ▋ ▌ ▍ ▎ ▏ ▐ ░ ▒ ▓
NYX_LOGO = """
   ███▄    █  ▓██   ██▓  ▒██   ██▒
   ██ ▀█   █   ▒██  ██▒  ▒▒ █ █ ▒░
  ▓██  ▀█ ██▒   ▒██ ██░  ░░  █   ░
  ▓██▒  ▐▌██▒    ░ ▐██▓░  ░ █ █ ▒
  ▒██░   ▓██░    ░ ██▒▓░ ░░  █   ░
  ░ ▒░   ▒ ▒    ██▒▒▒     ░     ░
  ░ ░░   ░ ▒░ ▓██ ░▒░    ░     ░
     ░   ░ ░  ▒ ▒ ░░          ░
           ░  ░ ░
              ░ ░
""".strip("\n").splitlines()


# Versão ASCII pura, para terminais sem UTF-8.
NYX_LOGO_ASCII = """
   N   N   Y   Y   X   X
   NN  N    Y Y     X X
   N N N     Y       X
   N  NN     Y      X X
   N   N     Y     X   X
""".strip("\n").splitlines()


# Mini-logo compacto (4 linhas) para banners em terminais estreitos.
NYX_LOGO_MINI = """
 ███▄    █  ▓██   ██▓  ▒██   ██▒
 ██ ▀█   █   ▒██  ██▒  ▒▒ █ █ ▒░
▓██  ▀█ ██▒   ▒██ ██░  ░░  █   ░
▒██░   ▓██░    ░ ██▒▓░ ░░  █   ░
""".strip("\n").splitlines()


# Ornamentos arcanos -- usar com moderação, em headers ritualísticos.
ARCANE_BORDER_TOP = "─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─"
ARCANE_BORDER_BOT = "─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─"


def get_logo(width: int = 80, ascii_only: bool = False) -> list[str]:
    """Escolhe o logo apropriado para a largura disponível.

    >=40 cols + UTF-8: NYX_LOGO completo.
    >=24 cols + UTF-8: NYX_LOGO_MINI.
    Caso contrário (ou ascii_only): NYX_LOGO_ASCII.
    """
    if ascii_only or width < 24:
        return NYX_LOGO_ASCII
    if width < 40:
        return NYX_LOGO_MINI
    return NYX_LOGO


__all__ = [
    "NYX_LOGO", "NYX_LOGO_ASCII", "NYX_LOGO_MINI",
    "ARCANE_BORDER_TOP", "ARCANE_BORDER_BOT",
    "get_logo",
]


# "Um logo é uma promessa em poucos traços." -- Paul Rand
