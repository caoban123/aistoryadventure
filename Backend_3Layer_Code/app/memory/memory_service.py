from __future__ import annotations

import re
from app.ai.provider import TextProvider
from app.ai.prompt import build_summary_prompt, build_memory_extract_prompt, build_rolling_summary_prompt, build_structured_state_prompt
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

        import asyncio
        asyncio.create_task(self._bg_extract_and_save(message, content))
        asyncio.create_task(self._bg_update_rolling_summary(message.session_id))
        asyncio.create_task(self._bg_update_structured_state(message.session_id))

    async def _bg_extract_and_save(self, message: Message, content: str) -> None:
        try:
            memories_data = await self.extract_memory_chunks_json(content)
            for m_data in memories_data:
                memory_text = m_data.get("text", "")
                if len(memory_text.split()) < 4: continue
                chunk = MemoryChunk(
                    chunk_id=make_chunk_id(message.session_id, memory_text),
                    session_id=message.session_id,
                    text=memory_text,
                    kind="event",
                    importance=3, # Simplified
                    source_message_id=message.message_id,
                    location=m_data.get("location"),
                    involved_npcs=m_data.get("involved_npcs", []),
                    keywords=m_data.get("keywords", [])
                )
                await self.vector_store.add_memory(chunk)
                print("MEMORY SAVED:", memory_text)
        except Exception as exc:
            print(f"Background memory extraction error for session {message.session_id}: {exc}")

    async def _bg_update_rolling_summary(self, session_id: str) -> None:
        try:
            session = await self.store.get_session(session_id)
            if not session:
                return
            
            messages = await self.store.get_messages(session_id, limit=20)
            
            if len(messages) >= 6 and len(messages) % 6 == 1: 
                recent_msgs = messages[-6:]
                
                prompt = build_rolling_summary_prompt(session.rolling_story_summary, recent_msgs)
                new_summary = await self.provider.generate_text(prompt)
                
                if new_summary and len(new_summary.strip()) > 10:
                    session.rolling_story_summary = new_summary.strip()
                    session.updated_at = utc_now_iso()
                    await self.store.update_session(session)
                    print(f"ROLLING SUMMARY UPDATED for session {session_id}")
        except Exception as exc:
            print(f"Rolling summary extraction error for session {session_id}: {exc}")

    async def _bg_update_structured_state(self, session_id: str) -> None:
        try:
            session = await self.store.get_session(session_id)
            if not session:
                return
            messages = await self.store.get_messages(session_id, limit=6)
            if len(messages) == 0: return
            
            recent_text = "\n".join([m.content for m in messages[-2:]])
            current_state_json = session.structured_state.model_dump_json()
            
            prompt = build_structured_state_prompt(current_state_json, recent_text)
            new_state_raw = await self.provider.generate_text(prompt)
            
            import json
            match = re.search(r'\{.*\}', new_state_raw, re.DOTALL)
            if match:
                new_state_dict = json.loads(match.group(0))
                from app.domain.models import StructuredState
                session.structured_state = StructuredState(**new_state_dict)
                session.updated_at = utc_now_iso()
                await self.store.update_session(session)
                print("STRUCTURED STATE UPDATED")
        except Exception as exc:
            print(f"Structured state update error: {exc}")



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
    async def extract_memory_chunks_json(self, text: str) -> list[dict]:
        prompt = build_memory_extract_prompt(text)
        raw = await self.provider.generate_text(prompt)
        try:
            import json
            match = re.search(r'\[.*\]', raw, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(raw)
        except Exception as e:
            print(f"Failed to parse memory JSON: {e}")
            return []

    def rerank_memories(self, memories: list[MemoryChunk], current_location: str, keywords: list[str]) -> list[MemoryChunk]:
        scored_memories = []
        for chunk in memories:
            score = 1.0
            if chunk.location and current_location and chunk.location.lower() == current_location.lower():
                score *= 1.2
            
            match_count = sum(1 for kw in keywords if kw.lower() in [k.lower() for k in chunk.keywords])
            score *= (1.0 + 0.15 * match_count)
            
            scored_memories.append((score, chunk))
        
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        return [m for score, m in scored_memories]

    async def fetch_npc_history(self, session_id: str, npc_id: str) -> list[MemoryChunk]:
        memories = await self.vector_store.search(session_id, npc_id, limit=30)
        return [m for m in memories if npc_id in m.involved_npcs]


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