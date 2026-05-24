from __future__ import annotations

import uuid
import logging
from app.domain.models import MemoryChunk

logger = logging.getLogger("ai_story.qdrant")

# Deterministic namespace for generating valid Qdrant UUIDs from chunk IDs
NAMESPACE_QDRANT = uuid.UUID("3db5d5c0-1090-482a-8924-a2e38c92a95c")


def _to_uuid(chunk_id: str) -> str:
    return str(uuid.uuid5(NAMESPACE_QDRANT, chunk_id))


class QdrantStore:
    def __init__(self) -> None:
        from app.config import get_settings
        from app.ai.embedding import EmbeddingService

        self.settings = get_settings()
        self.embedding_service = EmbeddingService()
        self.collection_name = "story_memories"
        self._client = None
        self._collection_verified = False

    async def _get_client(self):
        if self._client is None:
            from qdrant_client import AsyncQdrantClient
            self._client = AsyncQdrantClient(
                host=self.settings.qdrant_host,
                port=self.settings.qdrant_port,
                api_key=self.settings.qdrant_api_key,
                https=self.settings.qdrant_https,
            )

        if not self._collection_verified:
            from qdrant_client.models import Distance, VectorParams
            try:
                collections_res = await self._client.get_collections()
                exists = any(c.name == self.collection_name for c in collections_res.collections)
                if not exists:
                    dimension = self.embedding_service.get_dimension()
                    await self._client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=VectorParams(
                            size=dimension,
                            distance=Distance.COSINE,
                        ),
                    )
                self._collection_verified = True
            except Exception as exc:
                logger.error(f"Error initializing Qdrant collection: {exc}")
                raise exc

        return self._client

    async def add_memory(self, chunk: MemoryChunk) -> None:
        client = await self._get_client()
        vector = await self.embedding_service.get_embedding(chunk.text)

        from qdrant_client.models import PointStruct
        
        payload = {
            "chunk_id": chunk.chunk_id,
            "session_id": chunk.session_id,
            "kind": chunk.kind,
            "importance": chunk.importance,
            "source_message_id": chunk.source_message_id or "",
            "created_at": chunk.created_at,
            "text": chunk.text,
        }

        await client.upsert(
            collection_name=self.collection_name,
            points=[
                PointStruct(
                    id=_to_uuid(chunk.chunk_id),
                    vector=vector,
                    payload=payload,
                )
            ],
        )

    async def search(self, session_id: str, query: str, limit: int = 6) -> list[MemoryChunk]:
        client = await self._get_client()
        vector = await self.embedding_service.get_embedding(query)

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        results = await client.search(
            collection_name=self.collection_name,
            query_vector=vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id),
                    )
                ]
            ),
            limit=limit,
        )

        chunks = []
        for r in results:
            payload = r.payload
            chunks.append(
                MemoryChunk(
                    chunk_id=payload.get("chunk_id") or str(r.id),
                    session_id=payload["session_id"],
                    text=payload["text"],
                    kind=payload.get("kind", "event"),
                    importance=int(payload.get("importance", 3)),
                    source_message_id=payload.get("source_message_id") or None,
                    created_at=payload.get("created_at"),
                )
            )
        return chunks

    async def list_memories(self, session_id: str, limit: int = 50) -> list[MemoryChunk]:
        client = await self._get_client()

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        records, _ = await client.scroll(
            collection_name=self.collection_name,
            scroll_filter=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id),
                    )
                ]
            ),
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )

        chunks = []
        for r in records:
            payload = r.payload
            chunks.append(
                MemoryChunk(
                    chunk_id=payload.get("chunk_id") or str(r.id),
                    session_id=payload["session_id"],
                    text=payload["text"],
                    kind=payload.get("kind", "event"),
                    importance=int(payload.get("importance", 3)),
                    source_message_id=payload.get("source_message_id") or None,
                    created_at=payload.get("created_at"),
                )
            )
        return chunks

    async def delete_memories(self, session_id: str) -> None:
        client = await self._get_client()

        from qdrant_client.models import Filter, FieldCondition, MatchValue

        await client.delete(
            collection_name=self.collection_name,
            points_selector=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id),
                    )
                ]
            ),
        )
