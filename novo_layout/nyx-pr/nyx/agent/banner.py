"""
Nyx Code — Banner de boot (refatorado, PR-ready)

Três modos:
  compact   — cols < 80, 3 linhas
  wide      — cols >= 80, banner em box
  neofetch  — NYX_BANNER=neofetch ou --banner neofetch — ASCII art "NYX"
              + system info estilo neofetch (SO, kernel, GPU, VRAM, etc.)

Consome design_tokens + ascii_art como fonte única (ADR-023).
Retrocompatível: a função build_banner() mantém a mesma assinatura.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING

from nyx.__version__ import __version__ as NYX_VERSION
from nyx.themes import build_theme
from nyx.themes.ascii_art import pick_banner, banner_width

if TYPE_CHECKING:
    from nyx.config.settings import NyxSettings
    from nyx.themes.design_tokens import Theme


# ════════════════════════════════════════════════════════════════════════════
# API PÚBLICA
# ════════════════════════════════════════════════════════════════════════════

def build_banner(
    model: str,
    tools_count: int,
    project: str,
    settings: "NyxSettings | None" = None,
    cols: int | None = None,
    memory_count: int | None = None,
    mode: str | None = None,
) -> str:
    """Constrói banner de abertura.

    Args:
        model:        modelo Ollama ativo (ex: qwen3:4b)
        tools_count:  número de tools registradas (34)
        project:      nome do projeto (basename do cwd)
        settings:     NyxSettings (carrega default se None)
        cols:         largura do terminal (detecta default)
        memory_count: número de entradas em ~/.nyx/memory/ (opcional)
        mode:         "compact" | "wide" | "neofetch" | None (auto)

    Modo auto:
      - cols < 80           → compact
      - NYX_BANNER=neofetch → neofetch
      - resto               → wide
    """
    from nyx.config.settings import load_settings

    if settings is None:
        settings = load_settings()
    if cols is None:
        cols = shutil.get_terminal_size(fallback=(80, 24)).columns
    if mode is None:
        if os.environ.get("NYX_BANNER", "").lower() == "neofetch":
            mode = "neofetch"
        elif cols < 80:
            mode = "compact"
        else:
            mode = "wide"

    theme = build_theme()  # carrega tema persistido (config + env)

    if mode == "neofetch":
        return _build_neofetch(theme, model, tools_count, project, settings, memory_count)
    if mode == "compact":
        return _build_compact(theme, model, project, settings)
    return _build_wide(theme, model, tools_count, project, settings, cols, memory_count)


# ════════════════════════════════════════════════════════════════════════════
# COMPACT — 3 linhas, cols < 80
# ════════════════════════════════════════════════════════════════════════════

def _build_compact(
    theme: "Theme",
    model: str,
    project: str,
    settings: "NyxSettings",
) -> str:
    g = theme.glyphs
    a = theme.ansi
    nc = a.reset

    ports = f":{settings.ollama_port} ollama  {g.bullet}  :{settings.proxy_port} proxy"

    topo = f"  {a.accent}{g.tl}{g.h} Nyx {g.bullet} {model} {g.bullet} {project} {g.h}{g.tr}{nc}"
    meio = f"  {a.accent}{g.v}{nc}   {a.ink_dim}{ports}{nc}"
    base = f"  {a.accent}{g.bl}{g.h} {a.ink_dim}/help {g.bullet} Ctrl+D{a.accent} {g.h * 6}{g.br}{nc}"

    return "\n".join(["", topo, meio, base, ""])


# ════════════════════════════════════════════════════════════════════════════
# WIDE — banner em box, cols >= 80
# ════════════════════════════════════════════════════════════════════════════

def _build_wide(
    theme: "Theme",
    model: str,
    tools_count: int,
    project: str,
    settings: "NyxSettings",
    cols: int,
    memory_count: int | None,
) -> str:
    g = theme.glyphs
    a = theme.ansi
    nc = a.reset

    largura_total = min(cols - 2, 78)
    interior = largura_total - 2

    title_left = " Nyx "
    title_mid = f" v{NYX_VERSION} "
    title_right = " 100% offline "
    used = len(title_left) + len(title_mid) + len(title_right) + 2
    pad = max(2, interior - used)
    topo = (
        f"  {a.accent}{g.tl}{g.h}{title_left}{g.h}{title_mid}{g.h * pad}"
        f"{title_right}{g.h}{g.tr}{nc}"
    )

    def linha(payload: str) -> str:
        raw_len = len(payload)
        pad_right = max(0, interior - raw_len - 2)
        return f"  {a.accent}{g.v}{nc} {payload}{' ' * pad_right} {a.accent}{g.v}{nc}"

    ports_line = f":{settings.ollama_port} ollama  {g.bullet}  :{settings.proxy_port} proxy"
    col_labels = f"   modelo    {model:<18s}   tools    {tools_count}"
    col_projeto = f"   projeto   {project:<18s}   visão    moondream (fria)"
    col_rede = f"   rede      {ports_line}"
    mem_str = f"{memory_count} entradas" if memory_count is not None else "ativa"
    col_memoria = f"   memória   {mem_str}"

    vazia = linha("")
    rodape_txt = f" /help para comandos {g.bullet} Ctrl+D para sair "
    rodape_pad = max(2, interior - len(rodape_txt) - 2)
    base = f"  {a.accent}{g.bl}{g.h}{a.ink_dim}{rodape_txt}{a.accent}{g.h * rodape_pad}{g.h}{g.br}{nc}"

    return "\n".join([
        "",
        topo,
        vazia,
        linha(col_labels),
        linha(col_projeto),
        linha(col_rede),
        linha(col_memoria),
        vazia,
        base,
        "",
    ])


# ════════════════════════════════════════════════════════════════════════════
# NEOFETCH — ASCII art + system info
# ════════════════════════════════════════════════════════════════════════════

def _build_neofetch(
    theme: "Theme",
    model: str,
    tools_count: int,
    project: str,
    settings: "NyxSettings",
    memory_count: int | None,
) -> str:
    """Banner estilo neofetch: arte NYX à esquerda + info do sistema à direita.

    Usa apenas info LOCAL (uname, /proc, GPU via nvidia-smi se disponível).
    Latency budget: <50ms incluindo subprocess calls (todos com timeout=0.3s).
    """
    a = theme.ansi
    g = theme.glyphs
    nc = a.reset

    art = pick_banner("large")
    info = _gather_system_info(model, tools_count, project, settings, memory_count)

    art_width = banner_width(art)

    # alterna cor entre accent e ember pra ascii art (diagonal stripes feeling)
    def color_art(line: str, idx: int) -> str:
        c = a.accent if idx % 2 == 0 else a.ember
        return f"{c}{line}{nc}"

    lines: list[str] = [""]
    info_padded = list(info) + [""] * max(0, len(art) - len(info))

    for i, art_line in enumerate(art):
        info_line = info_padded[i] if i < len(info_padded) else ""
        lines.append(f"  {color_art(art_line, i)}  {info_line}")

    # rodapé com paleta visual
    blocks = (
        f"{a.accent}█{nc}{a.ember}█{nc}{a.success}█{nc}"
        f"{a.warning}█{nc}{a.error}█{nc}{a.info}█{nc}"
    )
    lines.append("")
    lines.append(f"  {' ' * art_width}  {blocks}  {a.ink_dim}paleta atual{nc}")
    lines.append(
        f"  {' ' * art_width}  {a.ink_dim}/help para comandos {g.bullet} Ctrl+D para sair{nc}"
    )
    lines.append("")
    return "\n".join(lines)


def _gather_system_info(
    model: str,
    tools_count: int,
    project: str,
    settings: "NyxSettings",
    memory_count: int | None,
) -> list[str]:
    """Coleta info do sistema. Cada item é uma string já formatada e colorida."""
    theme = build_theme()
    a = theme.ansi
    nc = a.reset

    def kv(label: str, value: str, hint: str = "") -> str:
        line = f"{a.ember}{label:<14}{nc}{a.ink}{value}{nc}"
        if hint:
            line += f" {a.ink_dim}{hint}{nc}"
        return line

    rows: list[str] = []
    rows.append(f"{a.accent}Nyx Code{nc} v{NYX_VERSION}  {a.ink_dim}{g_safe()}{nc}")
    rows.append(f"{a.ink_dim}{'─' * 32}{nc}")
    rows.append(kv("sistema",  _so(),       platform.machine()))
    rows.append(kv("kernel",   _kernel(),   ""))
    rows.append(kv("tempo",    _uptime(),   "ativa"))
    rows.append(kv("shell",    _shell(),    ""))
    rows.append(kv("CPU",      _cpu(),      ""))
    gpu, vram = _gpu_and_vram()
    rows.append(kv("GPU",      gpu,         ""))
    if vram:
        rows.append(kv("VRAM",  vram,        ""))
    rows.append(kv("memória",  _ram(),      ""))
    rows.append("")
    rows.append(kv("modelo",   model,       "100% offline"))
    rows.append(kv("tools",    f"{tools_count} registradas", ""))
    rows.append(kv("projeto",  project,     ""))
    rows.append(kv("rede",     f":{settings.ollama_port} ollama  {a.ink_dim}{nc}{a.ink}·{nc} {a.ink}:{settings.proxy_port} proxy{nc}", ""))
    if memory_count is not None:
        rows.append(kv("memória",  f"{memory_count} entradas", ""))
    return rows


def g_safe() -> str:
    """Build hash curto se disponível, senão vazio."""
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL, text=True, timeout=0.3,
        ).strip()
    except Exception:
        return ""


def _so() -> str:
    """Detecta distro Linux ou retorna platform.system()."""
    if Path("/etc/os-release").exists():
        try:
            content = Path("/etc/os-release").read_text(encoding="utf-8")
            for line in content.splitlines():
                if line.startswith("PRETTY_NAME="):
                    return line.split("=", 1)[1].strip().strip('"')
        except Exception:
            pass
    return platform.system()


def _kernel() -> str:
    return platform.release()


def _uptime() -> str:
    """Uptime curto: '1h 23min' ou '13min'."""
    try:
        with open("/proc/uptime") as f:
            seconds = float(f.read().split()[0])
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        if h > 0:
            return f"{h}h {m}min"
        return f"{m}min"
    except Exception:
        return "-"


def _shell() -> str:
    return Path(os.environ.get("SHELL", "?")).name


def _cpu() -> str:
    """Modelo + cores. Lê /proc/cpuinfo (Linux)."""
    try:
        with open("/proc/cpuinfo") as f:
            content = f.read()
        for line in content.splitlines():
            if line.startswith("model name"):
                name = line.split(":", 1)[1].strip()
                # encurta — "AMD Ryzen 5 7535HS with Radeon Graphics" → "AMD Ryzen 5 7535HS"
                if "with" in name:
                    name = name.split("with")[0].strip()
                cores = content.count("processor\t:")
                return f"{name} ({cores})"
    except Exception:
        pass
    return platform.processor() or "-"


def _gpu_and_vram() -> tuple[str, str]:
    """GPU model + VRAM usage. Roda nvidia-smi com timeout curto."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total",
             "--format=csv,noheader,nounits"],
            stderr=subprocess.DEVNULL, text=True, timeout=0.5,
        ).strip()
        line = out.splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) >= 3:
            name, used, total = parts[0], int(parts[1]), int(parts[2])
            pct = round(100 * used / total) if total else 0
            return name, f"{used / 1024:.1f} / {total / 1024:.1f} GiB ({pct}%)"
    except Exception:
        pass
    return "—", ""


def _ram() -> str:
    """RAM usage: '9.8 / 14.8 GiB (66%)'."""
    try:
        with open("/proc/meminfo") as f:
            mem: dict[str, int] = {}
            for line in f:
                k, v = line.split(":", 1)
                mem[k] = int(v.strip().split()[0])  # kB
        total_kb = mem.get("MemTotal", 0)
        avail_kb = mem.get("MemAvailable", 0)
        used_kb = total_kb - avail_kb
        total_gb = total_kb / 1024 / 1024
        used_gb = used_kb / 1024 / 1024
        pct = round(100 * used_kb / total_kb) if total_kb else 0
        return f"{used_gb:.1f} / {total_gb:.1f} GiB ({pct}%)"
    except Exception:
        return "-"


__all__ = ["build_banner"]


# "A primeira impressão dura 200ms. Use-os bem." — anônimo
