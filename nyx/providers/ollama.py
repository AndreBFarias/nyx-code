"""OllamaProvider -- Encapsula comunicação com o proxy/Ollama."""

from __future__ import annotations

from typing import Any

import httpx

from nyx.agent.services.logging_service import get_logger
from nyx.config.defaults import DEFAULT_MODEL as _DEFAULT_MODEL
from nyx.config.defaults import PROXY_URL as _DEFAULT_PROXY_URL
from nyx.providers.base import ProviderError

logger = get_logger("nyx.providers.ollama")

DEFAULT_TIMEOUT = 300
MAX_RETRIES = 2
RETRY_BACKOFF = 1.5


class OllamaProvider:
    def __init__(self, proxy_url: str = _DEFAULT_PROXY_URL, timeout: int = DEFAULT_TIMEOUT) -> None:
        self._url = proxy_url.rstrip("/")
        self._timeout = timeout

    async def chat(
        self, messages: list[dict], model: str = _DEFAULT_MODEL, tools: list[dict] | None = None, stream: bool = False
    ) -> dict[str, Any]:
        """Envia request de chat. Retorna resposta formatada."""
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }
        if tools:
            payload["tools"] = tools

        last_cause: BaseException | None = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                async with httpx.AsyncClient(timeout=self._timeout) as client:
                    r = await client.post(
                        f"{self._url}/v1/chat/completions",
                        json=payload,
                    )
                    data = r.json()

                if "choices" not in data:
                    raise ProviderError(
                        user_message="Resposta do proxy sem campo 'choices'.",
                        hint="Reinicie o proxy com ./run.sh ou inspecione ~/.nyx/logs/proxy.log.",
                        cause=RuntimeError(str(data)[:200]),
                    )

                msg = data["choices"][0]["message"]
                return {
                    "content": msg.get("content", ""),
                    "tool_calls": msg.get("tool_calls", []),
                    "usage": data.get("usage", {}),
                    "finish_reason": data["choices"][0].get("finish_reason", ""),
                }

            except ProviderError:
                raise
            except httpx.TimeoutException as e:
                last_cause = e
            except httpx.ConnectError as e:
                last_cause = e
            except Exception as e:
                last_cause = e

            if attempt < MAX_RETRIES:
                import asyncio

                await asyncio.sleep(RETRY_BACKOFF * (attempt + 1))

        if isinstance(last_cause, httpx.TimeoutException):
            raise ProviderError(
                user_message=f"Ollama não respondeu em {self._timeout}s.",
                hint="Verifique se está rodando: systemctl status ollama",
                cause=last_cause,
            )
        if isinstance(last_cause, httpx.ConnectError):
            raise ProviderError(
                user_message=f"Conexão recusada com o proxy em {self._url}.",
                hint="Reinicie com ./run.sh ou confira a porta com ss -ltnp | grep 1143",
                cause=last_cause,
            )
        raise ProviderError(
            user_message=f"Falha após {MAX_RETRIES + 1} tentativas de chat com o proxy.",
            hint="Consulte ~/.nyx/logs/nyx.log para o traceback completo.",
            cause=last_cause,
        )

    async def health(self) -> bool:
        """Verifica se proxy/Ollama responde."""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                r = await client.get(f"{self._url}/v1/models")
                return r.status_code == 200
        except Exception as e:
            logger.debug("Health check falhou: %s", e)
            return False

    async def models(self) -> list[str]:
        """Lista modelos disponíveis."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(f"{self._url}/v1/models")
                data = r.json()
                return [m.get("id", "") for m in data.get("data", [])]
        except Exception as e:
            logger.debug("Falha ao listar modelos: %s", e)
            return []


# "A abstração é a essência da engenharia." -- Edsger Dijkstra
