import os
import sys
import asyncio
from pathlib import Path

# Add project root to python path
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.memory.chroma_store import ChromaStore
from app.memory.qdrant_store import QdrantStore
from app.domain.models import MemoryChunk


async def migrate():
    print("--- Starting ChromaDB to Qdrant Migration ---")
    settings = get_settings()

    # 1. Initialize ChromaStore
    print("Loading ChromaDB data...")
    try:
        chroma = ChromaStore()
    except Exception as exc:
        print(f"Error loading ChromaDB (maybe it doesn't exist or is empty): {exc}")
        return

    # Get all records from Chroma collection
    res = chroma.collection.get()
    ids = res.get("ids", [])
    docs = res.get("documents", [])
    metas = res.get("metadatas", [])

    total = len(ids)
    print(f"Found {total} memory chunks in ChromaDB.")
    if total == 0:
        print("Nothing to migrate. Exiting.")
        return

    # 2. Initialize QdrantStore (will create collection if not exists)
    print("Connecting to Qdrant...")
    os.environ["VECTOR_DB"] = "qdrant"
    get_settings.cache_clear()

    try:
        qdrant = QdrantStore()
        # Ping Qdrant client to ensure it's up
        await qdrant._get_client()
    except Exception as exc:
        print(f"Error connecting to Qdrant: {exc}")
        print("Please make sure Qdrant is running and accessible.")
        return

    # 3. Migrate items
    success_count = 0
    for idx, (chunk_id, doc, meta) in enumerate(zip(ids, docs, metas), 1):
        print(f"[{idx}/{total}] Migrating {chunk_id}...")
        try:
            chunk = MemoryChunk(
                chunk_id=chunk_id,
                session_id=meta["session_id"],
                text=doc,
                kind=meta.get("kind", "event"),
                importance=int(meta.get("importance", 3)),
                source_message_id=meta.get("source_message_id") or None,
                created_at=meta.get("created_at"),
            )
            await qdrant.add_memory(chunk)
            success_count += 1
        except Exception as e:
            print(f"  Error migrating {chunk_id}: {e}")

    print(f"\nMigration complete! Successfully migrated {success_count}/{total} memories to Qdrant.")


if __name__ == "__main__":
    asyncio.run(migrate())
