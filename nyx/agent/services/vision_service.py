"""VisionService — fachada de descrição de imagens com cache.

Cache: ~/.nyx/vision_cache/<sha256>.txt
Fallback claro se moondream ausente. Veja ADR-022.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from nyx.agent.services.logging_service import get_logger
from nyx.providers.vision_client import VisionClient

logger = get_logger("nyx.services.vision")

CACHE_DIR = Path.home() / ".nyx" / "vision_cache"


class VisionService:
    def __init__(self, client: VisionClient | None = None) -> None:
        self._client = client or VisionClient()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def is_available(self) -> bool:
        return self._client.is_model_available()

    def describe(
        self,
        image_path: Path,
        prompt: str = "Describe this image in detail.",
    ) -> str:
        """Retorna descrição. Usa cache por sha256 do arquivo + prompt.

        Se moondream não disponível, retorna string-sentinela
        '[Imagem: visão indisponível — rode `./install.sh --vision`]'.
        """
        if not image_path.is_file():
            return f"[Imagem: arquivo não encontrado ({image_path})]"

        digest = self._digest(image_path, prompt)
        cache_file = CACHE_DIR / f"{digest}.txt"
        if cache_file.exists():
            logger.debug("vision cache hit: %s", digest[:8])
            return cache_file.read_text(encoding="utf-8")

        if not self.is_available():
            return "[Imagem: visão indisponível — rode `./install.sh --vision`]"

        try:
            desc = self._client.describe_image(image_path, prompt).strip()
            if desc:
                cache_file.write_text(desc, encoding="utf-8")
            return desc or "[Imagem: descrição vazia]"
        except Exception as e:  # noqa: BLE001 -- VisionClient pode levantar tipos diversos
            logger.warning("vision: descrição falhou (%s)", e)
            return f"[Imagem: erro ao descrever ({type(e).__name__})]"

    def describe_many(
        self,
        paths: list[Path],
        prompt: str = "Describe this image in detail.",
    ) -> list[str]:
        """Descreve múltiplas imagens sequencialmente (VISION-02).

        Paralelizar não acelera: moondream é CPU-bound e satura núcleos.
        Cache torna chamadas repetidas instantâneas.
        """
        return [self.describe(p, prompt) for p in paths]

    @staticmethod
    def _digest(path: Path, prompt: str) -> str:
        h = hashlib.sha256()
        h.update(path.read_bytes())
        h.update(b"||")
        h.update(prompt.encode("utf-8"))
        return h.hexdigest()
