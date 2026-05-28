from __future__ import annotations
from typing import Any
from pydantic import BaseModel, Field

# ==================== REQUEST SCHEMAS ====================

class RPGStartRequest(BaseModel):
    player_name: str = Field(default="Người lữ hành", min_length=1, max_length=80)
    gender: str = "Male"  # Male/Female/No mention
    region: str | None = None  # Starting region
    objective: str | None = None  # Objective
    appearance_desc: str | None = None  # Appearance description

class RPGTurnRequest(BaseModel):
    session_id: str
    choice_index: int = Field(ge=0, le=2)  # 0, 1, 2

class RPGPromptTurnRequest(BaseModel):
    session_id: str
    player_input: str = Field(min_length=1, max_length=4000)
    target_words: int = Field(default=600, ge=100, le=2000)

class RPGEventActionRequest(BaseModel):
    session_id: str
    action: str  # Action name (e.g. "Trò chuyện", "Nhận phước lành", "Tạm biệt", "Tấn công", "Xem hàng hóa", "Tránh xung đột", "Thu thập")

class RPGCombatActionRequest(BaseModel):
    session_id: str
    attacker_id: str
    skill_name: str  # "basic_attack", "skill_1", "skill_2"
    target_id: str
    defender_id: str | None = None

class RPGShopBuyRequest(BaseModel):
    session_id: str
    item_index: int

class RPGShopBuyMercRequest(BaseModel):
    session_id: str
    merc_index: int

class RPGShopSellRequest(BaseModel):
    session_id: str
    item_id: str

class RPGPartySwapRequest(BaseModel):
    session_id: str
    from_position: str  # "active_0", "reserve_1", etc.
    to_position: str

class RPGEquipRequest(BaseModel):
    session_id: str
    character_id: str
    item_id: str

# ==================== RESPONSE SCHEMAS ====================

class RPGTurnResponse(BaseModel):
    session_id: str
    story: str
    choices: list[str]
    rpg_state: dict[str, Any]
    event_type: str | None = None
    message_id: str | None = None

class RPGCombatResponse(BaseModel):
    session_id: str
    combat_log: list[str]
    combat_state: dict[str, Any]
    is_combat_over: bool = False
    result: str | None = None  # "win" / "lose" / None
    story: str | None = None
    rpg_state: dict[str, Any] | None = None

class RPGShopResponse(BaseModel):
    session_id: str
    shop: dict[str, Any]
    inventory: dict[str, Any]
    message: str = ""
    rpg_state: dict[str, Any] | None = None
