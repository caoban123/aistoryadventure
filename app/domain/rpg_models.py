from __future__ import annotations
from typing import Literal, Any
from pydantic import BaseModel, Field, model_validator

# ==================== ENUMS / CONSTANTS ====================
Rarity = Literal["Mythic", "Legendary", "Epic", "Rare", "Uncommon", "Common"]
Race = Literal["Valkyrie", "Angel", "Devil", "Elf", "Royalty", "Orc", "Goblin", "Human"]
CharClass = Literal["Defender", "Guard", "Caster", "Sniper", "Supporter", "Specialist"]
ItemType = Literal["Weapon", "Armor", "Consume"]
Condition = Literal["Bình thường", "Mệt mỏi", "Rất yếu"]

RARITY_COLORS = {
    "Mythic": "#FF0000",      # Đỏ
    "Legendary": "#FFD700",   # Vàng
    "Epic": "#9B59B6",        # Tím
    "Rare": "#3498DB",        # Xanh dương
    "Uncommon": "#2ECC71",    # Xanh lá
    "Common": "#BDC3C7",      # Trắng/Xám
}

# ==================== ITEM MODEL ====================
class RPGItem(BaseModel):
    item_id: str
    name: str
    rarity: str
    item_type: str  # Weapon / Armor / Consume
    stats_bonus: dict[str, float] = Field(default_factory=dict)
    description: str = ""
    quantity: int = 1
    sell_price: int = 0
    buy_price: int = 0

# ==================== EQUIPMENT ====================
class RPGEquipment(BaseModel):
    weapon: RPGItem | None = None
    armor: RPGItem | None = None
    consume: RPGItem | None = None

# ==================== BUFF / DEBUFF ====================
class RPGBuff(BaseModel):
    name: str  # "Lá chắn", "Chữa lành", "Cứng cáp", "Lá chắn phép", "Siêu cấp hồi phục", "Gia tăng sĩ khí"
    duration: int | None = None  # None = chỉ dùng 1 lần rồi biến mất, int = số turn còn lại

class RPGDebuff(BaseModel):
    name: str  # "Chảy máu", "Thiêu đốt", "Tê liệt", "Choáng", "Chậm chạp", "Yếu đuối", "Sợ hãi", "Giá lạnh", "Đông cứng"
    duration: int | None = None  # None = no limit (chỉ xóa bằng skill/item)

# ==================== CHARACTER STATS ====================
class RPGCharacterStats(BaseModel):
    max_hp: int = 100
    hp: int = 100
    atk: int = 10
    res: int = 0       # Magic attack (Supporter: heal %)
    defense: int = 30   # DEF as percentage (0-90)
    res_def: int = 20   # Magic DEF as percentage (0-70)
    atk_spd: int = 20

# ==================== SPECIAL SKILL DATA ====================
class RPGSpecialSkills(BaseModel):
    """Dữ liệu skill đặc biệt theo race"""
    passive_skill: str | None = None
    passive_activated: bool = False  # True = đã kích hoạt (1 lần duy nhất)
    
    skill_1: str | None = None
    skill_1_countdown: int = 0       # > 0 = đang hồi chiêu
    skill_1_activated: bool = False   # cho skill dùng 1 lần
    skill_1_activating: bool = False  # Lemuen: đang bắn liên tiếp
    
    skill_2: str | None = None
    skill_2_countdown: int = 0
    
    # Đặc biệt cho từng nhân vật
    quan_co_count: int = 0            # Wang: bộ đếm quân cờ
    bullet_count: int = 0             # Lemuen: bộ đếm viên đạn (max 5)
    hoshi_passive_countdown: int = 0  # Hoshiguma: đếm ngược hồi sinh
    lemuen_auto_shots: int = 0        # Lemuen: số phát bắn tự động còn lại


