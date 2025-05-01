"""OllamaProvider -- Encapsula comunicação com o proxy/Ollama."""

from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger("nyx.providers.ollama")

DEFAULT_TIMEOUT = 300
MAX_RETRIES = 2
RETRY_BACKOFF = 1.5


class OllamaProvider:
    def __init__(self, proxy_url: str = "http://127.0.0.1:11436",
                 timeout: int = DEFAULT_TIMEOUT) -> None:
        self._url = proxy_url.rstrip("/")
        self._timeout = timeout

    async def chat(self, messages: list[dict], model: str = "qwen3:4b",
                   tools: list[dict] | None = None,
                   stream: bool = False) -> dict[str, Any]:
        """Envia request de chat. Retorna resposta formatada."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools

        last_error = ""
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    r = await client.post(
                        f"{self._url}/v1/chat/completions",
                        json=payload,
                    )
                    data = r.json()

                if "choices" not in data:
                    return {"error": f"Resposta sem choices: {str(data)[:200]}"}

                msg = data["choices"][0]["message"]
                return {
                    "content": msg.get("content", ""),
                    "tool_calls": msg.get("tool_calls", []),
                    "usage": data.get("usage", {}),
                    "finish_reason": data["choices"][0].get("finish_reason", ""),
                }

            except httpx.TimeoutException:
                last_error = "Timeout"
            except httpx.ConnectError:
                last_error = "Conexão recusada"
            except Exception as e:
                last_error = str(e)

            if attempt < MAX_RETRIES:
                import asyncio
                await asyncio.sleep(RETRY_BACKOFF * (attempt + 1))

        return {"error": f"Falha após {MAX_RETRIES + 1} tentativas: {last_error}"}

    async def health(self) -> bool:
        """Verifica se proxy/Ollama responde."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self._url}/v1/models")
                return r.status_code == 200
        except Exception:
            return False

    async def models(self) -> list[str]:
        """Lista modelos disponíveis."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self._url}/v1/models")
                data = r.json()
                return [m.get("id", "") for m in data.get("data", [])]
        except Exception:
            return []


# "A abstração é a essência da engenharia." -- Edsger Dijkstra
