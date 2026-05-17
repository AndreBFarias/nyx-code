"""VisionClient — wrapper HTTP para Ollama /api/generate com imagem.

Usa moondream em CPU (num_gpu=0). Não compete com o modelo de chat por VRAM.
Veja ADR-022.
"""

from __future__ import annotations

import base64
from pathlib import Path

import httpx

from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import OLLAMA_URL

logger = get_logger("nyx.providers.vision")

VISION_MODEL = "moondream"
REQUEST_TIMEOUT = 60
NUM_CTX_VISION = 2048


class VisionClient:
    def __init__(self, ollama_url: str = OLLAMA_URL, timeout: int = REQUEST_TIMEOUT) -> None:
        self._url = ollama_url.rstrip("/")
        self._timeout = timeout

    def describe_image(
        self,
        image_path: Path,
        prompt: str = "Describe this image in detail.",
    ) -> str:
        """Chama moondream com imagem base64. CPU only (num_gpu=0)."""
        if not image_path.is_file():
            raise FileNotFoundError(f"Imagem não encontrada: {image_path}")

        b64 = base64.b64encode(image_path.read_bytes()).decode("ascii")
        payload = {
            "model": VISION_MODEL,
            "prompt": prompt,
            "images": [b64],
            "stream": False,
            "options": {
                "num_gpu": 0,
                "num_ctx": NUM_CTX_VISION,
            },
        }
        try:
            with httpx.Client(timeout=self._timeout) as client:
                r = client.post(f"{self._url}/api/generate", json=payload)
                r.raise_for_status()
                data = r.json()
                return (data.get("response") or "").strip()
        except httpx.TimeoutException as e:
            logger.warning(
                "vision: timeout após %ds (CPU sobrecarregada ou modelo travado)",
                self._timeout,
            )
            raise TimeoutError(f"moondream não respondeu em {self._timeout}s") from e
        except httpx.HTTPError as e:
            logger.warning("vision: falha HTTP (%s)", e)
            raise
        except (KeyError, ValueError) as e:
            logger.warning("vision: resposta inesperada (%s)", e)
            raise

    def is_model_available(self) -> bool:
        """Consulta /api/tags e verifica se moondream está puxado."""
        try:
            with httpx.Client(timeout=5) as client:
                r = client.get(f"{self._url}/api/tags")
                if r.status_code != 200:
                    return False
                tags = r.json().get("models", [])
                return any(VISION_MODEL in (m.get("name") or "") for m in tags)
        except httpx.HTTPError:
            return False
