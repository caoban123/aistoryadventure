from __future__ import annotations

import re
from app.ai.provider import TextProvider
from app.ai.prompt import build_summary_prompt, build_memory_extract_prompt
from app.config import get_settings
from app.domain.models import MemoryChunk, Message, SessionState, utc_now_iso
from app.memory.firebase_store import FirebaseStore
from app.memory.vector_store import VectorStore, make_chunk_id


class MemoryService:
    def __init__(self, store: FirebaseStore, vector_store: VectorStore, provider: TextProvider) -> None:
        self.store = store
        self.vector_store = vector_store
        self.provider = provider
        self.settings = get_settings()

    async def save_message(self, message: Message) -> None:
        await self.store.add_message(message)

        if message.role not in {"user", "ai"}:
            return

        content = message.content.strip()
        if len(content) < 20:
            return

        memories = await self.extract_memory_chunks(content)

        for memory_text in memories:
            chunk = MemoryChunk(
                chunk_id=make_chunk_id(message.session_id, memory_text),
                session_id=message.session_id,
                text=memory_text,
                kind="event",
                importance=memory_importance(memory_text),
                source_message_id=message.message_id,
            )
            await self.vector_store.add_memory(chunk)
            print("MEMORY SAVED:", memory_text)

    async def recent_messages(self, session_id: str) -> list[Message]:
        return await self.store.get_messages(session_id, limit=self.settings.max_recent_messages)

    async def relevant_memories(self, session_id: str, query: str) -> list[MemoryChunk]:
        return await self.vector_store.search(session_id, query, limit=self.settings.max_relevant_memories)

    async def refresh_summary(self, session: SessionState) -> SessionState:
        messages = await self.store.get_messages(session.session_id, limit=12)
        if len(messages) < 6:
            return session
        prompt = build_summary_prompt(session, messages)
        raw = await self.provider.generate_text(prompt)
        session.world_summary = _extract(raw, "WORLD_SUMMARY") or session.world_summary
        session.character_summary = _extract(raw, "CHARACTER_SUMMARY") or session.character_summary
        session.story_summary = _extract(raw, "STORY_SUMMARY") or session.story_summary
        facts_text = _extract(raw, "IMPORTANT_FACTS")
        if facts_text:
            facts = [x.strip(" -\n\t") for x in re.split(r";|\n", facts_text) if x.strip()]
            merged = list(dict.fromkeys(session.important_facts + facts))
            session.important_facts = merged[-12:]
        session.updated_at = utc_now_iso()
        await self.store.update_session(session)
        return session
    async def extract_memory_chunks(self, text: str) -> list[str]:
        prompt = build_memory_extract_prompt(text)
        raw = await self.provider.generate_text(prompt)

        lines = []
        for line in raw.splitlines():
            line = line.strip(" -•\t")
            lower = line.lower()

            if not line:
                continue
            if lower == "none":
                continue
            if len(line.split()) < 4:
                continue

            weak_phrases = [
                "nhìn quanh",
                "đi tiếp",
                "nói chuyện",
                "cảm thấy",
                "dường như",
                "có vẻ",
            ]

            if any(x in lower for x in weak_phrases):
                continue

            lines.append(line)

        # chống trùng, giới hạn 6 memory/lượt
        unique = list(dict.fromkeys(lines))
        return unique[:6]


def _extract(text: str, key: str) -> str:
    pattern = rf"{key}\s*:\s*(.*?)(?=\n[A-Z_]+\s*:|\Z)"
    match = re.search(pattern, text, flags=re.S)
    return match.group(1).strip() if match else ""
def split_events(text: str) -> list[str]:
    parts = []
    sentences = text.split(".")
    for s in sentences:
        s = s.strip()
        if len(s) > 15:
            parts.append(s)
    return parts[:5]
def memory_importance(text: str) -> int:
    lower = text.lower()
    high_keywords = [
        "bí mật", "lời nguyền", "chết", "bị thương", "mất tích",
        "phản bội", "vật phẩm", "chiếc nhẫn", "chìa khóa",
        "nhiệm vụ", "lời hứa", "quái vật", "npc", "gặp"
    ]

    if any(k in lower for k in high_keywords):
        return 5

    return 3