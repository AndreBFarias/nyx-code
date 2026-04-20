"""Configuração centralizada do Nyx-Code via .env e argumentos CLI."""

from __future__ import annotations

import os
from dataclasses import dataclass
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

    @property
    def ollama_base_url(self) -> str:
        return f"http://{self.ollama_host}:{self.ollama_port}"

    @property
    def proxy_url(self) -> str:
        return f"http://{self.ollama_host}:{self.proxy_port}"

    @property
    def proxy_v1_url(self) -> str:
        return f"{self.proxy_url}/v1"

    @property
    def num_gpu(self) -> int:
        if "7b" in self.model:
            return defaults.NUM_GPU_7B
        return defaults.NUM_GPU_3B


def load_settings(args: Any = None) -> NyxSettings:
    """Carrega configurações do .env + argumentos CLI."""
    project_root = Path(__file__).resolve().parent.parent.parent
    env_path = project_root / ".env"

    if env_path.exists():
        load_dotenv(env_path)

    model = defaults.DEFAULT_MODEL
    port = int(os.getenv("NYX_OLLAMA_PORT", str(defaults.OLLAMA_PORT)))
    proxy_port = int(os.getenv("NYX_PROXY_PORT", str(defaults.PROXY_PORT)))
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
    )


# "A liberdade é o reconhecimento da necessidade." -- Friedrich Engels
