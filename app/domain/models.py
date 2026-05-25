from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Any
from pydantic import BaseModel, Field


Role = Literal["user", "ai", "system"]

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

class Message(BaseModel):
    message_id: str
    session_id: str
    role: Role
    content: str
    choices: list[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=utc_now_iso)

class SessionState(BaseModel):
    session_id: str
    user_id: str

    title: str = "Cuộc phiêu lưu chưa đặt tên"
    foundation_text: str = ""

    world_summary: str = ""
    character_summary: str = ""
    story_summary: str = ""

    important_facts: list[str] = Field(default_factory=list)

    created_at: str = Field(default_factory=utc_now_iso)
    updated_at: str = Field(default_factory=utc_now_iso)
    is_saved: bool = True
    
    mode: Literal["adventure", "novel"] = "adventure"

    world_seed: str = ""
    world_questions: list[dict[str, Any]] = Field(default_factory=list)
    world_answers: list[dict[str, Any]] = Field(default_factory=list)

    adventure_profile: dict[str, Any] = Field(default_factory=dict)
    novel_profile: dict[str, Any] = Field(default_factory=dict)
    target_words: int = 600

class MemoryChunk(BaseModel):
    chunk_id: str
    session_id: str
    text: str
    kind: str = "event"
    importance: int = 3
    source_message_id: str | None = None
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


