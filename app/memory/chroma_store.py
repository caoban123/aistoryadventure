from __future__ import annotations

from app.config import get_settings
from app.domain.models import MemoryChunk


class ChromaStore:
    def __init__(self) -> None:
        import chromadb

        settings = get_settings()
        self.client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        self.collection = self.client.get_or_create_collection(name="story_memories")

    def _id(self, chunk: MemoryChunk) -> str:
        return chunk.chunk_id

    async def add_memory(self, chunk: MemoryChunk) -> None:
        self.collection.upsert(
            ids=[self._id(chunk)],
            documents=[chunk.text],
            metadatas=[{
                "session_id": chunk.session_id,
                "kind": chunk.kind,
                "importance": chunk.importance,
                "source_message_id": chunk.source_message_id or "",
                "created_at": chunk.created_at,
                "location": chunk.location or "",
                "involved_npcs": ",".join(chunk.involved_npcs),
                "keywords": ",".join(chunk.keywords),
            }],
        )

    async def search(self, session_id: str, query: str, limit: int = 6) -> list[MemoryChunk]:
        result = self.collection.query(
            query_texts=[query],
            n_results=limit,
            where={"session_id": session_id},
        )
        docs = result.get("documents", [[]])[0]
        ids = result.get("ids", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        chunks: list[MemoryChunk] = []
        for chunk_id, text, meta in zip(ids, docs, metas):
            chunks.append(MemoryChunk(
                chunk_id=chunk_id,
                session_id=session_id,
                text=text,
                kind=meta.get("kind", "event"),
                importance=int(meta.get("importance", 3)),
                source_message_id=meta.get("source_message_id") or None,
                location=meta.get("location") or None,
                involved_npcs=[x.strip() for x in meta.get("involved_npcs", "").split(",") if x.strip()],
                keywords=[x.strip() for x in meta.get("keywords", "").split(",") if x.strip()],
                created_at=meta.get("created_at"),
            ))
        return chunks

    async def list_memories(self, session_id: str, limit: int = 50) -> list[MemoryChunk]:
        result = self.collection.get(
            where={"session_id": session_id},
            limit=limit,
        )

        ids = result.get("ids", [])
        docs = result.get("documents", [])
        metas = result.get("metadatas", [])

        chunks: list[MemoryChunk] = []
        for chunk_id, text, meta in zip(ids, docs, metas):
            chunks.append(MemoryChunk(
                chunk_id=chunk_id,
                session_id=session_id,
                text=text,
                kind=meta.get("kind", "event"),
                importance=int(meta.get("importance", 3)),
                source_message_id=meta.get("source_message_id") or None,
                location=meta.get("location") or None,
                involved_npcs=[x.strip() for x in meta.get("involved_npcs", "").split(",") if x.strip()],
                keywords=[x.strip() for x in meta.get("keywords", "").split(",") if x.strip()],
                created_at=meta.get("created_at"),
            ))

        return chunks

    async def delete_memories(self, session_id: str) -> None:
        result = self.collection.get(
            where={"session_id": session_id},
            include=[]
        )

        ids = result.get("ids", [])

        if ids:
            self.collection.delete(ids=ids)
