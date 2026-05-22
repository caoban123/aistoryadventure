# Qdrant Migration Plan for AI Story Adventure

Repository: [caoban123/aistoryadventure](https://github.com/caoban123/aistoryadventure?utm_source=chatgpt.com)

---

# 1. Mục tiêu migration

Mục tiêu là thay thế:

```text
ChromaDB local persistence
```

bằng:

```text
Qdrant vector database
```

để cải thiện:

- scalability
- retrieval quality
- metadata filtering
- memory lifecycle
- multi-instance deployment
- production stability

---

# 2. Kiến trúc mới

## Kiến trúc cũ

```text
Frontend
   ↓
FastAPI
   ↓
ChromaDB local
```

---

## Kiến trúc mới

```text
Frontend
   ↓
FastAPI
   ↓
Qdrant
```

Nếu dùng Coolify:

```text
Internet
   ↓
Cloudflare Tunnel
   ↓
Coolify
   ↓
FastAPI Container
   ↓
Qdrant Container
```

---

# 3. Vì sao Qdrant tốt hơn ChromaDB cho project này

| Feature | ChromaDB | Qdrant |
|---|---|---|
| Metadata filtering | yếu | mạnh |
| Production stability | trung bình | tốt |
| Docker deployment | OK | rất tốt |
| Multi-instance | khó | tốt |
| Performance | khá | rất nhanh |
| Payload filtering | hạn chế | mạnh |
| Memory lifecycle | thủ công | dễ mở rộng |
| Hybrid search | yếu | mạnh |

---

# 4. Docker setup

## docker-compose.yml

```yaml
services:
  backend:
    build: .
    container_name: aistory-backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - qdrant

  qdrant:
    image: qdrant/qdrant:latest
    container_name: qdrant
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_storage:/qdrant/storage

volumes:
  qdrant_storage:
```

---

# 5. Cài SDK

## requirements.txt

```txt
qdrant-client
```

hoặc:

```bash
pip install qdrant-client
```

---

# 6. Tạo Qdrant service

## File mới

```text
app/memory/qdrant_store.py
```

---

## Khởi tạo client

```python
from qdrant_client import QdrantClient

client = QdrantClient(
    host="qdrant",
    port=6333,
)
```

Nếu local:

```python
client = QdrantClient("localhost", port=6333)
```

---

# 7. Tạo collection

```python
from qdrant_client.models import VectorParams, Distance

client.recreate_collection(
    collection_name="story_memories",
    vectors_config=VectorParams(
        size=1536,
        distance=Distance.COSINE,
    ),
)
```

1536 = OpenAI embedding size.

Nếu dùng nomic/bge thì đổi.

---

# 8. Memory schema mới

Đây là phần QUAN TRỌNG.

Bạn nên chuyển từ:

```text
raw chunks only
```

sang:

```text
structured narrative memory
```

---

## Payload schema

```python
payload = {
    "session_id": session_id,
    "memory_type": "event",
    "importance": 8,
    "character": "Aren",
    "location": "Sunless Realm",
    "timestamp": timestamp,
    "summary": memory_text,
    "chapter": 2,
    "tags": ["combat", "betrayal"],
}
```

---

# 9. Insert memory

```python
from qdrant_client.models import PointStruct

client.upsert(
    collection_name="story_memories",
    points=[
        PointStruct(
            id=memory_id,
            vector=embedding,
            payload=payload,
        )
    ]
)
```

---

# 10. Semantic retrieval

## Retrieval cơ bản

```python
results = client.search(
    collection_name="story_memories",
    query_vector=query_embedding,
    limit=10,
)
```

---

# 11. Retrieval với filtering

Đây là điểm mạnh lớn nhất của Qdrant.

```python
from qdrant_client.models import Filter, FieldCondition, MatchValue

results = client.search(
    collection_name="story_memories",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="session_id",
                match=MatchValue(value=session_id)
            )
        ]
    ),
    limit=10,
)
```

---

# 12. Importance-aware retrieval

Đây là thứ project bạn đang thiếu.

---

## Chỉ retrieve memories quan trọng

```python
FieldCondition(
    key="importance",
    range={"gte": 7}
)
```

---

## Ví dụ retrieval nâng cao

```python
results = client.search(
    collection_name="story_memories",
    query_vector=query_embedding,
    query_filter=Filter(
        must=[
            FieldCondition(
                key="session_id",
                match=MatchValue(value=session_id)
            ),
            FieldCondition(
                key="importance",
                range={"gte": 6}
            )
        ]
    ),
    limit=8,
)
```

---

# 13. Memory types

Bạn nên chia memory thành:

| Type | Ý nghĩa |
|---|---|
| event | sự kiện |
| character | thông tin nhân vật |
| world | world lore |
| item | vật phẩm |
| quest | nhiệm vụ |
| relationship | quan hệ |
| combat | chiến đấu |
| dialogue | hội thoại quan trọng |

---

# 14. Working memory architecture

Bạn hiện chỉ có:

```text
semantic memory
```

Bạn nên thêm:

---

## Working memory

Current scene:

```python
recent_messages[-8:]
```

---

## Episodic memory

Timeline:

```python
chapter summaries
```

---

## Semantic memory

Qdrant retrieval.

---

# 15. Hierarchical summarization

Cực kỳ quan trọng.

---

## Hiện tại

```text
message → vector
```

---

## Nên đổi thành

```text
message
   ↓
scene summary
   ↓
chapter summary
   ↓
world summary
```

---

# 16. Memory decay

Bạn cần decay memories cũ.

---

## Ví dụ

```python
importance *= 0.98
```

mỗi ngày.

---

## Hoặc

```python
final_score =
semantic_score
+ importance_score
+ recency_score
```

---

# 17. Duplicate memory prevention

Hiện tại project bạn rất dễ:

```text
duplicate memories
```

---

## Cách xử lý

Trước khi insert:

```python
search top 3 similar memories
```

Nếu similarity > 0.95:

```python
skip insert
```

---

# 18. Retrieval reranking

Đây là upgrade lớn.

---

## Flow mới

```text
semantic retrieval
      ↓
rerank bằng LLM
      ↓
inject prompt
```

---

# 19. AI memory pipeline mới

## Pipeline hiện tại

```text
message
   ↓
embedding
   ↓
retrieve
```

---

## Pipeline nên dùng

```text
message
   ↓
extract memory
   ↓
importance scoring
   ↓
embedding
   ↓
Qdrant insert
   ↓
retrieval
   ↓
reranking
   ↓
prompt injection
```

---

# 20. Migration strategy

## Bước 1

Giữ nguyên:

```text
StoryService
```

---

## Bước 2

Tạo abstraction:

```python
class VectorStore:
```

---

## Bước 3

Implement:

```python
ChromaStore
QdrantStore
```

---

## Bước 4

Switch bằng env:

```env
VECTOR_DB=qdrant
```

---

# 21. Config mới

## .env

```env
QDRANT_HOST=qdrant
QDRANT_PORT=6333
VECTOR_DB=qdrant
```

---

# 22. Production deployment

## Coolify setup

Tạo:

- backend service
- qdrant service

---

## Volume persistence

BẮT BUỘC:

```text
/qdrant/storage
```

nếu không sẽ mất vectors.

---

# 23. Future architecture

Sau khi migrate:

```text
Frontend
   ↓
FastAPI
   ↓
Narrative Engine
   ↓
Memory Orchestrator
   ↓
Qdrant
```

---

# 24. Biggest improvement

Sau migration, thứ cải thiện lớn nhất sẽ là:

```text
retrieval quality
```

không phải speed.

---

# 25. Quan trọng nhất

Điểm mạnh thực sự không phải:

```text
Qdrant vs ChromaDB
```

mà là:

```text
memory lifecycle architecture
```

Nếu bạn thêm:

- importance scoring
- reranking
- hierarchical summaries
- episodic memory
- decay

thì project sẽ từ:

```text
AI chatbot with memory
```

thành:

```text
real AI narrative engine
```

---

# 26. Code implementation thực tế

## File mới

```text
app/memory/qdrant_store.py
```

---

## Full implementation

```python
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    Range,
)

import uuid
import time


class QdrantStore:
    def __init__(
        self,
        host="qdrant",
        port=6333,
        collection_name="story_memories",
        vector_size=1536,
    ):
        self.collection_name = collection_name

        self.client = QdrantClient(
            host=host,
            port=port,
        )

        self._ensure_collection(vector_size)

    def _ensure_collection(self, vector_size):
        collections = self.client.get_collections().collections

        exists = any(
            c.name == self.collection_name
            for c in collections
        )

        if not exists:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def insert_memory(
        self,
        session_id,
        text,
        embedding,
        memory_type="event",
        importance=5,
        character=None,
        location=None,
        tags=None,
        chapter=1,
    ):
        payload = {
            "session_id": session_id,
            "text": text,
            "memory_type": memory_type,
            "importance": importance,
            "character": character,
            "location": location,
            "tags": tags or [],
            "chapter": chapter,
            "created_at": int(time.time()),
        }

        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=embedding,
            payload=payload,
        )

        self.client.upsert(
            collection_name=self.collection_name,
            points=[point],
        )

    def search_memories(
        self,
        session_id,
        query_embedding,
        limit=8,
        min_importance=0,
    ):
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="session_id",
                        match=MatchValue(value=session_id),
                    ),
                    FieldCondition(
                        key="importance",
                        range=Range(gte=min_importance),
                    ),
                ]
            ),
            limit=limit,
        )

        return [
            {
                "score": r.score,
                "payload": r.payload,
            }
            for r in results
        ]

    def delete_session_memories(self, session_id):
        self.client.delete(
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
```

---

# 27. Vector store abstraction

## File

```text
app/memory/vector_store.py
```

---

```python
class VectorStore:
    def insert_memory(self, *args, **kwargs):
        raise NotImplementedError

    def search_memories(self, *args, **kwargs):
        raise NotImplementedError
```

---

# 28. Environment config

## .env

```env
VECTOR_DB=qdrant
QDRANT_HOST=qdrant
QDRANT_PORT=6333
```

---

# 29. Store factory

## File

```text
app/memory/store_factory.py
```

---

```python
import os

from app.memory.qdrant_store import QdrantStore
from app.memory.chroma_store import ChromaStore


def get_vector_store():
    db = os.getenv("VECTOR_DB", "chroma")

    if db == "qdrant":
        return QdrantStore(
            host=os.getenv("QDRANT_HOST", "qdrant"),
            port=int(os.getenv("QDRANT_PORT", 6333)),
        )

    return ChromaStore()
```

---

# 30. StoryService integration

## Trước đây

```python
self.memory = ChromaStore()
```

---

## Đổi thành

```python
from app.memory.store_factory import get_vector_store

self.memory = get_vector_store()
```

---

# 31. Memory extraction pipeline

## File

```text
app/ai/memory_extractor.py
```

---

```python
IMPORTANT_KEYWORDS = [
    "death",
    "betrayal",
    "secret",
    "love",
    "war",
    "artifact",
]


def calculate_importance(text: str):
    score = 3

    text_lower = text.lower()

    for keyword in IMPORTANT_KEYWORDS:
        if keyword in text_lower:
            score += 2

    return min(score, 10)
```

---

# 32. Duplicate memory prevention

## Trước khi insert

```python
existing = store.search_memories(
    session_id=session_id,
    query_embedding=embedding,
    limit=3,
)

if existing:
    top_score = existing[0]["score"]

    if top_score > 0.97:
        return
```

---

# 33. Hierarchical summaries

## Nên thêm

```text
scene_summary
chapter_summary
world_summary
```

---

## Flow

```text
messages
   ↓
scene summary
   ↓
chapter summary
   ↓
world summary
```

---

# 34. Memory ranking formula

## Công thức đề xuất

```python
final_score = (
    semantic_similarity * 0.6
    + importance_score * 0.3
    + recency_score * 0.1
)
```

---

# 35. Prompt injection strategy

## Thay vì

```text
inject raw memories
```

---

## Nên

```text
inject:
- world summary
- character summary
- top 5 memories
- current scene
```

---

# 36. Docker production setup

## docker-compose.yml

```yaml
services:
  backend:
    build: .
    restart: unless-stopped
    env_file:
      - .env
    ports:
      - "8000:8000"
    depends_on:
      - qdrant

  qdrant:
    image: qdrant/qdrant:latest
    restart: unless-stopped
    ports:
      - "6333:6333"
    volumes:
      - qdrant_storage:/qdrant/storage

volumes:
  qdrant_storage:
```

---

# 37. Coolify deployment

## Tạo services

```text
backend
qdrant
```

---

## Mount volume

```text
/qdrant/storage
```

---

# 38. Cloudflare Tunnel

## Config

```yaml
ingress:
  - hostname: api.aistoryadventure.xyz
    service: http://backend:8000

  - service: http_status:404
```

---

# 39. Future upgrades

Sau khi migrate sang Qdrant, bạn có thể thêm:

---

## Memory graph

```text
NPC relationships
```

---

## Timeline engine

```text
story chronology
```

---

## RAG reranking

```text
LLM reranking
```

---

## Narrative planning

```text
future plot planning
```

---

# 40. Kết luận

Migration sang Qdrant không chỉ là đổi vector database.

Nó là bước đầu để:

```text
upgrade architecture
```

Từ:

```text
AI chatbot with memory
```

thành:

```text
persistent AI narrative engine
```

