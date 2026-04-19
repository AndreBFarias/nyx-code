"""WebFetch -- Busca conteúdo de uma URL e converte para texto.

Busca conteúdo de URLs e converte HTML para texto legível.
Usa httpx + html2text. 100% local, sem LLM intermediário.
"""

from __future__ import annotations

import time
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.services.logging_service import get_logger
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = get_logger("nyx.tools.web_fetch")

FETCH_TIMEOUT = 30
MAX_CONTENT_BYTES = 100_000
MAX_OUTPUT_CHARS = 20_000


class WebFetchTool(RegisteredTool):
    action_type = ActionType.WEB_FETCH

    tool_def = ToolDef(
        name="web_fetch",
        description=(
            "Busca conteúdo de uma URL e retorna como texto/markdown. "
            "Funciona com páginas HTML, APIs JSON e texto puro. "
            "Não funciona com URLs autenticadas ou conteúdo binário pesado."
        ),
        parameters={
            "url": {"type": "string", "description": "URL para buscar conteúdo"},
            "prompt": {
                "type": "string",
                "description": "Instrução sobre o que extrair do conteúdo (opcional)",
            },
        },
        required=["url"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        url = str(params.get("url", "")).strip()
        if not url:
            return ActionResult(success=False, error="URL vazia")

        if not url.startswith(("http://", "https://")):
            return ActionResult(success=False, error=f"URL inválida: {url}")

        try:
            import httpx
        except ImportError:
            return ActionResult(success=False, error="httpx não instalado")

        start = time.monotonic()

        try:
            with httpx.Client(
                timeout=FETCH_TIMEOUT,
                follow_redirects=True,
                headers={"User-Agent": "Nyx/1.0 (code-agent; local-first)"},
            ) as client:
                response = client.get(url)

            elapsed = time.monotonic() - start
            content_type = response.headers.get("content-type", "")
            raw_bytes = len(response.content)

            if response.status_code >= 400:
                return ActionResult(
                    success=False,
                    error=f"HTTP {response.status_code} ao buscar {url}",
                )

            if raw_bytes > MAX_CONTENT_BYTES:
                logger.warning("Conteúdo muito grande: %d bytes, truncando", raw_bytes)

            raw_text = response.text[:MAX_CONTENT_BYTES]

            if "text/html" in content_type:
                text = _html_to_text(raw_text)
            elif "application/json" in content_type:
                text = raw_text
            else:
                text = raw_text

            if len(text) > MAX_OUTPUT_CHARS:
                text = text[:MAX_OUTPUT_CHARS] + "\n\n[... conteúdo truncado]"

            summary = (
                f"URL: {url}\n"
                f"Status: {response.status_code}\n"
                f"Tipo: {content_type.split(';')[0]}\n"
                f"Tamanho: {raw_bytes} bytes\n"
                f"Tempo: {elapsed:.1f}s\n\n"
                f"{text}"
            )

            logger.info("Fetch OK: %s (%d bytes, %.1fs)", url, raw_bytes, elapsed)
            return ActionResult(success=True, output=summary)

        except httpx.TimeoutException:
            return ActionResult(success=False, error=f"Timeout ({FETCH_TIMEOUT}s) ao buscar {url}")
        except httpx.ConnectError:
            return ActionResult(success=False, error=f"Conexão recusada: {url}")
        except Exception as e:
            return ActionResult(success=False, error=f"Erro ao buscar {url}: {e}")


def _html_to_text(html: str) -> str:
    """Converte HTML para texto legível."""
    try:
        import html2text

        h = html2text.HTML2Text()
        h.ignore_links = False
        h.ignore_images = True
        h.ignore_emphasis = False
        h.body_width = 0
        return h.handle(html)
    except ImportError:
        import re

        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text


# "A rede é o computador." -- John Gage
