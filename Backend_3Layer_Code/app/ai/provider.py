from __future__ import annotations

import json
import urllib.request
from abc import ABC, abstractmethod

from app.config import get_settings


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
        self.model = settings.text_model

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
        self.model = settings.text_model

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
        self.model = settings.text_model

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
        self.model = settings.text_model

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


def get_text_provider() -> TextProvider:
    provider = get_settings().text_provider.lower().strip()
    if provider == "openai":
        return OpenAIProvider()
    if provider == "gemini":
        return GeminiProvider()
    if provider == "ollama":
        return OllamaProvider()
    if provider == "groq": 
        return GroqProvider()
    return MockProvider()
