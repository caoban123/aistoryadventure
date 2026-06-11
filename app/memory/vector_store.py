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
        try:
            await self.impl.add_memory(chunk)
        except Exception as e:
            import logging
            logger = logging.getLogger("ai_story.vector_store")
            logger.error(f"Vector DB error in add_memory: {e}. Falling back to ChromaStore.")
            try:
                from app.memory.chroma_store import ChromaStore
                fallback = ChromaStore()
                await fallback.add_memory(chunk)
            except Exception as fe:
                logger.error(f"ChromaStore fallback failed: {fe}")

    async def search(self, session_id: str, query: str, limit: int = 6) -> list[MemoryChunk]:
        try:
            return await self.impl.search(session_id, query, limit=limit)
        except Exception as e:
            import logging
            logger = logging.getLogger("ai_story.vector_store")
            logger.error(f"Vector DB error in search: {e}. Falling back to ChromaStore.")
            try:
                from app.memory.chroma_store import ChromaStore
                fallback = ChromaStore()
                return await fallback.search(session_id, query, limit=limit)
            except Exception as fe:
                logger.error(f"ChromaStore fallback failed: {fe}")
                return []

    async def list_memories(self, session_id: str, limit: int = 50) -> list[MemoryChunk]:
        try:
            return await self.impl.list_memories(session_id, limit=limit)
        except Exception as e:
            import logging
            logger = logging.getLogger("ai_story.vector_store")
            logger.error(f"Vector DB error in list_memories: {e}. Falling back to ChromaStore.")
            try:
                from app.memory.chroma_store import ChromaStore
                fallback = ChromaStore()
                return await fallback.list_memories(session_id, limit=limit)
            except Exception as fe:
                logger.error(f"ChromaStore fallback failed: {fe}")
                return []

    async def delete_memories(self, session_id: str) -> None:
        try:
            await self.impl.delete_memories(session_id)
        except Exception as e:
            import logging
            logger = logging.getLogger("ai_story.vector_store")
            logger.error(f"Vector DB error in delete_memories: {e}. Falling back to ChromaStore.")
            try:
                from app.memory.chroma_store import ChromaStore
                fallback = ChromaStore()
                await fallback.delete_memories(session_id)
            except Exception as fe:
                logger.error(f"ChromaStore fallback failed: {fe}")


def make_chunk_id(session_id: str, text: str) -> str:
    digest = hashlib.sha1(f"{session_id}:{text}".encode("utf-8")).hexdigest()[:16]
    return f"mem_{digest}"
