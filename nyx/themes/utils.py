"""Utilitários de cor para o sistema de temas.

Port de src/ui/theme_manager/utils.py da Luna.
"""


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    """Converte #RRGGBB para tupla (r, g, b)."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Converte (r, g, b) para #rrggbb."""
    return f"#{min(255, max(0, r)):02x}{min(255, max(0, g)):02x}{min(255, max(0, b)):02x}"


def lighten_color(hex_color: str, amount: int = 20) -> str:
    """Clareia uma cor hex por amount unidades RGB."""
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(r + amount, g + amount, b + amount)


def darken_color(hex_color: str, amount: int = 20) -> str:
    """Escurece uma cor hex por amount unidades RGB."""
    r, g, b = hex_to_rgb(hex_color)
    return rgb_to_hex(r - amount, g - amount, b - amount)


def hex_to_ansi(hex_color: str) -> str:
    """Converte #RRGGBB para escape sequence ANSI 24-bit (foreground)."""
    r, g, b = hex_to_rgb(hex_color)
    return f"\\033[38;2;{r};{g};{b}m"


def hex_to_ansi_raw(hex_color: str) -> str:
    """Converte #RRGGBB para escape sequence ANSI 24-bit (bytes reais)."""
    r, g, b = hex_to_rgb(hex_color)
    return f"\033[38;2;{r};{g};{b}m"


# "A medida de um homem é o que ele faz com o poder." -- Platão
