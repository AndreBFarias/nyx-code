"""SessionSummarizer -- resumo vivo da sessão, gerado via LLM.

Chamado em batch (a cada N turnos) pra evitar overhead. O cliente HTTP é
isolado do AgentLoop principal (evita competir pelo proxy ou acionar o
próprio summarizer recursivamente via tools). Toda resposta é limitada a
um limite de chars. Se o LLM falhar, mantém o resumo anterior.
"""

from __future__ import annotations

from pathlib import Path

import httpx

from nyx.agent.services.logging_service import get_logger
from nyx.agent.session import CodeSession

logger = get_logger("nyx.summarizer")

DEFAULT_BATCH = 5
MAX_SUMMARY_CHARS = 3200
REQUEST_TIMEOUT = 180

SUMMARY_SYSTEM = (
    "Sou um resumidor. Recebo o histórico de uma sessão de programação "
    "e devolvo um resumo curto em PT-BR. Zero emojis. Zero verbosidade."
)

SUMMARY_INSTRUCTIONS = """Gere um resumo da sessão atual. Máximo 400 palavras. Apenas texto, sem código.
Use exatamente estas 4 seções (títulos em markdown ##):

## Objetivo
(1-2 frases: o que o usuário está tentando fazer)

## Decisões
(lista curta: escolhas que não devem ser refeitas)

## Arquivos
(lista curta: arquivos lidos ou modificados e para quê)

## Estado
(1-2 frases: onde parou, o que sobra)"""


class SessionSummarizer:
    """Gera e atualiza resumo de sessão via proxy LLM."""

    def __init__(
        self,
        proxy_url: str,
        model: str,
        batch_size: int = DEFAULT_BATCH,
    ) -> None:
        self._proxy_url = proxy_url.rstrip("/")
        self._model = model
        self._batch_size = batch_size

    def should_summarize(self, session: CodeSession) -> bool:
        last = getattr(session, "last_summarized_at", 0)
        return session.iteration > 0 and (session.iteration - last) >= self._batch_size

    def _build_transcript(self, session: CodeSession) -> str:
        """Converte histórico em transcript compacto para o summarizer ler."""
        lines: list[str] = []
        for entry in session.history[-40:]:
            if entry.role == "user":
                lines.append(f"USER: {entry.content[:300]}")
            elif entry.role == "assistant":
                if entry.content:
                    lines.append(f"NYX: {entry.content[:300]}")
            elif entry.role == "tool":
                result = (entry.tool_result or entry.content)[:200]
                args = str(entry.tool_args)[:80]
                lines.append(f"TOOL {entry.tool_name}({args}) -> {result}")
        return "\n".join(lines)

    async def update(self, session: CodeSession) -> str:
        """Chama o LLM e grava o resumo em `session.summary`. Retorna o texto."""
        transcript = self._build_transcript(session)
        if not transcript.strip():
            return session.summary if hasattr(session, "summary") else ""

        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SUMMARY_SYSTEM},
                {
                    "role": "user",
                    "content": f"{SUMMARY_INSTRUCTIONS}\n\n---\n{transcript}",
                },
            ],
            "tools": [],
            "stream": False,
        }

        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                r = await client.post(
                    f"{self._proxy_url}/v1/chat/completions",
                    json=payload,
                )
                data = r.json()
                content = data["choices"][0]["message"].get("content", "").strip()
        except (httpx.HTTPError, KeyError, IndexError, ValueError) as e:
            logger.warning("summarizer: falha no LLM (%s), mantendo resumo anterior", e)
            return getattr(session, "summary", "")

        if len(content) > MAX_SUMMARY_CHARS:
            content = content[:MAX_SUMMARY_CHARS] + "\n[... truncado]"

        session.summary = content
        session.last_summarized_at = session.iteration
        logger.info(
            "summarizer: resumo atualizado (%d chars, iteration=%d)",
            len(content),
            session.iteration,
        )
        return content

    @staticmethod
    def write_to_disk(session_id: str, summary: str) -> Path | None:
        """Espelha o resumo em ~/.nyx/sessions/<id>/summary.md pra o dev inspecionar."""
        if not summary.strip() or not session_id:
            return None
        path = Path.home() / ".nyx" / "sessions" / session_id / "summary.md"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(summary + "\n", encoding="utf-8")
        except OSError as e:
            logger.warning("Falha ao gravar summary.md: %s", e)
            return None
        return path


# "Quem não se lembra do passado está condenado a repeti-lo." -- Santayana
