#!/usr/bin/env python3
"""Menu wizard interativo do Nyx-Code (NYX-MENU-WIZARD-01).

Roda antes de exec do CLI quando `./run.sh --menu` e configura:
- aesthetic + entity (paleta D + 5 alternativas; nyx + 6 entidades)
- modelo (qwen2.5-coder:3b | qwen3:4b | qwen2.5-coder:7b)
- banner mode (compact | wide | neofetch)
- auto-approve (sim | nao)

Persiste em ~/.nyx/config.toml (mesmo arquivo do /config setup).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Permitir invocação direta (./venv/bin/python scripts/menu_wizard.py).
# Sem isso, sys.path não inclui o repo root e `import nyx.*` falha.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from nyx.themes.design_tokens import (  # noqa: E402
    ANSI_ACCENT_FG, ANSI_BOLD, ANSI_DIM, ANSI_PRIMARY_FG,
    ANSI_RESET, ANSI_SUCCESS_FG,
)

CONFIG_PATH = Path.home() / ".nyx" / "config.toml"


def say(*args, **kwargs) -> None:
    """Imprime no stderr (TTY do usuario), preservando stdout pros exports.

    Necessario porque run.sh redireciona o stdout do wizard para
    /tmp/nyx_menu_exports.sh. Sem isso, as perguntas iam pro arquivo.
    """
    kwargs.setdefault("file", sys.stderr)
    kwargs.setdefault("flush", True)
    print(*args, **kwargs)


def banner() -> None:
    bold = ANSI_BOLD
    accent = ANSI_ACCENT_FG
    reset = ANSI_RESET
    say()
    say(f"  {bold}{accent}Nyx{reset} {ANSI_DIM}cockpit / menu{reset}")
    say(f"  {ANSI_DIM}Configure antes de inicializar (Enter aceita default).{reset}")
    say()


def ask(
    prompt: str,
    choices: list[tuple[str, str]],
    default: str,
    step: int | None = None,
    total: int | None = None,
    hint: str | None = None,
) -> str:
    """Mostra choices numeradas; aceita numero ou Enter pro default.

    choices: lista de (valor, descricao).
    TUI-REDESIGN-25-05: contador 'XX/YY' opcional + hint contextual + footer
    '↵ Enter aceita default'.
    """
    accent = ANSI_ACCENT_FG
    bold = ANSI_BOLD
    success = ANSI_SUCCESS_FG
    muted = ANSI_DIM
    reset = ANSI_RESET
    if step is not None and total is not None:
        header = f"{step:02d}/{total:02d} · {prompt}"
    else:
        header = prompt
    say()
    say(f"  {accent}{bold}{header}{reset}")
    if hint:
        say(f"  {muted}{hint}{reset}")
    for i, (val, desc) in enumerate(choices, start=1):
        marker = f"{success}*{reset}" if val == default else " "
        say(f"    {marker} {i}. {accent}{val:<16}{reset} {muted}{desc}{reset}")
    say(f"  {muted}↵ Enter aceita '{default}' >{reset} ", end="")
    raw = input().strip()
    if not raw:
        return default
    if raw.isdigit():
        idx = int(raw) - 1
        if 0 <= idx < len(choices):
            return choices[idx][0]
    for val, _ in choices:
        if val.lower() == raw.lower():
            return val
    return default


def ask_yes_no(
    prompt: str,
    default: bool = False,
    step: int | None = None,
    total: int | None = None,
    hint: str | None = None,
) -> bool:
    """Pergunta sim/não com contador e hint opcionais (TUI-REDESIGN-25-05)."""
    accent = ANSI_ACCENT_FG
    bold = ANSI_BOLD
    muted = ANSI_DIM
    reset = ANSI_RESET
    if step is not None and total is not None:
        header = f"{step:02d}/{total:02d} · {prompt}"
    else:
        header = prompt
    say()
    say(f"  {accent}{bold}{header}{reset}")
    if hint:
        say(f"  {muted}{hint}{reset}")
    suffix = "[S/n]" if default else "[s/N]"
    default_label = "sim" if default else "nao"
    say(f"  {muted}↵ Enter aceita '{default_label}' {suffix} >{reset} ", end="")
    raw = input().strip().lower()
    if not raw:
        return default
    return raw in ("s", "sim", "y", "yes")


def render_summary(cfg: dict) -> None:
    """Renderiza summary card com box drawing antes de salvar (TUI-REDESIGN-25-05)."""
    accent = ANSI_ACCENT_FG
    muted = ANSI_DIM
    reset = ANSI_RESET
    say()
    say(f"  {accent}╭─ resumo ─────────────────────────────╮{reset}")
    for k, v in cfg.items():
        v_render = "sim" if v is True else ("não" if v is False else str(v))
        say(f"  {accent}│{reset}  {accent}{k:<14}{reset} = {v_render}")
    say(f"  {accent}╰──────────────────────────────────────╯{reset}")
    say()


def write_config(cfg: dict) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# ~/.nyx/config.toml (gerado por scripts/menu_wizard.py)", ""]
    for k, v in cfg.items():
        if isinstance(v, bool):
            v_s = "true" if v else "false"
        elif isinstance(v, (int, float)):
            v_s = str(v)
        else:
            v_s = f'"{v}"'
        lines.append(f"{k} = {v_s}")
    CONFIG_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def emit_env_exports(cfg: dict) -> None:
    """Imprime export VAR=valor numa linha por var pro run.sh source-ar."""
    if cfg.get("aesthetic") and cfg["aesthetic"] != "default":
        print(f'export NYX_AESTHETIC="{cfg["aesthetic"]}"')
    if cfg.get("entity") and cfg["entity"] != "nyx":
        print(f'export NYX_ENTITY="{cfg["entity"]}"')
    if cfg.get("schema") and cfg["schema"] != "hybrid":
        print(f'export NYX_SCHEMA="{cfg["schema"]}"')
    if cfg.get("banner_mode") and cfg["banner_mode"] != "wide":
        print(f'export NYX_BANNER_MODE="{cfg["banner_mode"]}"')
    if cfg.get("model"):
        print(f'export NYX_MODEL="{cfg["model"]}"')
    if cfg.get("auto_approve"):
        print('export NYX_AUTO_APPROVE=1')


def main() -> int:
    banner()
    cfg = {}

    # TUI-REDESIGN-25-05: contador XX/YY + hint contextual em cada passo.
    # Total = 6 passos após TUI-REDESIGN-25-16 ampliar com schema.
    TOTAL_STEPS = 6

    cfg["aesthetic"] = ask(
        "Aesthetic visual",
        [
            ("default", "paleta D canônica (turquesa + roxo)"),
            ("arcano", "noite violeta com glow"),
            ("cyberpunk", "neon saturado + scanlines"),
            ("brutalist", "papel branco, tinta preta"),
            ("mecha", "HUD âmbar"),
            ("editorial", "papel creme, serif"),
        ],
        default="default",
        step=1, total=TOTAL_STEPS,
        hint="Cor base do tema (bg, ink, accent, glyphs).",
    )

    cfg["entity"] = ask(
        "Entidade (sobrescreve accent + glow)",
        [
            ("nyx", "turquesa  #00D4AA"),
            ("eris", "rosa      #FF79C6"),
            ("juno", "verde     #A4CB58"),
            ("lars", "matrix    #50FA7B"),
            ("luna", "violeta   #BD93F9"),
            ("mars", "vermelho  #FF5555"),
            ("somn", "ciano     #8BE9FD"),
        ],
        default="nyx",
        step=2, total=TOTAL_STEPS,
        hint="Apenas accent + glow; aesthetic permanece como base.",
    )

    cfg["schema"] = ask(
        "Schema de interface (estrutura e layout)",
        [
            ("hybrid", "padrão -- soft-box + side-rule (Dracula refinada)"),
            ("editorial", "sentence-case + header bar + inline tools"),
            ("arcano", "ornament-box + glow bar + ornament chips"),
            ("brutalist", "CAIXA ALTA + bracket labels + table rows"),
        ],
        default="hybrid",
        step=3, total=TOTAL_STEPS,
        hint="Estrutura: prefixes, bubbles, divisores (ortogonal à cor).",
    )

    cfg["banner_mode"] = ask(
        "Banner",
        [
            ("wide", "3 linhas, ADR-029 (padrão)"),
            ("compact", "1 linha mínima"),
            ("neofetch", "info-rich estilo neofetch"),
        ],
        default="wide",
        step=4, total=TOTAL_STEPS,
        hint="Forma do header impresso no boot do REPL.",
    )

    cfg["model"] = ask(
        "Modelo Ollama",
        [
            ("qwen2.5-coder:3b", "padrão -- rápido, PT-BR 100%, ~2GB VRAM"),
            ("qwen3:4b", "thinking -- pode degradar PT-BR; usar --4b"),
            ("qwen2.5-coder:7b", "qualidade maior, ~3GB VRAM, P95 alto"),
        ],
        default="qwen2.5-coder:3b",
        step=5, total=TOTAL_STEPS,
        hint="Tradeoff VRAM × latência × qualidade.",
    )

    cfg["auto_approve"] = ask_yes_no(
        "Auto-aprovar permissões CONFIRM_ONCE (modo automação)?",
        default=False,
        step=6, total=TOTAL_STEPS,
        hint="Auto-aprovar tools de nível CONFIRM_ONCE; aprovação manual permanece para níveis acima.",
    )

    render_summary(cfg)

    if ask_yes_no("Salvar em ~/.nyx/config.toml e inicializar?", default=True):
        write_config(cfg)
        say(f"  {ANSI_SUCCESS_FG}configuração salva.{ANSI_RESET}")
        # stdout reservado para exports VAR=valor (run.sh source-a)
        if os.environ.get("NYX_MENU_EMIT") == "1":
            emit_env_exports(cfg)
        return 0
    say(f"  {ANSI_DIM}configuração descartada.{ANSI_RESET}")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        say()
        say(f"  {ANSI_DIM}/menu cancelado{ANSI_RESET}")
        sys.exit(2)
