"""SessionMemory -- Persistência de memórias entre sessões.

Armazena decisões-chave, padrões observados e contexto
que deve sobreviver entre sessões do agent.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from nyx.agent.services.logging_service import get_logger

logger = get_logger("nyx.services.memory")

MEMORY_DIR = Path.home() / ".nyx" / "memory"


@dataclass
class Memory:
    key: str
    content: str
    tags: list[str] = field(default_factory=list)
    timestamp: float = 0.0
    session_id: str = ""


def _memory_file(session_id: str) -> Path:
    return MEMORY_DIR / f"mem_{session_id}.json"


class SessionMemory:
    def __init__(self) -> None:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        self._cache: list[Memory] = []
        self._load_all()

    def _load_all(self) -> None:
        self._cache.clear()
        for f in sorted(MEMORY_DIR.glob("mem_*.json")):
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                for item in data:
                    self._cache.append(Memory(**item))
            except Exception as e:
                logger.warning("Falha ao carregar memória %s: %s", f.name, e)
                continue

    def save(self, key: str, content: str, tags: list[str] | None = None, session_id: str = "default") -> Memory:
        mem = Memory(
            key=key,
            content=content,
            tags=tags or [],
            timestamp=time.time(),
            session_id=session_id,
        )
        self._cache.append(mem)
        self._persist(session_id)
        logger.info("Memória salva: %s (%d chars)", key, len(content))
        return mem

    def search(self, query: str, limit: int = 10) -> list[Memory]:
        query_lower = query.lower()
        matches = []
        for mem in self._cache:
            score = 0
            if query_lower in mem.key.lower():
                score += 3
            if query_lower in mem.content.lower():
                score += 2
            if any(query_lower in t.lower() for t in mem.tags):
                score += 1
            if score > 0:
                matches.append((score, mem))
        matches.sort(key=lambda x: (-x[0], -x[1].timestamp))
        return [m for _, m in matches[:limit]]

    def get_recent(self, n: int = 10) -> list[Memory]:
        sorted_mems = sorted(self._cache, key=lambda m: m.timestamp, reverse=True)
        return sorted_mems[:n]

    def get_for_session(self, session_id: str) -> list[Memory]:
        return [m for m in self._cache if m.session_id == session_id]

    def _persist(self, session_id: str) -> None:
        mems = [m for m in self._cache if m.session_id == session_id]
        path = _memory_file(session_id)
        path.write_text(
            json.dumps([asdict(m) for m in mems], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @property
    def count(self) -> int:
        return len(self._cache)


# "A memória é o diário que todos carregam consigo." -- Oscar Wilde
