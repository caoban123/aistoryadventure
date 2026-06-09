from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Any
from pydantic import BaseModel, Field, model_validator


Role = Literal["user", "ai", "system"]

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class NPCState(BaseModel):
    npc_id: str
    name: str
    status: Literal["alive", "dead", "missing", "unknown"] = "alive"
    relationship_score: int = 0
    known_information: list[str] = Field(default_factory=list)

class StructuredState(BaseModel):
    current_location: str = "Unknown"
    current_quest: str = ""
    npcs: dict[str, NPCState] = Field(default_factory=dict)
    critical_choices: list[str] = Field(default_factory=list)

    inventory: list[str] = Field(default_factory=list)
    bosses_defeated: list[str] = Field(default_factory=list)

    emotional_states: dict[str, str] = Field(default_factory=dict)
    branching_flags: dict[str, bool] = Field(default_factory=dict)

    @model_validator(mode='before')
    @classmethod
    def clean_state(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # 1. Clean up critical_choices: if item is dict, extract its value
        if "critical_choices" in data and isinstance(data["critical_choices"], list):
            cleaned_choices = []
            for item in data["critical_choices"]:
                if isinstance(item, dict):
                    val = item.get("choice") or item.get("text") or next(iter(item.values()), str(item))
                    cleaned_choices.append(str(val))
                else:
                    cleaned_choices.append(str(item))
            data["critical_choices"] = cleaned_choices

        # 2. Clean up emotional_states: convert values to string
        if "emotional_states" in data and isinstance(data["emotional_states"], dict):
            cleaned_emotions = {}
            for k, v in data["emotional_states"].items():
                if isinstance(v, dict):
                    v = v.get("level") or v.get("value") or next(iter(v.values()), str(v))
                cleaned_emotions[str(k)] = str(v)
            data["emotional_states"] = cleaned_emotions

        return data

class Message(BaseModel):
    message_id: str
    session_id: str
    role: Role
    content: str
    choices: list[str] = Field(default_factory=list)
    image_url: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)

class SessionState(BaseModel):
    session_id: str
    user_id: str

    title: str = "Cuộc phiêu lưu chưa đặt tên"
    foundation_text: str = ""

    world_summary: str = ""
    character_summary: str = ""
    story_summary: str = ""
    rolling_story_summary: str = ""

    important_facts: list[str] = Field(default_factory=list)

    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    is_saved: bool = True
    
    mode: Literal["adventure", "novel", "rpg"] = "adventure"
    rpg_state: dict[str, Any] = Field(default_factory=dict)

    world_seed: str = ""
    world_questions: list[dict[str, Any]] = Field(default_factory=list)
    world_answers: list[dict[str, Any]] = Field(default_factory=list)

    adventure_profile: dict[str, Any] = Field(default_factory=dict)
    novel_profile: dict[str, Any] = Field(default_factory=dict)
    target_words: int = 600

    structured_state: StructuredState = Field(default_factory=StructuredState)

class MemoryChunk(BaseModel):
    chunk_id: str
    session_id: str
    text: str
    kind: str = "event"
    importance: int = 3
    source_message_id: str | None = None
    location: str | None = None
    involved_npcs: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)


class AdminUserState(BaseModel):
    uid: str
    email: str | None = None
    name: str | None = None
    provider: str | None = None
    points_balance: int = 50
    is_banned: bool = False
    ban_reason: str = ""
    banned_at: str | None = None
    banned_by: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    last_seen_at: str = Field(default_factory=utc_now_iso)


class PointsLedgerEntry(BaseModel):
    entry_id: str
    uid: str
    delta: int
    balance_after: int
    reason: str
    action: str
    actor_uid: str | None = None
    session_id: str | None = None
    created_at: str = Field(default_factory=utc_now_iso)


class AIUsageLogEntry(BaseModel):
    entry_id: str
    uid: str
    session_id: str | None = None
    action: str
    operation: str
    provider: str
    model: str
    status: str
    error_kind: str | None = None
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    actual_input_tokens: int | None = None
    actual_output_tokens: int | None = None
    latency_ms: int = 0
    points_delta: int = 0
    created_at: str = Field(default_factory=utc_now_iso)


class AppSettingsState(BaseModel):
    settings_id: str = "app"
    maintenance_enabled: bool = False
    maintenance_message: str = "AI Story Adventure is under maintenance. Please come back soon."
    points_enabled: bool = False
    cost_start_adventure: int = 10
    cost_novel_world: int = 5
    cost_novel_foundation: int = 15
    cost_turn: int = 3
    cost_image_generation: int = 10
    image_enabled: bool = True
    rate_limit_enabled: bool = True
    daily_turn_limit: int = 20
    daily_create_limit: int = 5
    usage_log_retention_days: int = 30
    updated_at: str = Field(default_factory=utc_now_iso)
    updated_by: str | None = None


class AuditLogEntry(BaseModel):
    entry_id: str
    actor_uid: str
    actor_email: str | None = None
    action: str
    target_uid: str | None = None
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now_iso)


class CommunityWorld(BaseModel):
    id: str
    session_id: str | None = None
    title: str
    description: str
    mode: Literal["adventure", "novel"]
    tags: list[str] = Field(default_factory=list)
    world_seed: str = ""
    long_description: str = ""
    foundation_text: str = ""
    author_uid: str
    author_name: str
    is_approved: bool = False
    likes: int = 0
    liked_by: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)


class Announcement(BaseModel):
    id: str
    title: str
    content: str
    type: str  # "fixed" or "temporary"
    created_at: str = Field(default_factory=utc_now_iso)
    created_by: str


