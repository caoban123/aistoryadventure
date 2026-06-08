from __future__ import annotations

import json
import urllib.request
from abc import ABC, abstractmethod
from google import genai
from openai import AsyncOpenAI
from app.config import get_settings
# from app.ai.pool.gemini_pool_provider import GeminiPoolProvider
# from app.ai.pool.openai_pool_provider import OpenAIPoolProvider
# from app.ai.pool.grog_pool_provider import GroqPoolProvider
class TextProvider(ABC):
    last_usage: dict | None = None

    def clear_usage(self) -> None:
        self.last_usage = None

    def set_usage(
        self,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
    ) -> None:
        self.last_usage = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        }

    @abstractmethod
    async def generate_text(self, prompt: str) -> str:
        raise NotImplementedError


class MockProvider(TextProvider):
    async def generate_text(self, prompt: str) -> str:
        self.clear_usage()
        return (
            "Màn sương mở ra trên một vùng đất xa lạ. Bạn tỉnh dậy giữa tiếng gió, "
            "trong tay còn giữ một vật nhỏ mà chính bạn cũng chưa hiểu vì sao nó quan trọng.\n\n"
            "Bạn có thể quan sát xung quanh, gọi thử xem có ai đáp lại, hoặc tự chọn một hướng để đi."
        )


class OpenAIProvider(TextProvider):
    def __init__(self) -> None:
        from openai import AsyncOpenAI

        settings = get_settings()
        if not settings.openai_api_key:
            raise RuntimeError("Missing OPENAI_API_KEY in .env")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def generate_text(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
        )
        usage = getattr(response, "usage", None)
        if usage:
            self.set_usage(
                input_tokens=getattr(usage, "prompt_tokens", None),
                output_tokens=getattr(usage, "completion_tokens", None),
            )
        else:
            self.clear_usage()
        return response.choices[0].message.content or ""


class GeminiProvider(TextProvider):
    def __init__(self) -> None:
        from google import genai

        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError("Missing GEMINI_API_KEY in .env")
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.model = settings.gemini_model

    async def generate_text(self, prompt: str) -> str:
        import asyncio
        response = await asyncio.to_thread(
            self.client.models.generate_content,
            model=self.model,
            contents=prompt,
        )
        usage = getattr(response, "usage_metadata", None)
        if usage:
            self.set_usage(
                input_tokens=getattr(usage, "prompt_token_count", None),
                output_tokens=getattr(usage, "candidates_token_count", None),
            )
        else:
            self.clear_usage()
        return response.text or ""


