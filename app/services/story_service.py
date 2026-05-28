from __future__ import annotations

from datetime import datetime, timedelta, timezone
from time import perf_counter
from uuid import uuid4
from app.ai.output_parser import parse_story_output
from app.ai.prompt import (
    build_start_prompt,
    build_turn_prompt,
    build_novel_world_prompt,
    build_novel_foundation_prompt,
)
from app.ai.provider import get_text_provider
from app.domain.models import Message, SessionState, utc_now_iso
from app.domain.schemas import (
    StartGameRequest,
    StoryResponse,
    TurnRequest,
    NovelStartRequest,
    NovelWorldResponse,
    NovelFoundationRequest,
)
from app.memory.firebase_store import FirebaseStore
from app.memory.memory_service import MemoryService
from app.memory.vector_store import VectorStore
from app.services.admin_service import AdminControlService
from app.services.safety_service import SafetyFilterService
import json 

DRAFT_TTL_HOURS = 24

SURVIVAL_STAT_KEYS = ("danger", "supplies", "wounds", "time_pressure")


def _clamp_survival_stat(value, fallback: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = fallback

    return max(0, min(5, number))


def build_adventure_profile(request: StartGameRequest) -> dict:
    raw = request.adventure_profile or {}
    profile = {
        "player_name": request.player_name,
        "role": str(raw.get("role") or request.personality or "Wanderer").strip(),
        "starting_condition": str(raw.get("starting_condition") or "Thrown into danger").strip(),
        "region": str(raw.get("region") or request.world_hint or request.story_style or "Unknown wilds").strip(),
        "objective": str(raw.get("objective") or "Survive and find a way forward").strip(),
        "threat": str(raw.get("threat") or "A danger is closing in").strip(),
        "loadout": str(raw.get("loadout") or "Light supplies").strip(),
        "danger": _clamp_survival_stat(raw.get("danger"), 3),
        "supplies": _clamp_survival_stat(raw.get("supplies"), 3),
        "wounds": _clamp_survival_stat(raw.get("wounds"), 0),
        "time_pressure": _clamp_survival_stat(raw.get("time_pressure"), 3),
        "last_survival_note": str(raw.get("last_survival_note") or "The run has just begun.").strip(),
    }

    seed_parts = [
        profile["starting_condition"],
        profile["region"],
        profile["objective"],
        profile["threat"],
        profile["loadout"],
    ]
    profile["seed"] = " | ".join(part for part in seed_parts if part)[:400]
    return profile


def merge_survival_update(profile: dict, update: dict | None) -> dict:
    if not isinstance(update, dict) or not update:
        return profile

    merged = dict(profile or {})

    for key in SURVIVAL_STAT_KEYS:
        if key in update:
            merged[key] = _clamp_survival_stat(update.get(key), merged.get(key, 0))

    for key in (
        "objective",
        "threat",
        "region",
        "loadout",
        "last_survival_note",
    ):
        value = update.get(key)
        if isinstance(value, str) and value.strip():
            merged[key] = value.strip()[:500]

    return merged


class StoryService:
    def __init__(self) -> None:
        self.provider = get_text_provider()
        self.store = FirebaseStore()
        self.vector_store = VectorStore()
        self.admin_control = AdminControlService()
        self.memory = MemoryService(self.store, self.vector_store, self.provider)
        self.safety_filter = SafetyFilterService()

    async def _generate_text_logged(
        self,
        prompt: str,
        *,
        user_id: str,
        session_id: str | None,
        operation: str,
    ) -> str:
        started_at = perf_counter()
        estimated_input_tokens = estimate_token_count(prompt)

        if hasattr(self.provider, "clear_usage"):
            self.provider.clear_usage()

        try:
            raw = await self.provider.generate_text(prompt)
            usage = getattr(self.provider, "last_usage", None) or {}
            await self.admin_control.log_ai_usage(
                user={"uid": user_id},
                action="provider_call",
                operation=operation,
                status="success",
                session_id=session_id,
                estimated_input_tokens=estimated_input_tokens,
                estimated_output_tokens=estimate_token_count(raw),
                actual_input_tokens=usage.get("input_tokens"),
                actual_output_tokens=usage.get("output_tokens"),
                latency_ms=round((perf_counter() - started_at) * 1000),
            )
            return raw
        except Exception as exc:
            await self.admin_control.log_ai_usage(
                user={"uid": user_id},
                action="provider_call",
                operation=operation,
                status="error",
                session_id=session_id,
                error_kind="provider_error",
                estimated_input_tokens=estimated_input_tokens,
                latency_ms=round((perf_counter() - started_at) * 1000),
            )
            raise

    async def cleanup_old_drafts(self, user_id: str) -> int:
        cutoff = (
            datetime.now(timezone.utc) - timedelta(hours=DRAFT_TTL_HOURS)
        ).isoformat()
        drafts = await self.store.list_old_draft_sessions(
            user_id=user_id,
            older_than=cutoff,
            limit=100,
        )

        for draft in drafts:
            await self.vector_store.delete_memories(draft.session_id)
            await self.store.delete_session(draft.session_id)

        return len(drafts)

    async def start_game(self, request: StartGameRequest, user_id: str,) -> StoryResponse:
        await self.cleanup_old_drafts(user_id)
        
        # Validate inputs
        self.safety_filter.validate_input(request.player_name, "Tên người chơi")
        self.safety_filter.validate_input(request.character_hint, "Mô tả nhân vật")
        self.safety_filter.validate_input(request.world_hint, "Mô tả thế giới")
        adventure_profile = build_adventure_profile(request)
        for key in ["starting_condition", "region", "objective", "threat", "loadout"]:
            self.safety_filter.validate_input(adventure_profile.get(key), f"Hồ sơ phiêu lưu ({key})")

        session = SessionState(
            session_id=str(uuid4()),
            user_id=user_id,
            is_saved=False,
            adventure_profile=adventure_profile,
            world_seed=adventure_profile.get("seed", ""),
            title=f"Câu chuyện của {request.player_name}",
        )
        await self.store.create_session(session)

        prompt = build_start_prompt(
            player_name=request.player_name,
            story_style=request.story_style,
            character_hint=request.character_hint,
            world_hint=request.world_hint,
            adventure_profile=adventure_profile,
            gender=request.gender,
            personality=request.personality,
        )

        raw = await self._generate_text_logged(
            prompt,
            user_id=user_id,
            session_id=session.session_id,
            operation="start_adventure.main",
        )
        parsed = parse_story_output(raw)

        foundation_text = self.safety_filter.censor_output(parsed["foundation"])
        ai_text = self.safety_filter.censor_output(parsed["story"])
        choices = [self.safety_filter.censor_output(c) for c in parsed["choices"]]
        session.adventure_profile = merge_survival_update(
            session.adventure_profile,
            parsed.get("survival_update"),
        )

        if foundation_text:
            session.foundation_text = foundation_text
            session.world_summary = foundation_text
            session.character_summary = foundation_text
            session.story_summary = "The story has just begun."
            session.important_facts = list(dict.fromkeys(session.important_facts + [foundation_text]))[-12:]
            session.updated_at = utc_now_iso()
            await self.store.update_session(session)
        else:
            session.updated_at = utc_now_iso()
            await self.store.update_session(session)

        foundation_message = Message(
            message_id=str(uuid4()),
            session_id=session.session_id,
            role="system",
            content=f"Story foundation profile:\n{foundation_text}" if foundation_text else "Story foundation profile is not clearly.",
        )
        await self.store.add_message(foundation_message)

        ai_message = Message(
            message_id=str(uuid4()),
            session_id=session.session_id,
            role="ai",
            content=ai_text,
            choices=choices,
        )
        await self.memory.save_message(ai_message)

        import asyncio
        asyncio.create_task(self.memory.refresh_summary(session))

        return StoryResponse(
            session_id=session.session_id,
            message=ai_text,
            choices=choices,
            foundation_text=session.foundation_text,
            session=session,
            message_id=ai_message.message_id,
        )

    async def continue_story(self, request: TurnRequest, user_id: str, ) -> StoryResponse:
        self.safety_filter.validate_input(request.player_input, "Hành động của người chơi")
        session = await self.store.get_session(request.session_id)
        if session is None:
            raise ValueError("Session not found")
        if session.user_id != user_id:
            raise PermissionError("You do not own this session")
        user_message = Message(
            message_id=str(uuid4()),
            session_id=request.session_id,
            role="user",
            content=request.player_input,
        )
        await self.memory.save_message(user_message)

        recent = await self.memory.recent_messages(request.session_id)
        query = f"{request.player_input}\n{session.foundation_text}\n{session.story_summary}\n{session.character_summary}"
        relevant = await self.memory.relevant_memories(request.session_id, query)

        critical_instruction = ""
        if session.mode == "adventure" and session.adventure_profile:
            wounds = int(session.adventure_profile.get("wounds") or 0)
            supplies = int(session.adventure_profile.get("supplies") or 3)
            
            if wounds >= 5:
                critical_instruction = (
                    "The player is severely wounded and collapsed. "
                    "You must narrate them losing consciousness or being defeated, and then being rescued or recovering in a safe place (such as a medical tent, shelter, or saved by a kind stranger). "
                    "You MUST adjust their wounds down to 3 in the survival_update to represent this recovery, and possibly deduct some supplies or tools to reflect the cost of rescue. "
                    "Make sure this rescue makes narrative sense."
                )
            elif supplies <= 0:
                critical_instruction = (
                    "The player has run out of supplies (starvation). "
                    "You must narrate their extreme hunger, fatigue, and desperation. "
                    "The choices provided must force them into highly risky scenarios to obtain food/supplies. "
                    "You MUST increase their danger level or wounds in the survival_update to represent the physical toll, "
                    "but give them a way to find at least 1 supply in the choices or outcome if they choose the desperate path."
                )

        prompt = build_turn_prompt(
                session,
                recent,
                relevant,
                request.player_input,
                target_words=request.target_words,
                critical_instruction=critical_instruction,
            )
        raw = await self._generate_text_logged(
            prompt,
            user_id=user_id,
            session_id=session.session_id,
            operation="turn.main",
        )
        parsed = parse_story_output(raw)

        ai_text = self.safety_filter.censor_output(parsed["story"])
        choices = [self.safety_filter.censor_output(c) for c in parsed["choices"]]
        if session.mode == "adventure":
            session.adventure_profile = merge_survival_update(
                session.adventure_profile,
                parsed.get("survival_update"),
            )

        ai_message = Message(
            message_id=str(uuid4()),
            session_id=request.session_id,
            role="ai",
            content=ai_text,
            choices=choices,
        )
        await self.memory.save_message(ai_message)

        session.updated_at = utc_now_iso()
        await self.store.update_session(session)
        import asyncio
        asyncio.create_task(self.memory.refresh_summary(session))

        return StoryResponse(
            session_id=session.session_id,
            message=ai_text,
            choices=choices,
            foundation_text=session.foundation_text,
            session=session,
            message_id=ai_message.message_id,
        )

    async def get_session(self, session_id: str, user_id: str,):
        session = await self.store.get_session(session_id)
        if session is None:
            raise ValueError("Session not found")
        if session.user_id != user_id:
            raise PermissionError("You do not own this session")
        messages = await self.store.get_messages(session_id, limit=100)
        return session, messages
    async def debug_memory(self, session_id: str):
        session = await self.store.get_session(session_id)
        if session is None:
            raise ValueError("Session not found")

        messages = await self.store.get_messages(session_id, limit=30)
        memories = await self.vector_store.list_memories(session_id, limit=100)

        return {
            "session": session,
            "messages": messages,
            "memories": memories,
        }
    async def list_sessions(self, user_id: str):
        await self.cleanup_old_drafts(user_id)

        return await self.store.list_sessions(
                user_id=user_id,
                limit=30,
            )
    async def save_session(self, session_id: str, user_id: str, title: str | None = None,):
        session = await self.store.get_session(session_id)

        if session is None:
            raise ValueError("Session not found")
        if session.user_id != user_id:
            raise PermissionError("You do not own this session")

        if title is not None:
            session.title = title

        session.is_saved = True
        session.updated_at = utc_now_iso()
        await self.store.update_session(session)
        await self.cleanup_old_drafts(user_id)

        return session

    async def rename_session(self, session_id: str, user_id: str, title: str,):
        session = await self.store.get_session(session_id)

        if session is None:
            raise ValueError("Session not found")
        if session.user_id != user_id:
            raise PermissionError("You do not own this session")
        if not session.is_saved:
            raise ValueError("Only saved History items can be renamed")

        session.title = title
        session.updated_at = utc_now_iso()
        await self.store.update_session(session)

        return session

    async def delete_session(self, session_id: str, user_id: str,):
        session = await self.store.get_session(session_id)

        if session is None:
            raise ValueError("Session not found")
        if session.user_id != user_id:
            raise PermissionError("You do not own this session")

        await self.vector_store.delete_memories(session_id)
        await self.store.delete_session(session_id)

        return {"success": True}
    def _parse_json(self, raw: str) -> dict:
        from app.ai.output_parser import _try_parse_json
        data = _try_parse_json(raw)
        if isinstance(data, dict):
            return data
        text = raw.strip()
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)
    async def start_novel_world(
        self,
        request: NovelStartRequest,
        user_id: str,
    ) -> NovelWorldResponse:
        await self.cleanup_old_drafts(user_id)
        self.safety_filter.validate_input(request.title, "Tiêu đề tiểu thuyết")
        self.safety_filter.validate_input(request.world_seed, "Bối cảnh thế giới")

        session = SessionState(
            session_id=str(uuid4()),
            user_id=user_id,
            mode="novel",
            is_saved=False,
            title=request.title or "Untitled Novel",
            world_seed=request.world_seed or "",
            target_words=request.target_words,
        )

        await self.store.create_session(session)

        prompt = build_novel_world_prompt(request.world_seed)
        raw = await self._generate_text_logged(
            prompt,
            user_id=user_id,
            session_id=session.session_id,
            operation="novel_world.main",
        )
        data = self._parse_json(raw)

        world_draft = self.safety_filter.censor_output(data.get("world_draft", ""))
        questions = [self.safety_filter.censor_output(q) for q in data.get("questions", [])]

        session.world_summary = world_draft
        session.world_questions = questions
        session.novel_profile = {
            "world_draft": world_draft,
            "questions": questions,
        }
        session.updated_at = utc_now_iso()

        await self.store.update_session(session)

        return NovelWorldResponse(
            session_id=session.session_id,
            world_draft=world_draft,
            questions=questions,
            session=session,
        )
    async def create_novel_foundation(
        self,
        request: NovelFoundationRequest,
        user_id: str,
    ) -> StoryResponse:
        self.safety_filter.validate_input(request.player_name, "Tên nhân vật")
        self.safety_filter.validate_input(request.occupation, "Nghề nghiệp")
        self.safety_filter.validate_input(request.personality, "Tính cách")
        for ans in request.answers:
            self.safety_filter.validate_input(ans.answer, f"Câu trả lời cho câu hỏi '{ans.question}'")

        session = await self.store.get_session(request.session_id)

        if session is None:
            raise ValueError("Session not found")

        if session.user_id != user_id:
            raise PermissionError("You do not own this session")

        answers = [a.model_dump() for a in request.answers]

        session.world_answers = answers
        session.target_words = request.target_words

        prompt = build_novel_foundation_prompt(
            session=session,
            player_name=request.player_name,
            gender=request.gender,
            age=request.age,
            occupation=request.occupation,
            personality=request.personality,
            answers=answers,
            target_words=request.target_words,
        )

        raw = await self._generate_text_logged(
            prompt,
            user_id=user_id,
            session_id=session.session_id,
            operation="novel_foundation.main",
        )
        data = self._parse_json(raw)

        foundation_text = self.safety_filter.censor_output(data.get("foundation", ""))
        novel_profile = data.get("novel_profile", {})
        if isinstance(novel_profile, dict):
            if "protagonist" in novel_profile and isinstance(novel_profile["protagonist"], dict):
                for k, v in novel_profile["protagonist"].items():
                    if isinstance(v, str):
                        novel_profile["protagonist"][k] = self.safety_filter.censor_output(v)
            if "world" in novel_profile and isinstance(novel_profile["world"], dict):
                for k, v in novel_profile["world"].items():
                    if isinstance(v, str):
                        novel_profile["world"][k] = self.safety_filter.censor_output(v)

        ai_text = self.safety_filter.censor_output(data.get("story", ""))
        choices = [self.safety_filter.censor_output(c) for c in data.get("choices", [])]

        session.foundation_text = foundation_text
        session.novel_profile = novel_profile
        session.character_summary = json.dumps(
            novel_profile.get("protagonist", {}),
            ensure_ascii=False,
        )
        session.story_summary = "The novel has just begun."
        session.important_facts = [foundation_text]
        session.updated_at = utc_now_iso()

        await self.store.update_session(session)

        foundation_message = Message(
            message_id=str(uuid4()),
            session_id=session.session_id,
            role="system",
            content=f"Novel foundation profile:\n{foundation_text}",
        )
        await self.store.add_message(foundation_message)

        ai_message = Message(
            message_id=str(uuid4()),
            session_id=session.session_id,
            role="ai",
            content=ai_text,
            choices=choices,
        )
        await self.memory.save_message(ai_message)

        import asyncio
        asyncio.create_task(self.memory.refresh_summary(session))

        return StoryResponse(
            session_id=session.session_id,
            message=ai_text,
            choices=choices,
            foundation_text=session.foundation_text,
            session=session,
            message_id=ai_message.message_id,
        )

    async def translate_prompt_to_english(self, prompt: str) -> str:
        translation_prompt = (
            f"You are a translation assistant. Translate the following image generation prompt from Vietnamese to English. "
            f"Provide only the translation, no extra comments, explanations or formatting.\n"
            f"Vietnamese Prompt: {prompt}"
        )
        try:
            import asyncio
            english = await asyncio.wait_for(
                self.provider.generate_text(translation_prompt),
                timeout=3.0
            )
            english = english.strip()
            if english.startswith('"') and english.endswith('"'):
                english = english[1:-1].strip()
            if english.startswith("'") and english.endswith("'"):
                english = english[1:-1].strip()
            return english
        except Exception as exc:
            import logging
            logging.getLogger("ai_story.translate").warning(
                "Failed to translate illustration prompt to English (falling back to raw prompt): %s", exc
            )
            return prompt

    async def illustrate_message(
        self,
        session_id: str,
        message_id: str,
        prompt: str,
        user: dict,
    ) -> str:
        app_settings = await self.admin_control.store.get_app_settings()
        if not app_settings.image_enabled:
            raise ValueError("Image generation feature is currently disabled by Admin.")

        user_state = await self.admin_control.store.get_admin_user_state(user["uid"])
        if not user_state:
            user_state = await self.admin_control.ensure_user_state(user)

        cost = app_settings.cost_image_generation
        is_admin = bool(user.get("admin"))

        if app_settings.points_enabled and not is_admin:
            if user_state.points_balance < cost:
                raise ValueError(
                    f"Insufficient coins. Cost is {cost} coins, but you only have {user_state.points_balance} coins."
                )

        messages = await self.store.get_messages(session_id, limit=200)
        target_message = None
        for m in messages:
            if m.message_id == message_id:
                target_message = m
                break

        if not target_message:
            raise ValueError("Target message not found in session history.")

        self.safety_filter.validate_input(prompt, "Mô tả ảnh")

        if app_settings.points_enabled and not is_admin:
            await self.admin_control.adjust_points(
                target_uid=user["uid"],
                delta=-cost,
                reason=f"Generated scene illustration for message {message_id}",
                action="image.generation",
                actor=user,
                session_id=session_id,
            )

        english_prompt = await self.translate_prompt_to_english(prompt)

        import urllib.parse
        import random
        encoded_prompt = urllib.parse.quote(english_prompt)
        seed = random.randint(1, 999999)
        image_url = f"https://image.pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&nologo=true&seed={seed}"

        target_message.image_url = image_url
        await self.store.add_message(target_message)

        return image_url


def estimate_token_count(value: str) -> int:
    text = str(value or "")
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)
