from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator
from app.domain.models import (
    AIUsageLogEntry,
    AdminUserState,
    AppSettingsState,
    AuditLogEntry,
    CommunityWorld,
    Message,
    PointsLedgerEntry,
    SessionState,
)

class StartGameRequest(BaseModel):
    player_name: str = Field(default="Người lữ hành", min_length=1, max_length=80)
    gender: str | None = Field(default=None, max_length=120)
    personality: str | None = Field(default=None, max_length=300)
    story_style: str | None = Field(default=None, max_length=200)
    character_hint: str | None = Field(default=None, max_length=1000)
    world_hint: str | None = Field(default=None, max_length=1000)
    adventure_profile: dict[str, Any] | None = None

class TurnRequest(BaseModel):
    session_id: str
    player_input: str = Field(min_length=1, max_length=4000)
    target_words: int = Field(default=600, ge=100, le=2000)

class StoryResponse(BaseModel):
    session_id: str
    message: str
    choices: list[str] = Field(default_factory=list)
    foundation_text: str = ""
    session: SessionState
    message_id: str | None = None

class SessionResponse(BaseModel):
    session: SessionState
    messages: list[Message]


class SessionSaveRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str | None) -> str | None:
        if value is None:
            return None

        title = value.strip()

        if not title:
            raise ValueError("Title is required")

        return title


class SessionRenameRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def clean_title(cls, value: str) -> str:
        title = value.strip()

        if not title:
            raise ValueError("Title is required")

        return title


class WorldCatalogItem(BaseModel):
    id: str
    title: str
    mode: str
    description: str
    world_seed: str
    long_description: str = ""
    image: str = ""
    tags: list[str] = Field(default_factory=list)


class NovelStartRequest(BaseModel):
    title: str | None = Field(default=None, max_length=120)
    world_seed: str | None = Field(default=None, max_length=4000)
    target_words: int = Field(default=600, ge=150, le=2000)


class NovelQuestionAnswer(BaseModel):
    question_id: str
    question: str
    answer: str


class NovelWorldResponse(BaseModel):
    session_id: str
    world_draft: str
    questions: list[dict] = Field(default_factory=list)
    session: SessionState


class NovelFoundationRequest(BaseModel):
    session_id: str
    player_name: str = Field(default="The Wanderer", min_length=1, max_length=80)
    gender: str | None = Field(default=None, max_length=120)
    age: str | None = Field(default=None, max_length=80)
    occupation: str | None = Field(default=None, max_length=160)
    personality: str | None = Field(default=None, max_length=500)
    answers: list[NovelQuestionAnswer] = Field(default_factory=list)
    target_words: int = Field(default=600, ge=150, le=2000)


class AdminSessionListItem(BaseModel):
    session_id: str
    user_id: str
    title: str
    mode: str
    is_saved: bool
    created_at: str
    updated_at: str
    target_words: int
    preview: str
    summary_source: str


class AdminSessionsResponse(BaseModel):
    items: list[AdminSessionListItem]
    count: int
    next_before: str | None = None


class AdminUserListItem(BaseModel):
    uid: str
    email: str | None = None
    name: str | None = None
    provider: str | None = None
    points_balance: int = 0
    is_banned: bool = False
    ban_reason: str = ""
    last_seen_at: str | None = None
    saved_sessions: int = 0
    draft_sessions: int = 0
    latest_session_at: str | None = None
    usage_today: int = 0
    usage_30d: int = 0
    estimated_tokens_today: int = 0
    estimated_tokens_30d: int = 0


class AdminUsersResponse(BaseModel):
    items: list[AdminUserListItem]
    count: int


class ReadinessCheckItem(BaseModel):
    check_id: str
    label: str
    status: str
    message: str
    hint: str = ""


class ReadinessReport(BaseModel):
    app_env: str
    storage_mode: str
    overall_status: str
    production_ready: bool
    generated_at: str
    checks: list[ReadinessCheckItem] = Field(default_factory=list)