class OllamaProvider(TextProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.ollama_base_url.rstrip("/")
        self.model = settings.ollama_model

    async def generate_text(self, prompt: str) -> str:
        self.clear_usage()
        import asyncio
        payload = json.dumps({"model": self.model, "prompt": prompt, "stream": False}).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        def _make_request():
            with urllib.request.urlopen(request, timeout=180) as response:
                return json.loads(response.read().decode("utf-8"))
        data = await asyncio.to_thread(_make_request)
        return data.get("response", "")

class GroqProvider(TextProvider):
    def __init__(self) -> None:
        from openai import AsyncOpenAI

        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("Missing GROQ_API_KEY in .env")

        # Groq dùng OpenAI-compatible API
        self.client = AsyncOpenAI(
            api_key=settings.groq_api_key,
            base_url="https://api.groq.com/openai/v1",
        )
        self.model = settings.groq_model


    async def generate_text(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
        )
        usage = getattr(response, "usage", None)
        if usage:
            self.set_usage(
                input_tokens=getattr(usage, "prompt_tokens", None),
                output_tokens=getattr(usage, "completion_tokens", None),
            )
        else:
            self.clear_usage()
        return response.choices[0].message.content or ""

class GeminiPoolProvider(TextProvider):
    def __init__(self):
        settings = get_settings()

        keys = settings.gemini_api_keys.strip()

        if not keys:
            raise RuntimeError(
                "Missing GEMINI_API_KEYS"
            )

        self.keys = [
            k.strip()
            for k in keys.split(",")
            if k.strip()
        ]

        self.index = 0
        self.model = settings.gemini_model

    def _next_client(self):
        key = self.keys[self.index]
        key_display = f"{key[:6]}...{key[-4:]}"  # che bớt key, chỉ hiện đầu/cuối
        print(f"[GEMINI] Using model={self.model} | key[{self.index}]={key_display}")
        self.index = (self.index + 1) % len(self.keys)
        return genai.Client(api_key=key)

    async def generate_text(
        self,
        prompt: str
    ) -> str:
        import asyncio

        last_error = None

        for _ in range(len(self.keys)):

            try:
                client = self._next_client()

                response = await asyncio.to_thread(
                    client.models.generate_content,
                    model=self.model,
                    contents=prompt,
                )

                return response.text or ""

            except Exception as e:
                last_error = e

        raise last_error

class GroqPoolProvider(TextProvider):

    def __init__(self):
        settings = get_settings()

        keys = settings.groq_api_keys.strip()

        if not keys:
            raise RuntimeError(
                "Missing GROQ_API_KEYS"
            )

        self.keys = [
            k.strip()
            for k in keys.split(",")
            if k.strip()
        ]

        self.index = 0
        self.model = settings.groq_model

    def _next_client(self):
        key = self.keys[self.index]
        key_display = f"{key[:6]}...{key[-4:]}"
        print(f"[GROQ] Using model={self.model} | key[{self.index}]={key_display}")
        self.index = (self.index + 1) % len(self.keys)
        return AsyncOpenAI(
            api_key=key,
            base_url="https://api.groq.com/openai/v1",
        )

    async def generate_text(self, prompt: str) -> str:
        last_error = None
        for _ in range(len(self.keys)):
            try:
                client = self._next_client()
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": prompt,
                        }
                    ],
                    temperature=0.9,
                )
                return (
                    response
                    .choices[0]
                    .message
                    .content
                    or ""
                )
            except Exception as e:
                last_error = e
        raise last_error


class RoundRobinProvider(TextProvider):
    """
    Thứ tự ưu tiên: Gemini → Groq → Ollama
    - Mỗi provider tự thử hết key nội bộ trước
    - Chỉ chuyển provider tiếp theo khi provider hiện tại hết sạch key
    """
    def __init__(self):
        self.provider_classes = [
            GeminiPoolProvider,   # ưu tiên 1: thử hết key Gemini
            GroqPoolProvider,     # ưu tiên 2: thử hết key Groq
            OllamaProvider,       # ưu tiên 3: fallback cuối
        ]
        self._providers: list[TextProvider | None] = [None] * len(self.provider_classes)

    def _get_provider(self, idx: int) -> TextProvider | None:
        """Lazy init — chỉ khởi tạo khi cần, cache lại để dùng lần sau."""
        if self._providers[idx] is not None:
            return self._providers[idx]
        try:
            self._providers[idx] = self.provider_classes[idx]()
            return self._providers[idx]
        except RuntimeError as e:
            print(f"[FALLBACK] Skip {self.provider_classes[idx].__name__}: {e}")
            return None

    async def generate_text(self, prompt: str) -> str:
        last_error: Exception | None = None

        for idx in range(len(self.provider_classes)):
            provider = self._get_provider(idx)
            if provider is None:
                continue  # thiếu config → bỏ qua

            try:
                print(f"[FALLBACK] Trying: {provider.__class__.__name__}")
                return await provider.generate_text(prompt)
            except Exception as e:
                # provider đã thử hết key nội bộ, chuyển sang cái tiếp theo
                print(f"[FALLBACK] {provider.__class__.__name__} exhausted: {e}")
                last_error = e

        raise RuntimeError("All providers exhausted") from last_error


def get_text_provider() -> TextProvider:
    provider = get_settings().text_provider.lower().strip()
    if provider == "round_robin":
        return RoundRobinProvider()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "gemini":
        return GeminiProvider()
    if provider == "ollama":
        return OllamaProvider()
    if provider == "groq": 
        return GroqProvider()
    return MockProvider()
