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

from nyx.themes.design_tokens import (
    ANSI_ACCENT_FG, ANSI_BOLD, ANSI_DIM, ANSI_PRIMARY_FG,
    ANSI_RESET, ANSI_SUCCESS_FG,
)

CONFIG_PATH = Path.home() / ".nyx" / "config.toml"


def banner() -> None:
    bold = ANSI_BOLD
    accent = ANSI_ACCENT_FG
    reset = ANSI_RESET
    print()
    print(f"  {bold}{accent}Nyx{reset} {ANSI_DIM}cockpit / menu{reset}")
    print(f"  {ANSI_DIM}configure antes de bootar (Enter aceita default){reset}")
    print()


def ask(prompt: str, choices: list[tuple[str, str]], default: str) -> str:
    """Mostra choices numeradas; aceita numero ou Enter pro default.

    choices: lista de (valor, descricao).
    """
    accent = ANSI_ACCENT_FG
    success = ANSI_SUCCESS_FG
    muted = ANSI_DIM
    reset = ANSI_RESET
    print(f"  {accent}{prompt}{reset}")
    for i, (val, desc) in enumerate(choices, start=1):
        marker = f"{success}*{reset}" if val == default else " "
        print(f"    {marker} {i}. {accent}{val:<16}{reset} {muted}{desc}{reset}")
    print(f"  {muted}[Enter = {default}] >{reset} ", end="", flush=True)
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


def ask_yes_no(prompt: str, default: bool = False) -> bool:
    muted = ANSI_DIM
    reset = ANSI_RESET
    accent = ANSI_ACCENT_FG
    suffix = "[S/n]" if default else "[s/N]"
    print(f"  {accent}{prompt}{reset} {muted}{suffix}>{reset} ", end="", flush=True)
    raw = input().strip().lower()
    if not raw:
        return default
    return raw in ("s", "sim", "y", "yes")


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
    if cfg.get("banner_mode") and cfg["banner_mode"] != "wide":
        print(f'export NYX_BANNER_MODE="{cfg["banner_mode"]}"')
    if cfg.get("model"):
        print(f'export NYX_MODEL="{cfg["model"]}"')
    if cfg.get("auto_approve"):
        print('export NYX_AUTO_APPROVE=1')


def main() -> int:
    banner()
    cfg = {}

    cfg["aesthetic"] = ask(
        "Aesthetic visual",
        [
            ("default", "paleta D canonica (turquesa + roxo)"),
            ("arcano", "noite violeta com glow"),
            ("cyberpunk", "neon saturado + scanlines"),
            ("brutalist", "papel branco, tinta preta"),
            ("mecha", "HUD ambar"),
            ("editorial", "papel creme, serif"),
        ],
        default="default",
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
    )

    cfg["banner_mode"] = ask(
        "Banner",
        [
            ("wide", "3 linhas, ADR-029 (padrao)"),
            ("compact", "1 linha mínima"),
            ("neofetch", "info-rich estilo neofetch"),
        ],
        default="wide",
    )

    cfg["model"] = ask(
        "Modelo Ollama",
        [
            ("qwen2.5-coder:3b", "padrao -- rapido, PT-BR 100%, ~2GB VRAM"),
            ("qwen3:4b", "thinking -- pode degradar PT-BR; usar --4b"),
            ("qwen2.5-coder:7b", "qualidade maior, ~3GB VRAM, P95 alto"),
        ],
        default="qwen2.5-coder:3b",
    )

    cfg["auto_approve"] = ask_yes_no(
        "Auto-aprovar permissoes CONFIRM_ONCE (modo automacao)?",
        default=False,
    )

    print()
    print(f"  {ANSI_DIM}Configuracao escolhida:{ANSI_RESET}")
    for k, v in cfg.items():
        print(f"    {ANSI_ACCENT_FG}{k:<14}{ANSI_RESET} = {v}")
    print()

    if ask_yes_no("Salvar em ~/.nyx/config.toml e bootar?", default=True):
        write_config(cfg)
        print(f"  {ANSI_SUCCESS_FG}configuracao salva.{ANSI_RESET}")
        # Emite exports para o run.sh source-ar via process substitution
        if os.environ.get("NYX_MENU_EMIT") == "1":
            emit_env_exports(cfg)
        return 0
    print(f"  {ANSI_DIM}configuracao descartada.{ANSI_RESET}")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print()
        print(f"  {ANSI_DIM}/menu cancelado{ANSI_RESET}")
        sys.exit(2)