class AdminOverviewResponse(BaseModel):
    app_name: str
    app_env: str = "local"
    storage_mode: str
    text_provider: str
    text_model: str
    embedding_provider: str
    catalog_count: int
    sessions_total: int
    sessions_saved: int
    sessions_draft: int
    sessions_adventure: int
    sessions_novel: int
    users_total: int
    users_banned: int
    total_points_balance: int
    usage_today: int = 0
    usage_errors_today: int = 0
    estimated_tokens_today: int = 0
    estimated_tokens_30d: int = 0
    points_spent_today: int = 0
    latest_updated_at: str | None = None
    settings: AppSettingsState
    readiness: ReadinessReport | None = None


class AdminPointsAdjustRequest(BaseModel):
    delta: int = Field(ge=-100000, le=100000)
    reason: str = Field(min_length=1, max_length=240)

    @field_validator("delta")
    @classmethod
    def non_zero_delta(cls, value: int) -> int:
        if value == 0:
            raise ValueError("Delta must not be zero")
        return value

    @field_validator("reason")
    @classmethod
    def clean_reason(cls, value: str) -> str:
        reason = value.strip()
        if not reason:
            raise ValueError("Reason is required")
        return reason


class AdminBanRequest(BaseModel):
    reason: str = Field(default="", max_length=240)

    @field_validator("reason")
    @classmethod
    def clean_ban_reason(cls, value: str) -> str:
        return value.strip()


class AdminSettingsUpdateRequest(BaseModel):
    maintenance_enabled: bool | None = None
    maintenance_message: str | None = Field(default=None, max_length=300)
    points_enabled: bool | None = None
    cost_start_adventure: int | None = Field(default=None, ge=0, le=100000)
    cost_novel_world: int | None = Field(default=None, ge=0, le=100000)
    cost_novel_foundation: int | None = Field(default=None, ge=0, le=100000)
    cost_turn: int | None = Field(default=None, ge=0, le=100000)
    cost_image_generation: int | None = Field(default=None, ge=0, le=100000)
    image_enabled: bool | None = None
    rate_limit_enabled: bool | None = None
    daily_turn_limit: int | None = Field(default=None, ge=0, le=100000)
    daily_create_limit: int | None = Field(default=None, ge=0, le=100000)
    usage_log_retention_days: int | None = Field(default=None, ge=1, le=365)

    @field_validator("maintenance_message")
    @classmethod
    def clean_maintenance_message(cls, value: str | None) -> str | None:
        if value is None:
            return None
        message = value.strip()
        if not message:
            raise ValueError("Maintenance message must not be empty")
        return message


class AdminLedgerResponse(BaseModel):
    items: list[PointsLedgerEntry]
    count: int


class AdminAuditResponse(BaseModel):
    items: list[AuditLogEntry]
    count: int


class AdminUsageTotals(BaseModel):
    requests: int = 0
    successes: int = 0
    errors: int = 0
    blocked: int = 0
    estimated_input_tokens: int = 0
    estimated_output_tokens: int = 0
    actual_input_tokens: int = 0
    actual_output_tokens: int = 0
    points_spent: int = 0


class AdminUsageResponse(BaseModel):
    today: AdminUsageTotals
    last_30d: AdminUsageTotals
    items: list[AIUsageLogEntry]
    count: int


class AdminUsageUserItem(BaseModel):
    uid: str
    email: str | None = None
    name: str | None = None
    requests_today: int = 0
    requests_30d: int = 0
    errors_today: int = 0
    estimated_tokens_today: int = 0
    estimated_tokens_30d: int = 0
    points_spent_today: int = 0
    points_spent_30d: int = 0


class AdminUsageUsersResponse(BaseModel):
    items: list[AdminUsageUserItem]
    count: int


class AdminErrorsResponse(BaseModel):
    items: list[AIUsageLogEntry]
    count: int
