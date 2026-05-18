"""Banner de boot do Nyx CLI (v2 -- neofetch style).

Três modos:
  - Compacto (cols < 60): 1 linha de tagline + 1 linha de versão.
  - Wide (60 <= cols < 100): banner do v1 (build_banner_classic), retido.
  - Neofetch (cols >= 100): logo ASCII à esquerda + system info à direita.

Substitui ``nyx/agent/banner.py`` antigo. A função ``build_banner()``
mantém a assinatura externa — call-sites em ``cli.py`` continuam funcionando.

Consome ``themes/design_tokens.py`` (tema ativo) e ``themes/glyphs.py``
(box drawing + fallback ASCII). Ver ADR-023 e ADR-025.
"""

from __future__ import annotations

import platform
import shutil
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from nyx.__version__ import __version__ as NYX_VERSION
from nyx.themes.ascii_art import get_logo
from nyx.themes.design_tokens import (
    ANSI_BOLD,
    ANSI_DIM,
    ANSI_RESET,
    get_active_theme,
)
from nyx.themes.glyphs import glyphs_for, supports_utf8

if TYPE_CHECKING:
    from nyx.config.settings import NyxSettings


# ──────────────────────────────────────────────────────────────────────────────
# 1. COLETA DE SYSTEM INFO (neofetch-like)
# ──────────────────────────────────────────────────────────────────────────────


def _system_summary() -> list[tuple[str, str, str]]:
    """Retorna lista de (label, valor_primário, valor_secundário).

    Mantém TODOS os campos curtos -- cada um vira UMA linha do painel direito.
    Falhas silenciosas: campos indisponíveis ficam como "?".
    """
    info: list[tuple[str, str, str]] = []

    # SO
    try:
        sys_name = platform.system()
        if sys_name == "Linux":
            try:
                with open("/etc/os-release", encoding="utf-8") as f:
                    osr = dict(
                        line.strip().split("=", 1)
                        for line in f
                        if "=" in line and not line.startswith("#")
                    )
                pretty = osr.get("PRETTY_NAME", "Linux").strip('"')
            except OSError:
                pretty = "Linux"
            info.append(("sistema", pretty, platform.machine()))
        else:
            info.append(("sistema", sys_name, platform.machine()))
    except Exception:  # noqa: BLE001
        info.append(("sistema", "?", ""))

    # Kernel
    try:
        info.append(("kernel", platform.release(), ""))
    except Exception:  # noqa: BLE001
        info.append(("kernel", "?", ""))

    # Uptime
    try:
        if Path("/proc/uptime").exists():
            with open("/proc/uptime") as f:
                seconds = float(f.read().split()[0])
            hours, rem = divmod(int(seconds), 3600)
            minutes = rem // 60
            uptime = f"{hours}h {minutes}min"
            info.append(("tempo ativo", uptime, ""))
    except Exception:  # noqa: BLE001
        pass

    # Shell
    import os as _os
    shell = _os.environ.get("SHELL", "?").split("/")[-1]
    info.append(("shell", shell, ""))

    # GPU + VRAM (nvidia-smi se disponível)
    try:
        out = subprocess.run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.used,memory.total",
                "--format=csv,noheader,nounits",
            ],
            capture_output=True, text=True, timeout=1.5,
        )
        if out.returncode == 0 and out.stdout.strip():
            parts = [p.strip() for p in out.stdout.strip().split(",")]
            if len(parts) == 3:
                name, used, total = parts
                info.append(("GPU", name, f"{int(total)//1024} GB VRAM"))
                pct = int(used) * 100 // max(int(total), 1)
                info.append(("VRAM", f"{int(used)/1024:.1f} / {int(total)/1024:.1f} GiB",
                             f"uso {pct}%"))
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        pass

    # RAM
    try:
        if Path("/proc/meminfo").exists():
            mem: dict[str, int] = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    k, v = line.split(":", 1)
                    mem[k] = int(v.split()[0])
            total = mem.get("MemTotal", 0) / 1024 / 1024
            avail = mem.get("MemAvailable", 0) / 1024 / 1024
            used = total - avail
            pct = int(used * 100 / max(total, 1))
            info.append(("memória", f"{used:.1f} / {total:.1f} GiB", f"uso {pct}%"))
    except Exception:  # noqa: BLE001
        pass

    return info


# ──────────────────────────────────────────────────────────────────────────────
# 2. BUILD BANNER
# ──────────────────────────────────────────────────────────────────────────────


def build_banner(
    model: str,
    tools_count: int,
    project: str,
    settings: "NyxSettings | None" = None,
    cols: int | None = None,
    memory_count: int | None = None,
) -> str:
    """Constrói banner de abertura. Compatível com a API antiga.

    Em terminais >= 100 cols, usa layout neofetch (logo + sistema).
    Em terminais médios (60-99), volta ao banner clássico de boxes.
    Em terminais estreitos (<60), compacto de duas linhas.
    """
    if cols is None:
        cols = shutil.get_terminal_size(fallback=(80, 24)).columns

    if cols >= 100:
        return _build_neofetch(model, tools_count, project, memory_count)
    if cols >= 60:
        return _build_classic(model, tools_count, project, memory_count, cols)
    return _build_compact(model, project, cols)


