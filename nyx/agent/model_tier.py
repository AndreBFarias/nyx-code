"""ModelTier -- Configuração por hardware para o Nyx Agent.

Port de Luna src/skills/code_agent/model_tier.py.
Auto-detecta GPU via nvidia-smi e seleciona o perfil adequado.

3 perfis:
  COMPACT (<4GB): num_gpu=8, num_ctx=4096, max_iterations=15
  STANDARD (4-8GB): num_gpu=12, num_ctx=8192, max_iterations=30
  POWER (8GB+): num_gpu=-1, num_ctx=32768, max_iterations=50
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from enum import Enum

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.tier")


class HardwareProfile(Enum):
    COMPACT = "compact"
    STANDARD = "standard"
    POWER = "power"


@dataclass(frozen=True)
class ModelTier:
    model_name: str
    hardware_profile: HardwareProfile

    num_gpu: int = -1
    num_ctx: int = 4096
    max_iterations: int = 15
    temperature: float = 0.3

    force_done_threshold: int = 1
    prompt_strategy: str = "compact"
    max_system_chars: int = 600
    supports_multi_step: bool = False
    supports_nothink: bool = True

    gpu_name: str = "CPU-only"
    vram_total_mib: int = 0


def detect_hardware_profile() -> tuple[HardwareProfile, str, int]:
    """Detecta GPU e retorna (perfil, nome_gpu, vram_mib)."""
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            text=True,
            timeout=5,
        ).strip()
        parts = out.split(",")
        gpu_name = parts[0].strip()
        vram_mib = int(parts[1].strip())

        if vram_mib >= 8000:
            return HardwareProfile.POWER, gpu_name, vram_mib
        if vram_mib >= 4000:
            return HardwareProfile.STANDARD, gpu_name, vram_mib
        return HardwareProfile.COMPACT, gpu_name, vram_mib
    except Exception as e:
        logger.debug("GPU não detectada: %s", e)
        return HardwareProfile.COMPACT, "CPU-only", 0


def get_model_tier(model: str = "qwen3:4b") -> ModelTier:
    """Retorna tier baseado no hardware detectado."""
    profile, gpu_name, vram_mib = detect_hardware_profile()

    if profile == HardwareProfile.POWER:
        tier = ModelTier(
            model_name=model,
            hardware_profile=profile,
            num_gpu=-1,
            num_ctx=32768,
            max_iterations=50,
            temperature=0.2,
            force_done_threshold=3,
            prompt_strategy="rich",
            max_system_chars=2400,
            supports_multi_step=True,
            gpu_name=gpu_name,
            vram_total_mib=vram_mib,
        )
    elif profile == HardwareProfile.STANDARD:
        tier = ModelTier(
            model_name=model,
            hardware_profile=profile,
            num_gpu=12,
            num_ctx=8192,
            max_iterations=30,
            temperature=0.3,
            force_done_threshold=2,
            prompt_strategy="standard",
            max_system_chars=1200,
            supports_multi_step=True,
            gpu_name=gpu_name,
            vram_total_mib=vram_mib,
        )
    else:
        tier = ModelTier(
            model_name=model,
            hardware_profile=profile,
            num_gpu=8,
            num_ctx=4096,
            max_iterations=15,
            temperature=0.3,
            force_done_threshold=1,
            prompt_strategy="compact",
            max_system_chars=600,
            supports_multi_step=False,
            gpu_name=gpu_name,
            vram_total_mib=vram_mib,
        )

    logger.info(
        "[TIER] %s -> %s (num_gpu=%d, num_ctx=%d, vram=%dMiB)",
        profile.value,
        model,
        tier.num_gpu,
        tier.num_ctx,
        vram_mib,
    )
    return tier


# "Abstrações devem ser descobertas, não inventadas." -- Ralph Johnson
