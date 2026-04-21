"""Design Tokens Nyx -- fonte única da linguagem visual.

Qualquer cor, glifo, box char ou frame de spinner usado na UI (cli.py,
output.py, toolbar, etc.) DEVE vir daqui. Ver ADR-023.

Paleta D (2026-04-18): estrutura CLI minimalista + turquesa histórica +
toques de roxo para estados especiais (bypass ON, memória, skills).
"""

from __future__ import annotations

# ── Cores (hex) ─────────────────────────────────────────────────────

NYX_ACCENT = "#00D4AA"       # turquesa -- accent principal
NYX_ACCENT_DIM = "#007A63"    # turquesa escuro -- hover/selected

NYX_PURPLE = "#9D4EDD"        # roxo -- bypass ON, memória, skills, estado "atenção"
NYX_PURPLE_DIM = "#5A189A"    # roxo escuro

NYX_PRIMARY = "#E8E8E8"       # texto primário
NYX_MUTED = "#606060"         # dim

NYX_BG = "#1A1B23"            # fundo preferido
NYX_BG_SOFT = "#2A2C39"       # fundo de painel

NYX_SUCCESS = "#4ADE80"
NYX_WARNING = "#FFC857"
NYX_ERROR = "#FF6B6B"


# ── ANSI 24-bit (derivados dos hex acima) ───────────────────────────


def hex_to_ansi_fg(hex_str: str) -> str:
    """Converte #RRGGBB para escape ANSI 24-bit foreground."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


def hex_to_ansi_bg(hex_str: str) -> str:
    """Converte #RRGGBB para escape ANSI 24-bit background."""
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[48;2;{r};{g};{b}m"


ANSI_ACCENT_FG = hex_to_ansi_fg(NYX_ACCENT)
ANSI_PURPLE_FG = hex_to_ansi_fg(NYX_PURPLE)
ANSI_PRIMARY_FG = hex_to_ansi_fg(NYX_PRIMARY)
ANSI_MUTED_FG = hex_to_ansi_fg(NYX_MUTED)
ANSI_ERROR_FG = hex_to_ansi_fg(NYX_ERROR)
ANSI_SUCCESS_FG = hex_to_ansi_fg(NYX_SUCCESS)
ANSI_WARNING_FG = hex_to_ansi_fg(NYX_WARNING)

ANSI_DIM = "\033[2m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"


# ── Glifos canônicos (zero emoji, ADR-004) ──────────────────────────
# Faixas de emoji proibidas: U+1F300-U+1F9FF e U+2600-U+27BF.
# Aqui usamos apenas Box Drawing (U+2500-U+257F), Braille (U+2800-U+28FF),
# e ASCII seguro.

BOX_CHARS = {
    "tl": "╭", "tr": "╮", "bl": "╰", "br": "╯",
    "h": "─", "v": "│",
    "tjoin": "┬", "bjoin": "┴", "ljoin": "├", "rjoin": "┤", "cross": "┼",
}

BULLETS = {
    "tool": "●",         # círculo cheio -- tool em execução/concluída
    "tool_ok": "●",
    "tool_err": "●",
    "result": "└─",
    "note": "·",
    "arrow": "→",
    "bypass_on": "[!]",  # substitui U+26A1 (emoji)
    "bypass_off": "[ ]",
    "ready": "●",
    "working": "○",
    "prompt": ">",
}

SPINNER_FRAMES = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")
# Braille Patterns (U+2800-U+28FF) -- símbolo técnico, não emoji.


__all__ = [
    "NYX_ACCENT", "NYX_ACCENT_DIM", "NYX_PURPLE", "NYX_PURPLE_DIM",
    "NYX_PRIMARY", "NYX_MUTED", "NYX_BG", "NYX_BG_SOFT",
    "NYX_SUCCESS", "NYX_WARNING", "NYX_ERROR",
    "ANSI_ACCENT_FG", "ANSI_PURPLE_FG", "ANSI_PRIMARY_FG", "ANSI_MUTED_FG",
    "ANSI_ERROR_FG", "ANSI_SUCCESS_FG", "ANSI_WARNING_FG",
    "ANSI_DIM", "ANSI_BOLD", "ANSI_RESET",
    "BOX_CHARS", "BULLETS", "SPINNER_FRAMES",
    "hex_to_ansi_fg", "hex_to_ansi_bg",
]


# "A linguagem do produto começa pela consistência de seus tokens." -- anônimo
