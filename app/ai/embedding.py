from __future__ import annotations

import logging
from app.config import get_settings

logger = logging.getLogger("ai_story.embedding")


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.provider = self.settings.embedding_provider.lower().strip()
        self._encoder = None

    def get_dimension(self) -> int:
        if self.provider == "openai":
            return 1536
        # BAAI/bge-small-en-v1.5 is default in fastembed (384 dimensions)
        return 384

    async def get_embedding(self, text: str) -> list[float]:
        if not text:
            # Return zero vector of appropriate size as a fallback
            return [0.0] * self.get_dimension()

        if self.provider == "openai":
            import openai
            
            api_key = self.settings.openai_api_key
            if not api_key:
                logger.error("OpenAI API key missing for embeddings")
                raise ValueError("OPENAI_API_KEY is not set but embedding_provider is 'openai'")

            client = openai.AsyncOpenAI(api_key=api_key)
            response = await client.embeddings.create(
                model="text-embedding-3-small",
                input=[text]
            )
            return response.data[0].embedding
        else:
            # Local fastembed
            if self._encoder is None:
                from fastembed import TextEmbedding
                # Suppress verbose download progress or logs in fastembed if needed
                self._encoder = TextEmbedding()

            # TextEmbedding.embed returns a generator of numpy arrays/iterables
            embeddings = list(self._encoder.embed([text]))
            if not embeddings:
                return [0.0] * self.get_dimension()
            return [float(x) for x in embeddings[0]]