# ==================== CHARACTER ====================
class RPGCharacter(BaseModel):
    character_id: str
    name: str
    race: str
    char_class: str
    rarity: str
    gender: str = "Male"
    condition: str = "Bình thường"
    description: str = ""
    
    level: int = 1
    exp: int = 0
    max_level: int = 99
    
    stats: RPGCharacterStats = Field(default_factory=RPGCharacterStats)
    base_stats: RPGCharacterStats | None = None  # Lưu stats gốc cho combat
    
    buffs: list[RPGBuff] = Field(default_factory=list)
    debuffs: list[RPGDebuff] = Field(default_factory=list)
    equipment: RPGEquipment = Field(default_factory=RPGEquipment)
    
    image_url: str | None = None
    special_skills: RPGSpecialSkills = Field(default_factory=RPGSpecialSkills)
    
    is_player_character: bool = False

    @model_validator(mode="after")
    def set_dynamic_max_level(self) -> RPGCharacter:
        if self.character_id == "player" or self.is_player_character:
            self.max_level = 99
        else:
            rarity_max = {
                "Mythic": 90,
                "Legendary": 80,
                "Epic": 70,
                "Rare": 60,
                "Uncommon": 55,
                "Common": 50
            }
            self.max_level = rarity_max.get(self.rarity, 50)
        return self

# ==================== PARTY ====================
class RPGParty(BaseModel):
    active: list[RPGCharacter] = Field(default_factory=list)    # max 4
    reserve: list[RPGCharacter] = Field(default_factory=list)   # max 5

# ==================== INVENTORY ====================
class RPGInventory(BaseModel):
    items: list[RPGItem] = Field(default_factory=list)
    gold: int = 0

# ==================== SHOP ====================
class RPGShopState(BaseModel):
    level: int = 1
    items_for_sale: list[RPGItem] = Field(default_factory=list)
    mercenaries_for_sale: list[RPGCharacter] = Field(default_factory=list)

# ==================== COMBAT STATE ====================
class RPGCombatState(BaseModel):
    cb_turn_count: int = 0
    combat_party: list[RPGCharacter] = Field(default_factory=list)
    enemy: RPGCharacter | None = None
    combat_log: list[str] = Field(default_factory=list)
    is_active: bool = True
    enemy_feared: bool = False  # Sư tử hống: cấm kẻ thù tấn công turn này

# ==================== RPG GAME STATE ====================
class RPGGameState(BaseModel):
    """Toàn bộ trạng thái 1 phiên RPG"""
    turn_count: int = 0
    past_turn_is_special: bool = False
    
    party: RPGParty = Field(default_factory=RPGParty)
    inventory: RPGInventory = Field(default_factory=RPGInventory)
    shop: RPGShopState = Field(default_factory=RPGShopState)
    
    combat: RPGCombatState | None = None
    
    player_character: RPGCharacter | None = None
    
    current_event: str | None = None  # "monk" / "merchant" / "stranger" / "item" / "normal" / None
    offered_event: str | None = None  # Sự kiện đang được đề xuất ở lượt trước (chưa kích hoạt)
    sympathy: int = 0  # Mức độ thiện cảm kẻ lạ mặt
    current_stranger: RPGCharacter | None = None  # NPC kẻ lạ mặt hiện tại
    current_monk: RPGCharacter | None = None  # NPC tu sĩ hiện tại
    current_merchant: RPGCharacter | None = None  # NPC thương nhân hiện tại
    bypass_region_turn: bool = False  # Bỏ qua kiến trúc ở lượt trước, chặn xúc xắc kiến trúc ở lượt này
    region: str = ""
    objective: str = ""
    
    # Update 1-1 Map, Quest, Dungeon & Achievement additions
    environment: str = ""
    current_region: str | None = None
    explored_regions: list[str] = Field(default_factory=list)
    unlocked_fast_travel: list[str] = Field(default_factory=list)
    dungeon_state: dict[str, Any] | None = None
    active_quests: list[dict[str, Any]] = Field(default_factory=list)
    achievements_progress: dict[str, Any] = Field(default_factory=dict)
    debug_cheats: dict[str, Any] = Field(default_factory=dict)
    dummy_combat_backup: RPGParty | None = None


