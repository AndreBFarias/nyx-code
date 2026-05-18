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
    say(f"  {ANSI_DIM}configure antes de bootar (Enter aceita default){reset}")
    say()


def ask(prompt: str, choices: list[tuple[str, str]], default: str) -> str:
    """Mostra choices numeradas; aceita numero ou Enter pro default.

    choices: lista de (valor, descricao).
    """
    accent = ANSI_ACCENT_FG
    success = ANSI_SUCCESS_FG
    muted = ANSI_DIM
    reset = ANSI_RESET
    say(f"  {accent}{prompt}{reset}")
    for i, (val, desc) in enumerate(choices, start=1):
        marker = f"{success}*{reset}" if val == default else " "
        say(f"    {marker} {i}. {accent}{val:<16}{reset} {muted}{desc}{reset}")
    say(f"  {muted}[Enter = {default}] >{reset} ", end="")
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
    say(f"  {accent}{prompt}{reset} {muted}{suffix}>{reset} ", end="")
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

    say()
    say(f"  {ANSI_DIM}Configuracao escolhida:{ANSI_RESET}")
    for k, v in cfg.items():
        say(f"    {ANSI_ACCENT_FG}{k:<14}{ANSI_RESET} = {v}")
    say()

    if ask_yes_no("Salvar em ~/.nyx/config.toml e bootar?", default=True):
        write_config(cfg)
        say(f"  {ANSI_SUCCESS_FG}configuracao salva.{ANSI_RESET}")
        # stdout reservado para exports VAR=valor (run.sh source-a)
        if os.environ.get("NYX_MENU_EMIT") == "1":
            emit_env_exports(cfg)
        return 0
    say(f"  {ANSI_DIM}configuracao descartada.{ANSI_RESET}")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        say()
        say(f"  {ANSI_DIM}/menu cancelado{ANSI_RESET}")
        sys.exit(2)
