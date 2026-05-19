"""Render showcase de cada aesthetic com paleta+glifos crus.

Bypassa o banner (que ainda não consome glyphs do aesthetic) e desenha um
quadro de demonstração usando AESTHETICS[<id>] diretamente. Usado pela
SPRINT_VISUAL_LAYOUT_06 para gerar PNGs distintos por estética.

Uso:
    NYX_AESTHETIC=cyberpunk ./venv/bin/python scripts/visual/render_aesthetic_showcase.py
    ./venv/bin/python scripts/visual/render_aesthetic_showcase.py cyberpunk
"""

from __future__ import annotations

import os
import sys

from nyx.themes.design_tokens_extended import AESTHETICS


def _hex_to_ansi_fg(hex_or_rgba: str) -> str:
    if hex_or_rgba.startswith("rgba") or not hex_or_rgba.startswith("#"):
        return ""
    h = hex_or_rgba.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[38;2;{r};{g};{b}m"


def _hex_to_ansi_bg(hex_str: str) -> str:
    h = hex_str.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"\033[48;2;{r};{g};{b}m"


def render(aesthetic_id: str) -> str:
    ae = AESTHETICS.get(aesthetic_id, AESTHETICS["default"])
    pal = ae["palette"]
    gl = ae["glyphs"]
    rst = "\033[0m"

    bg = _hex_to_ansi_bg(pal["bg"])
    ink = _hex_to_ansi_fg(pal["ink"])
    ink_dim = _hex_to_ansi_fg(pal["ink_dim"])
    ink_muted = _hex_to_ansi_fg(pal["ink_muted"])
    accent = _hex_to_ansi_fg(pal["accent"])
    ember = _hex_to_ansi_fg(pal["ember"])
    success = _hex_to_ansi_fg(pal["success"])

    width = 70
    h_line = gl["h"] * (width - 2)
    pad = " " * (width - 2)

    out = []
    out.append(f"{bg}{pad}{rst}")
    out.append(f"{bg}{accent}{gl['tl']}{h_line}{gl['tr']}{rst}")
    title = f"NYX-CODE  --  AESTHETIC: {ae['name'].upper()}"
    spc_l = (width - 2 - len(title)) // 2
    spc_r = (width - 2 - len(title)) - spc_l
    out.append(
        f"{bg}{accent}{gl['v']}{rst}{bg}{ink}{' ' * spc_l}{title}{' ' * spc_r}{rst}{bg}{accent}{gl['v']}{rst}"
    )
    out.append(f"{bg}{accent}{gl['v']}{ink_muted}{h_line}{accent}{gl['v']}{rst}")
    tag = ae.get("tagline", "")[: width - 6]
    tag_pad = " " * (width - 4 - len(tag))
    out.append(
        f"{bg}{accent}{gl['v']} {ink_dim}{tag}{tag_pad}{accent}{gl['v']}{rst}"
    )
    out.append(f"{bg}{accent}{gl['v']}{ink_muted}{h_line}{accent}{gl['v']}{rst}")

    palette_keys = ["bg", "ink", "accent", "ember", "success", "warning", "error", "info"]
    chunks = []
    for k in palette_keys:
        c = pal.get(k, "#888888")
        if c.startswith("#"):
            sw_fg = _hex_to_ansi_fg(c)
            chunks.append(f"{sw_fg}{k[:4].upper():<5}{rst}{bg}")
    line = "  ".join(chunks)
    visible_len = sum(len(k[:4]) + 7 for k in palette_keys) - 2
    fill = " " * max(0, width - 4 - visible_len)
    out.append(f"{bg}{accent}{gl['v']} {line}{fill}{accent}{gl['v']}{rst}")

    out.append(f"{bg}{accent}{gl['v']}{ink_muted}{h_line}{accent}{gl['v']}{rst}")
    glyph_demo = (
        f"glyphs: {gl['tl']}{gl['tr']}{gl['bl']}{gl['br']}  "
        f"{gl['h']*4}  {gl['v']}  "
        f"{accent}{ae['name']}{rst}"
    )
    glyph_visible = f"glyphs: {gl['tl']}{gl['tr']}{gl['bl']}{gl['br']}  {gl['h']*4}  {gl['v']}  {ae['name']}"
    gpad = " " * max(0, width - 4 - len(glyph_visible))
    out.append(
        f"{bg}{accent}{gl['v']} {ink}{glyph_demo}{gpad}{accent}{gl['v']}{rst}"
    )

    out.append(f"{bg}{accent}{gl['v']}{ink_muted}{h_line}{accent}{gl['v']}{rst}")
    status = f"{success}OK{rst} smoke  {ember}*{rst} ember  {accent}>>{rst} accent"
    status_visible = "OK smoke  * ember  >> accent"
    spad = " " * max(0, width - 4 - len(status_visible))
    out.append(f"{bg}{accent}{gl['v']} {status}{spad}{accent}{gl['v']}{rst}")

    out.append(f"{bg}{accent}{gl['bl']}{h_line}{gl['br']}{rst}")
    out.append(f"{bg}{pad}{rst}")
    return "\n".join(out)


def main() -> int:
    if len(sys.argv) > 1:
        aid = sys.argv[1]
    else:
        aid = os.environ.get("NYX_AESTHETIC", "default")
    print(render(aid))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
