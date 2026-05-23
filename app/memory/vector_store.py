from __future__ import annotations

import hashlib
from app.config import get_settings
from app.domain.models import MemoryChunk


class VectorStore:
    def __init__(self) -> None:
        settings = get_settings()
        db_type = settings.vector_db.lower().strip()

        if db_type == "qdrant":
            from app.memory.qdrant_store import QdrantStore
            self.impl = QdrantStore()
        else:
            from app.memory.chroma_store import ChromaStore
            self.impl = ChromaStore()

    async def add_memory(self, chunk: MemoryChunk) -> None:
        await self.impl.add_memory(chunk)

    async def search(self, session_id: str, query: str, limit: int = 6) -> list[MemoryChunk]:
        return await self.impl.search(session_id, query, limit=limit)

    async def list_memories(self, session_id: str, limit: int = 50) -> list[MemoryChunk]:
        return await self.impl.list_memories(session_id, limit=limit)

    async def delete_memories(self, session_id: str) -> None:
        await self.impl.delete_memories(session_id)


def make_chunk_id(session_id: str, text: str) -> str:
    digest = hashlib.sha1(f"{session_id}:{text}".encode("utf-8")).hexdigest()[:16]
    return f"mem_{digest}"
