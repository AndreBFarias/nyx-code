"""WebSearch -- Busca na web via DuckDuckGo + Wikipedia.

Port de Luna src/tools/web_search/ adaptado para o Nyx.
Fontes: DuckDuckGo (primário), Wikipedia PT/EN (fallback).
100% local, sem API cloud.

Requer: pip install ddgs
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

from nyx.agent.models import ActionResult, ActionType
from nyx.agent.tools.base import RegisteredTool, ToolDef

logger = logging.getLogger("nyx.tools.web_search")

SEARCH_TIMEOUT = 15
MAX_RESULTS_DEFAULT = 8
RATE_LIMIT_INTERVAL = 2.5
CACHE_TTL = 3600
MAX_CACHE = 100

_NON_LATIN = re.compile(
    r"[\u0400-\u04FF\u0E00-\u0E7F\u4E00-\u9FFF"
    r"\u3040-\u30FF\u0600-\u06FF\u0900-\u097F\uAC00-\uD7AF]",
)


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    timestamp: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class WebSearchEngine:
    """Motor de busca com DuckDuckGo + Wikipedia fallback."""

    WIKIPEDIA_API = "https://pt.wikipedia.org/w/api.php"

    def __init__(self) -> None:
        self._cache: dict[str, tuple[list[SearchResult], float]] = {}
        self._last_request = 0.0
        self._ddg_available = self._check_ddg()
        logger.info("WebSearch: DuckDuckGo=%s", self._ddg_available)

    def _check_ddg(self) -> bool:
        try:
            from ddgs import DDGS
            return True
        except ImportError:
            try:
                from duckduckgo_search import DDGS
                return True
            except ImportError:
                logger.warning("ddgs não instalado. Execute: pip install ddgs")
                return False

    def search(self, query: str, max_results: int = MAX_RESULTS_DEFAULT) -> list[SearchResult]:
        if not query or not query.strip():
            return []

        cache_key = hashlib.md5(query.lower().strip().encode(), usedforsecurity=False).hexdigest()[:16]
        if cache_key in self._cache:
            results, ts = self._cache[cache_key]
            if time.time() - ts < CACHE_TTL:
                logger.info("Cache hit: '%s'", query[:30])
                return results

        all_results: list[SearchResult] = []

        if self._ddg_available:
            ddg = self._search_ddg(query, max_results)
            all_results.extend(ddg)

        if len(all_results) < max_results // 2:
            wiki = self._search_wikipedia(query, max_results=4)
            for w in wiki:
                if not any(r.title == w.title for r in all_results):
                    all_results.append(w)

        results = all_results[:max_results]

        if results:
            if len(self._cache) >= MAX_CACHE:
                oldest = min(self._cache, key=lambda k: self._cache[k][1])
                del self._cache[oldest]
            self._cache[cache_key] = (results, time.time())

        return results

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request
        if elapsed < RATE_LIMIT_INTERVAL:
            time.sleep(RATE_LIMIT_INTERVAL - elapsed)
        self._last_request = time.time()

    def _search_ddg(self, query: str, max_results: int) -> list[SearchResult]:
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            self._rate_limit()

            for region in ["br-pt", "wt-wt"]:
                try:
                    with DDGS() as ddgs:
                        raw = list(ddgs.text(query, region=region, safesearch="off", max_results=max_results))
                    if raw:
                        break
                except Exception as e:
                    logger.debug("Falha na busca DuckDuckGo região %s: %s", region, e)
                    continue
            else:
                return []

            results = []
            for r in raw:
                title = r.get("title", "")
                snippet = r.get("body", r.get("snippet", ""))
                if _NON_LATIN.search(title or "") and len(_NON_LATIN.findall(title)) > len(title) * 0.15:
                    continue
                results.append(SearchResult(
                    title=title,
                    url=r.get("href", r.get("link", "")),
                    snippet=(snippet or "")[:300],
                    source="duckduckgo",
                    timestamp=time.time(),
                ))

            logger.info("DuckDuckGo: %d resultados para '%s'", len(results), query[:30])
            return results

        except Exception as e:
            logger.error("Erro DuckDuckGo: %s", e)
            return []

    def _search_wikipedia(self, query: str, max_results: int = 3) -> list[SearchResult]:
        try:
            import httpx

            params = {
                "action": "query",
                "list": "search",
                "srsearch": query,
                "srlimit": max_results,
                "format": "json",
                "utf8": 1,
            }
            headers = {
                "User-Agent": "Nyx/1.0 (code-agent; local-first)",
                "Accept": "application/json",
            }

            with httpx.Client(timeout=10) as client:
                resp = client.get(self.WIKIPEDIA_API, params=params, headers=headers)

            if resp.status_code != 200:
                return []

            data = resp.json()
            search_results = data.get("query", {}).get("search", [])

            results = []
            for item in search_results:
                title = item.get("title", "")
                snippet = re.sub(r"<[^>]+>", "", item.get("snippet", ""))
                results.append(SearchResult(
                    title=f"Wikipedia: {title}",
                    url=f"https://pt.wikipedia.org/wiki/{title.replace(' ', '_')}",
                    snippet=snippet[:300],
                    source="wikipedia",
                    timestamp=time.time(),
                ))

            if results:
                logger.info("Wikipedia: %d resultados", len(results))
            return results

        except Exception as e:
            logger.debug("Wikipedia falhou: %s", e)
            return []

    def format_results(self, results: list[SearchResult], max_chars: int = 4000) -> str:
        if not results:
            return "Nenhum resultado encontrado."

        lines = [f"[Busca web - {datetime.now().strftime('%d/%m/%Y %H:%M')}]"]
        char_count = len(lines[0])

        for i, r in enumerate(results, 1):
            entry = f"\n{i}. {r.title}\n   {r.snippet}\n   {r.url}"
            if char_count + len(entry) > max_chars:
                lines.append("\n[... mais resultados omitidos]")
                break
            lines.append(entry)
            char_count += len(entry)

        return "\n".join(lines)


_engine: WebSearchEngine | None = None


def _get_engine() -> WebSearchEngine:
    global _engine
    if _engine is None:
        _engine = WebSearchEngine()
    return _engine


class WebSearchTool(RegisteredTool):
    action_type = ActionType.SEARCH

    tool_def = ToolDef(
        name="web_search",
        description=(
            "Busca na web usando DuckDuckGo e Wikipedia. "
            "Retorna títulos, URLs e trechos dos resultados. "
            "Use para buscar informações atuais, documentação, "
            "ou qualquer dado que não esteja no projeto local."
        ),
        parameters={
            "query": {"type": "string", "description": "Termo de busca"},
            "max_results": {
                "type": "integer",
                "description": "Número máximo de resultados (padrão: 8)",
            },
        },
        required=["query"],
    )

    def execute(self, params: dict[str, Any], project_root: str) -> ActionResult:
        query = str(params.get("query", "")).strip()
        if not query:
            return ActionResult(success=False, error="Query vazia")

        max_results = int(params.get("max_results", MAX_RESULTS_DEFAULT))

        engine = _get_engine()
        results = engine.search(query, max_results=max_results)

        if not results:
            return ActionResult(
                success=True,
                output=f"Nenhum resultado encontrado para: {query}",
            )

        formatted = engine.format_results(results)
        logger.info("WebSearch: %d resultados para '%s'", len(results), query[:30])
        return ActionResult(success=True, output=formatted)


# "Quem controla a informação controla o mundo." -- Napoleão Bonaparte
