"""Configuração centralizada do Nyx-Code via .env e argumentos CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from . import defaults


@dataclass
class NyxSettings:
    """Configurações do Nyx-Code."""

    project_root: Path
    ollama_host: str
    ollama_port: int
    proxy_port: int
    model: str
    vram_max_gb: float
    max_iterations: int
    temperature: float
    max_tokens: int
    num_ctx: int
    debug: bool
    headless: bool
    # PROJECT-ROOTS-MULTI-01: roots adicionais autorizados no boot.
    # Origem: env NYX_EXTRA_ROOTS (CSV) ou [extra_roots] em config.toml.
    # Lista vazia = só o project_root sandboxado (comportamento legado).
    extra_roots: list[Path] = field(default_factory=list)

    @property
    def ollama_base_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"

    @property
    def proxy_url(self) -> str:
        return f"http://{self.ollama_host}:{self.proxy_port}"

    @property
    def proxy_v1_url(self) -> str:
        return f"{self.proxy_url}/v1"


def _load_toml_overrides() -> dict[str, Any]:
    """ONBOARDING-01: lê ~/.nyx/config.toml se existir. Vazio em <3.11 ou erro."""
    import sys

    if sys.version_info < (3, 11):
        return {}
    try:
        import tomllib
    except ImportError:
        return {}
    path = Path.home() / ".nyx" / "config.toml"
    if not path.exists():
        return {}
    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception:  # noqa: BLE001 -- toml mal-formado não deve quebrar boot
        return {}


def load_settings(args: Any = None) -> NyxSettings:
    """Carrega configurações: env > ~/.nyx/config.toml > defaults (ONBOARDING-01)."""
    project_root = Path(__file__).resolve().parent.parent.parent
    env_path = project_root / ".env"

    if env_path.exists():
        load_dotenv(env_path)

    toml_cfg = _load_toml_overrides()

    model = os.getenv("NYX_MODEL") or toml_cfg.get("modelo") or defaults.DEFAULT_MODEL
    port_env = os.getenv("NYX_OLLAMA_PORT")
    port = int(port_env) if port_env else int(toml_cfg.get("ollama_port") or defaults.OLLAMA_PORT)
    proxy_port_env = os.getenv("NYX_PROXY_PORT")
    proxy_port = (
        int(proxy_port_env)
        if proxy_port_env
        else int(toml_cfg.get("proxy_port") or defaults.PROXY_PORT)
    )
    debug = os.getenv("NYX_DEBUG", "0") == "1"
    headless = False

    if args is not None:
        model = getattr(args, "model", model)
        port = getattr(args, "port", port)
        proxy_port = getattr(args, "proxy_port", proxy_port)
        debug = getattr(args, "debug", debug)
        headless = getattr(args, "headless", headless)

    raw_host = os.getenv("NYX_OLLAMA_HOST", defaults.OLLAMA_HOST)
    if ":" in raw_host:
        raise ValueError(
            f"NYX_OLLAMA_HOST deve ser host puro (sem porta), recebido '{raw_host}'. "
            "Use NYX_OLLAMA_PORT para a porta."
        )

    # PROJECT-ROOTS-MULTI-01: extra_roots vem de env NYX_EXTRA_ROOTS (CSV)
    # ou [extra_roots] no config.toml (lista). Env tem prioridade. Paths
    # inválidos são silenciosamente descartados (boot best-effort) com
    # warning visível pelo cli.py ao validar antes de adicionar ao sandbox.
    extra_roots: list[Path] = []
    raw_env = os.getenv("NYX_EXTRA_ROOTS", "").strip()
    if raw_env:
        for chunk in raw_env.split(","):
            cleaned = chunk.strip()
            if cleaned:
                extra_roots.append(Path(cleaned).expanduser())
    else:
        toml_extras = toml_cfg.get("extra_roots") or []
        if isinstance(toml_extras, list):
            for item in toml_extras:
                if isinstance(item, str) and item.strip():
                    extra_roots.append(Path(item.strip()).expanduser())

    return NyxSettings(
        project_root=project_root,
        ollama_host=raw_host,
        ollama_port=port,
        proxy_port=proxy_port,
        model=model,
        vram_max_gb=float(os.getenv("NYX_VRAM_MAX", str(defaults.VRAM_MAX_GB))),
        max_iterations=int(os.getenv("NYX_MAX_ITERATIONS", str(defaults.MAX_ITERATIONS))),
        temperature=float(os.getenv("NYX_TEMPERATURE", str(defaults.TEMPERATURE))),
        max_tokens=defaults.MAX_TOKENS,
        num_ctx=defaults.NUM_CTX,
        debug=debug,
        headless=headless,
        extra_roots=extra_roots,
    )


# "A liberdade é o reconhecimento da necessidade." -- Friedrich Engels