# ── Neofetch (cols >= 100) ────────────────────────────────────────────────────


def _build_neofetch(
    model: str, tools_count: int, project: str, memory_count: int | None,
) -> str:
    theme = get_active_theme()
    g = glyphs_for(theme.aesthetic.id)

    accent = theme.ansi_accent_fg
    ember = theme.ansi_ember_fg
    primary = theme.ansi_primary_fg
    muted = theme.ansi_muted_fg
    success = theme.ansi_success_fg
    nc = ANSI_RESET
    dim = ANSI_DIM

    logo = get_logo(width=40, ascii_only=not supports_utf8())
    system = _system_summary()

    # Pad logo até 12 linhas (system info também terá no máximo 12)
    while len(logo) < 12:
        logo.append("")

    # Linha extra de info Nyx-específica
    nyx_info = [
        ("", "", ""),
        ("Nyx", f"v{NYX_VERSION}", ""),
        ("modelo", model, ""),
        ("tools", str(tools_count), ""),
        ("projeto", project, ""),
    ]
    if memory_count is not None:
        nyx_info.append(("memória", f"{memory_count} entradas", ""))
    nyx_info.append(("rede", "100% offline", ""))

    # Compõe lado-a-lado
    lines: list[str] = [""]
    pairs = list(zip(logo + [""] * (max(0, len(nyx_info) - len(logo))),
                     system + nyx_info))

    for i, (logo_line, info) in enumerate(pairs):
        label, val1, val2 = info if info else ("", "", "")
        logo_color = accent if i % 2 == 0 else ember
        logo_part = f"  {logo_color}{logo_line:<40}{nc}"
        if label:
            label_part = f"{ember}{ANSI_BOLD}{label:<14}{nc}"
            val_part = f"{primary}{ANSI_BOLD}{val1}{nc}"
            if val2:
                val_part += f" {muted}{val2}{nc}"
        else:
            label_part = ""
            val_part = ""
        lines.append(f"{logo_part}{label_part}{val_part}")

    # Paleta visual no rodapé do logo
    lines.append("")
    swatch = (
        f"  {' ' * 40}"
        f"{accent}█{nc}{ember}█{nc}{success}█{nc}"
        f"  {dim}{accent}▓{nc}{dim}{ember}▓{nc}{dim}{success}▓{nc}"
        f"  {muted}░░░{nc}"
    )
    lines.append(swatch)
    lines.append("")
    lines.append(
        f"  {ember}{g.arrow}{nc} {muted}diga o que precisa.{nc}"
    )
    lines.append("")

    return "\n".join(lines)


# ── Clássico (60 <= cols < 100) ───────────────────────────────────────────────


def _build_classic(
    model: str, tools_count: int, project: str,
    memory_count: int | None, cols: int,
) -> str:
    theme = get_active_theme()
    g = glyphs_for(theme.aesthetic.id)
    b = g.box

    accent = theme.ansi_accent_fg
    muted = theme.ansi_muted_fg
    nc = ANSI_RESET

    largura = min(cols - 2, 78)
    interior = largura - 2

    title_left = f" Nyx · v{NYX_VERSION} "
    title_right = " 100% offline "
    pad = max(2, interior - len(title_left) - len(title_right) - 2)
    topo = f"  {accent}{b.tl}{b.h}{title_left}{b.h * pad}{title_right}{b.h}{b.tr}{nc}"

    def linha(payload: str) -> str:
        raw_len = len(payload)
        pad_right = max(0, interior - raw_len - 2)
        return f"  {accent}{b.v}{nc} {payload}{' ' * pad_right} {accent}{b.v}{nc}"

    col_modelo = f"   modelo    {model:<18s}   tools    {tools_count}"
    col_projeto = f"   projeto   {project:<18s}"
    mem_str = f"{memory_count} entradas" if memory_count is not None else "ativa"
    col_memoria = f"   memória   {mem_str}"

    vazia = linha("")
    rodape_txt = " /help para comandos · Ctrl+D para sair "
    rodape_pad = max(2, interior - len(rodape_txt) - 2)
    base = f"  {accent}{b.bl}{b.h}{muted}{rodape_txt}{accent}{b.h * rodape_pad}{b.h}{b.br}{nc}"

    return "\n".join([
        "",
        topo,
        vazia,
        linha(col_modelo),
        linha(col_projeto),
        linha(col_memoria),
        vazia,
        base,
        "",
    ])


# ── Compacto (cols < 60) ──────────────────────────────────────────────────────


def _build_compact(model: str, project: str, cols: int) -> str:
    theme = get_active_theme()
    accent = theme.ansi_accent_fg
    muted = theme.ansi_muted_fg
    nc = ANSI_RESET

    line1 = f"  {accent}Nyx · v{NYX_VERSION}{nc}  {muted}· {model} · {project}{nc}"
    line2 = f"  {muted}/help · Ctrl+D para sair · 100% offline{nc}"
    return "\n".join(["", line1, line2, ""])


__all__ = ["build_banner"]


# "A forma segue a função." -- Louis Sullivan
