import random
import uuid
from typing import Literal, Any
from app.domain.rpg_models import (
    RPGCharacter, RPGCharacterStats, RPGItem, RPGEquipment,
    RPGBuff, RPGDebuff, RPGSpecialSkills, RPGParty, RPGInventory,
    RPGShopState, RPGCombatState, RPGGameState
)

# ==================== CONSTANTS & REFERENCE TABLES ====================

BASE_STATS = {
    "Defender":   {"max_hp": 100, "atk": 10, "defense": 60, "res": 0,  "res_def": 30, "atk_spd": 20},
    "Guard":      {"max_hp": 70,  "atk": 30, "defense": 30, "res": 10, "res_def": 10, "atk_spd": 30},
    "Caster":     {"max_hp": 55,  "atk": 10, "defense": 10, "res": 40, "res_def": 40, "atk_spd": 25},
    "Sniper":     {"max_hp": 55,  "atk": 45, "defense": 15, "res": 10, "res_def": 10, "atk_spd": 35},
    "Supporter":  {"max_hp": 60,  "atk": 5,  "defense": 10, "res": 10, "res_def": 30, "atk_spd": 27},
    "Specialist": {"max_hp": 65,  "atk": 21, "defense": 21, "res": 21, "res_def": 19, "atk_spd": 26},
}

RACE_CLASS_BONUS = {
    "Valkyrie": {
        "Defender": {"defense": 50, "max_hp": 50, "atk_spd": 50},
        "Guard":    {"atk": 50, "max_hp": 50, "defense": 20, "res_def": 20, "atk_spd": 10},
        "Caster":   {"res": 50, "max_hp": 20, "defense": 10, "res_def": 50, "atk_spd": 20},
        "Sniper":   {"atk": 60, "max_hp": 20, "defense": 20, "res_def": 10, "atk_spd": 40},
    },
    "Angel": {
        "_all": {"max_hp": 20, "atk": 30, "res": 30, "res_def": 30},
    },
    "Devil": {
        "_all": {"max_hp": 40, "atk": 20, "res": 20, "defense": 30},
    },
    "Elf": {
        "_all": {"atk": 20, "res": 20, "atk_spd": 40},
    },
    "Royalty": {
        "_all": {"max_hp": 10, "atk": 15, "defense": 10, "res": 15, "res_def": 10},
    },
    "Orc": {
        "_all": {"max_hp": 25, "defense": 10, "res": 5},
    },
    "Goblin": {
        "_all": {"max_hp": -10, "atk": 10, "defense": -5, "res_def": -5, "atk_spd": 10},
    },
    "Human": {
        "_all": {},
    },
}

RARITY_RACE_MAP = {
    "Mythic":    ["Valkyrie"],
    "Legendary": ["Angel", "Devil"],
    "Epic":      ["Elf"],
    "Rare":      ["Royalty"],
    "Uncommon":  ["Orc"],
    "Common":    ["Goblin", "Human"],
}

RACE_CLASSES = {
    "Valkyrie": ["Defender", "Guard", "Caster", "Sniper"],
    "Angel":    ["Guard", "Caster", "Sniper", "Supporter"],
    "Devil":    ["Defender", "Guard", "Caster"],
    "Elf":      ["Guard", "Caster", "Sniper", "Supporter"],
    "Royalty":  ["Defender", "Guard", "Caster", "Sniper", "Supporter"],
    "Orc":      ["Defender", "Guard", "Caster"],
    "Goblin":   ["Guard", "Sniper"],
    "Human":    ["Defender", "Guard", "Caster", "Sniper", "Supporter"],
}

RARITY_MAX_LEVEL = {
    "Mythic": 90, "Legendary": 80, "Epic": 70,
    "Rare": 60, "Uncommon": 55, "Common": 50,
}

MYTHIC_CHARACTERS = {
    "Defender": [{"name": "Hoshiguma the breacher", "gender": "Female"}],
    "Guard":    [
        {"name": "VinaVictoria", "gender": "Female"},
        {"name": "SilverAsh the Reignfrost", "gender": "Male"}
    ],
    "Caster":   [{"name": "Wang", "gender": "Male"}],
    "Sniper":   [{"name": "Lemuen", "gender": "Female"}],
}

DEF_CAPS = {
    "Defender":   {"defense": 80, "res_def": 70},
    "Guard":      {"defense": 60, "res_def": 50},
    "Caster":     {"defense": 40, "res_def": 50},
    "Sniper":     {"defense": 50, "res_def": 40},
    "Supporter":  {"defense": 30, "res_def": 30},
    "Specialist": {"defense": 50, "res_def": 50},
}

ITEM_CATALOG = {
    "Mythic": {
        "Weapon": {"name": "Thánh kiếm", "stats_bonus": {"atk": 40, "res": 30, "atk_spd": 20}, "description": "Tăng đáng kể ATK, RES và tốc độ đánh."},
        "Armor":  {"name": "Giáp Valkyrie", "stats_bonus": {"max_hp": 25, "defense": 30, "res_def": 35}, "description": "Bộ giáp tối thượng gia tăng chống chịu ma pháp lẫn vật lý."},
        "Consume": {"name": "Hiệu triệu", "description": "Hồi sinh 1 đồng đội đã tử trận với 100% HP."},
    },
    "Legendary": {
        "Weapon": {"name": "Thương sét", "stats_bonus": {"atk": 20, "res": 20, "atk_spd": 30}, "description": "Gia tăng tốc độ đánh và cả ATK lẫn RES."},
        "Armor":  {"name": "Giáp Quỷ", "stats_bonus": {"max_hp": 30, "defense": 20, "res_def": 20}, "description": "Gia tăng HP mạnh mẽ và phòng ngự cân bằng."},
        "Consume": {"name": "Thiết triệu", "description": "Hồi sinh 1 đồng đội với 5% HP."},
    },
    "Epic": {
        "Weapon": {"name": "Nỏ thần", "stats_bonus": {"atk": 30, "res": 10, "atk_spd": 10}, "description": "Tăng mạnh ATK cho người sử dụng."},
        "Armor":  {"name": "Giáp Elf", "stats_bonus": {"max_hp": 10, "defense": 10, "res_def": 30}, "description": "Giáp nhẹ nhàng, gia tăng mạnh phòng ngự ma pháp."},
        "Consume": {"name": "Bình nước thánh", "description": "Hồi 70% Max HP và hóa giải mọi hiệu ứng bất lợi."},
    },
    "Rare": {
        "Weapon": {"name": "Bảo kiếm", "stats_bonus": {"atk": 20, "atk_spd": 10}, "description": "Thanh kiếm sắc bén tăng ATK và tốc độ."},
        "Armor":  {"name": "Thiết trụ", "stats_bonus": {"defense": 20, "res_def": 5, "max_hp": 5}, "description": "Giáp thép nặng tăng mạnh phòng ngự vật lý."},
        "Consume": {"name": "Băng gạt", "description": "Xóa hiệu ứng Chảy máu và hồi 30% Max HP."},
    },
    "Uncommon": {
        "Weapon": {"name": "Chuỳ gai", "stats_bonus": {"atk": 15, "atk_spd": -5}, "description": "Vũ khí thô kệch tăng sát thương nhưng giảm nhẹ tốc độ đánh."},
        "Armor":  {"name": "Da thú", "stats_bonus": {"defense": 5, "res_def": 5}, "description": "Bộ da thú thô sơ tăng nhẹ phòng ngự."},
        "Consume": {"name": "Thịt thú nướng", "description": "Món ăn ngon miệng hồi lại 30% Max HP."},
    },
    "Common": {
        "Weapon": {"name": "Kiếm ngắn", "stats_bonus": {"atk": 5}, "description": "Kiếm gỗ/kiếm sắt ngắn tăng nhẹ ATK."},
        "Armor":  {"name": "Giáp thô sơ", "stats_bonus": {"defense": 5}, "description": "Quần áo vải dày tăng nhẹ phòng thủ."},
        "Consume": {"name": "Mẫu bánh mì", "description": "Hồi lại 20% Max HP."},
    },
}

BUY_PRICES = {"Mythic": 500, "Legendary": 400, "Epic": 300, "Rare": 150, "Uncommon": 80, "Common": 30}
SELL_PRICES = {"Mythic": 400, "Legendary": 300, "Epic": 200, "Rare": 90, "Uncommon": 50, "Common": 10}
MERC_PRICES = {"Mythic": 3999, "Legendary": 600, "Epic": 400, "Rare": 200, "Uncommon": 100, "Common": 50}

SHOP_UPGRADE_COSTS = {1: 25, 2: 60, 3: 90, 4: 100, 5: 120}
SHOP_SLOTS = {1: 4, 2: 5, 3: 6, 4: 6, 5: 6, 6: 6}

SHOP_RARITY_PROBS = {
    1: {"Mythic": 2, "Legendary": 5, "Epic": 10, "Rare": 15, "Uncommon": 25, "Common": 43},
    2: {"Mythic": 2, "Legendary": 5, "Epic": 10, "Rare": 15, "Uncommon": 25, "Common": 43},
    3: {"Mythic": 2, "Legendary": 5, "Epic": 10, "Rare": 15, "Uncommon": 25, "Common": 43},
    4: {"Mythic": 5, "Legendary": 8, "Epic": 13, "Rare": 18, "Uncommon": 28, "Common": 28},
    5: {"Mythic": 8, "Legendary": 11, "Epic": 15, "Rare": 21, "Uncommon": 31, "Common": 14},
    6: {"Mythic": 10, "Legendary": 15, "Epic": 20, "Rare": 25, "Uncommon": 20, "Common": 10},
}

# Note: EVENT_PROBS is deprecated. Active turn event probabilities are now dynamic
# and managed in app/services/rpg_service.py based on environment and region.

STRANGER_RARITY_PROBS = {
    "Mythic": 5, "Legendary": 8, "Epic": 10, "Rare": 15, "Uncommon": 20, "Common": 42
}

ITEM_FIND_RARITY_PROBS = {
    "Mythic": 2, "Legendary": 5, "Epic": 13, "Rare": 20, "Uncommon": 25, "Common": 35
}

DEFEND_CHANCES = {
    "Defender": 60, "Guard": 50, "Caster": 20,
    "Sniper": 20, "Supporter": 10, "Specialist": 40
}

BUFFS = {
    "Lá chắn":         {"duration": 1, "effect": "Sát thương nhận = 0 cho 1 lần"},
    "Chữa lành":       {"duration": 5, "effect": "Đầu turn hồi 5% HP đã mất"},
    "Cứng cáp":        {"duration": 2, "effect": "+20% DEF, +20% Res_DEF"},
    "Lá chắn phép":    {"duration": 3, "effect": "Miễn nhiễm Debuff"},
    "Siêu cấp hồi phục": {"duration": 3, "effect": "Đầu turn hồi 15% HP đã mất"},
    "Gia tăng sĩ khí": {"duration": 2, "effect": "+5% ATK, +5% DEF, +5% Atk_SPD"},
}

DEBUFFS = {
    "Chảy máu":  {"duration": None, "effect": "Đầu turn -10% HP hiện tại. Xóa bằng skill/item"},
    "Thiêu đốt": {"duration": 5,    "effect": "Đầu turn -15% HP hiện tại"},
    "Tê liệt":   {"duration": None, "effect": "Không chịu đòn, 50% miss khi tấn công. Xóa bằng skill/item"},
    "Choáng":     {"duration": 2,    "effect": "Không tấn công, không chịu đòn"},
    "Chậm chạp":  {"duration": 3,    "effect": "-50% Atk_SPD"},
    "Yếu đuối":  {"duration": 2,    "effect": "-10% ATK, -10% DEF, -10% Res_DEF"},
    "Sợ hãi":    {"duration": 3,    "effect": "Không tấn công, không chịu đòn"},
    "Giá lạnh":  {"duration": 6,    "effect": "-30% Atk_SPD cho mỗi tầng, cộng dồn tối đa 2 tầng"},
    "Đông cứng": {"duration": 1,    "effect": "Đứng im chịu trận, không thể né đòn/phản đòn, nhận x1.5 sát thương vật lý (x1.8 từ SilverAsh)"},
}

ENEMY_DEBUFF_CHANCE = {
    "Orc":      {"chance": 20, "debuffs": ["Choáng"]},
    "Royalty":  {"chance": 20, "debuffs": ["Chậm chạp", "Yếu đuối"]},
    "Elf":      {"chance": 30, "debuffs": ["Chảy máu", "Chậm chạp"]},
    "Devil":    {"chance": 36, "debuffs": ["Sợ hãi", "Thiêu đốt"]},
    "Angel":    {"chance": 36, "debuffs": ["Tê liệt", "Thiêu đốt"]},
    "Valkyrie": {"chance": 40, "debuffs": ["Chảy máu", "Thiêu đốt", "Sợ hãi"]},
    "Human":    {"chance": 0,  "debuffs": []},
    "Goblin":   {"chance": 0,  "debuffs": []},
}

DROP_TABLE = {
    "Mythic":    {"items": 5, "gold": 200, "exp": 200, "probs": {"Mythic":10,"Legendary":20,"Epic":25,"Rare":30,"Uncommon":10,"Common":5}},
    "Legendary": {"items": 4, "gold": 145, "exp": 145, "probs": {"Mythic":3,"Legendary":12,"Epic":20,"Rare":25,"Uncommon":30,"Common":10}},
    "Epic":      {"items": 3, "gold": 95,  "exp": 95,  "probs": {"Mythic":1,"Legendary":9,"Epic":15,"Rare":20,"Uncommon":35,"Common":20}},
    "Rare":      {"items": 3, "gold": 65,  "exp": 65,  "probs": {"Mythic":0,"Legendary":3,"Epic":7,"Rare":15,"Uncommon":45,"Common":30}},
    "Uncommon":  {"items": 2, "gold": 30,  "exp": 30,  "probs": {"Mythic":0,"Legendary":1,"Epic":4,"Rare":10,"Uncommon":25,"Common":60}},
    "Common":    {"items": 2, "gold": 15,  "exp": 15,  "probs": {"Mythic":0,"Legendary":0,"Epic":2,"Rare":8,"Uncommon":20,"Common":70}},
}


# ==================== GENERAL GAME ENGINE LOGIC ====================

class RPGEngine:

    @staticmethod
    def roll_by_probability(probs: dict[str, float]) -> str:
        """Rolls a random key based on a dictionary of key -> percentage/weight."""
        total = sum(probs.values())
        r = random.uniform(0, total)
        running_sum = 0.0
        for key, weight in probs.items():
            running_sum += weight
            if r <= running_sum:
                return key
        return list(probs.keys())[-1]

    @staticmethod
    def calculate_current_stats(character: RPGCharacter, active_party_size: int = 1) -> RPGCharacterStats:
        """
        Calculates character stats based on class, race, level, active equipment, and passive bonuses.
        Also handles Hoshiguma and VinaVictoria custom caps and passive bonuses.
        """
        # 1. Base Class Stats
        if character.base_stats is not None:
            stats_l1 = {
                "max_hp": character.base_stats.max_hp,
                "atk": character.base_stats.atk,
                "res": character.base_stats.res,
                "defense": character.base_stats.defense,
                "res_def": character.base_stats.res_def,
                "atk_spd": character.base_stats.atk_spd
            }
            current_stats = stats_l1.copy()
        else:
            cls_stats = BASE_STATS.get(character.char_class, BASE_STATS["Specialist"])
            
            # 2. Race / Class Multipliers
            race_bonuses = {}
            if character.race in RACE_CLASS_BONUS:
                race_data = RACE_CLASS_BONUS[character.race]
                if "_all" in race_data:
                    race_bonuses = race_data["_all"]
                elif character.char_class in race_data:
                    race_bonuses = race_data[character.char_class]
            
            stats_l1 = {}
            for stat in ["max_hp", "atk", "res", "defense", "res_def", "atk_spd"]:
                base_val = cls_stats.get(stat, 0)
                bonus_pct = race_bonuses.get(stat, 0)
                stats_l1[stat] = int(base_val * (1 + bonus_pct / 100))

            # 3. Add Level Bonuses
            level_scale = max(0, character.level - 1)
            growth_rate = 0.06 if character.is_player_character else 0.04
                
            current_stats = {}
            for stat in ["max_hp", "atk", "res", "defense", "res_def", "atk_spd"]:
                current_stats[stat] = int(stats_l1[stat] * (1 + level_scale * growth_rate))

        # 4. Equipment Bonuses
        equip_mods = {"max_hp": 0.0, "atk": 0.0, "res": 0.0, "defense": 0.0, "res_def": 0.0, "atk_spd": 0.0}
        for slot in ["weapon", "armor"]:
            item = getattr(character.equipment, slot)
            if item and item.stats_bonus:
                for stat, bonus in item.stats_bonus.items():
                    if stat in equip_mods:
                        equip_mods[stat] += bonus
                        
        final_stats = {}
        for stat in ["max_hp", "atk", "res", "defense", "res_def", "atk_spd"]:
            final_stats[stat] = int(current_stats[stat] * (1 + equip_mods[stat] / 100))

        # 5. Passive Skill Stat Adjustments
        # VinaVictoria Passive: Hoàng đế (+5% to all stats per ally in active party with HP > 0, max 3)
        if character.special_skills.passive_skill == "Hoàng đế" and active_party_size > 1:
            ally_count = min(active_party_size - 1, 3)
            vina_bonus = 0.05 * ally_count
            for stat in ["max_hp", "atk", "res", "defense", "res_def", "atk_spd"]:
                final_stats[stat] = int(final_stats[stat] * (1 + vina_bonus))

        # Orc Passive: Cuồng nộ (HP < 20%: +10% ATK/DEF/Res_DEF)
        if character.special_skills.passive_skill == "Cuồng nộ":
            if character.stats.max_hp > 0 and (character.stats.hp / character.stats.max_hp) < 0.20:
                final_stats["atk"] = int(final_stats["atk"] * 1.10)
                final_stats["defense"] = int(final_stats["defense"] * 1.10)
                final_stats["res_def"] = int(final_stats["res_def"] * 1.10)

        # 6. Apply Caps
        def_cap = 50
        res_def_cap = 50
        if character.name == "Hoshiguma the breacher":
            def_cap = 90
            res_def_cap = 90
        elif character.name == "VinaVictoria":
            def_cap = 70
            res_def_cap = 60
        else:
            caps = DEF_CAPS.get(character.char_class, {"defense": 50, "res_def": 50})
            def_cap = caps.get("defense", 50)
            res_def_cap = caps.get("res_def", 50)
            
        final_stats["defense"] = min(final_stats["defense"], def_cap)
        final_stats["res_def"] = min(final_stats["res_def"], res_def_cap)

        # Apply Hoshiguma Skill 1 modification if activated: DEF -> 0, increase max_hp
        if character.special_skills.skill_1 == "Võ sĩ đạo" and character.special_skills.skill_1_activated:
            hp_increase = int(final_stats["defense"] * final_stats["max_hp"] / 100)
            final_stats["max_hp"] += hp_increase
            final_stats["defense"] = 0

        # 7. Apply Buffs / Debuffs (e.g. Cứng cáp, Yếu đuối, Chậm chạp)
        for buff in character.buffs:
            if buff.name == "Cứng cáp":
                final_stats["defense"] = min(int(final_stats["defense"] * 1.20), def_cap)
                final_stats["res_def"] = min(int(final_stats["res_def"] * 1.20), res_def_cap)
            elif buff.name == "Gia tăng sĩ khí":
                final_stats["atk"] = int(final_stats["atk"] * 1.05)
                final_stats["defense"] = min(int(final_stats["defense"] * 1.05), def_cap)
                final_stats["atk_spd"] = int(final_stats["atk_spd"] * 1.05)

        for debuff in character.debuffs:
            if debuff.name == "Chậm chạp":
                final_stats["atk_spd"] = int(final_stats["atk_spd"] * 0.50)
            elif debuff.name == "Yếu đuối":
                final_stats["atk"] = int(final_stats["atk"] * 0.90)
                final_stats["defense"] = int(final_stats["defense"] * 0.90)
                final_stats["res_def"] = int(final_stats["res_def"] * 0.90)
        
        # Xử lý Giá lạnh
        frost_stacks = sum(1 for d in character.debuffs if d.name == "Giá lạnh")
        if frost_stacks > 0:
            penalty = 0.30 * min(frost_stacks, 2)
            final_stats["atk_spd"] = int(final_stats["atk_spd"] * (1 - penalty))

        # Set character's stats while keeping current HP bounded by new max_hp
        new_max_hp = final_stats["max_hp"]
        current_hp = min(character.stats.hp, new_max_hp) if character.stats.hp > 0 else 0
        
        return RPGCharacterStats(
            max_hp=new_max_hp,
            hp=current_hp,
            atk=final_stats["atk"],
            res=final_stats["res"],
            defense=final_stats["defense"],
            res_def=final_stats["res_def"],
            atk_spd=final_stats["atk_spd"]
        )

    @classmethod
    def sync_character_stats(cls, character: RPGCharacter, active_party_size: int = 1) -> None:
        """Recalculates and updates the character stats block."""
        character.stats = cls.calculate_current_stats(character, active_party_size)

    @classmethod
    def generate_random_character(cls, player_level: int, rarity_probs: dict[str, float] = None) -> RPGCharacter:
        """Generates a random character scaling to player level."""
        if rarity_probs is None:
            rarity_probs = STRANGER_RARITY_PROBS
            
        rarity = cls.roll_by_probability(rarity_probs)
        
        # Determine Race
        races = RARITY_RACE_MAP.get(rarity, ["Human"])
        race = random.choice(races)
        
        # Determine Class
        classes = RACE_CLASSES.get(race, ["Guard"])
        char_class = random.choice(classes)
        
        # Determine Level (player_level +/- 2, min 1, max based on rarity)
        max_lvl = RARITY_MAX_LEVEL.get(rarity, 50)
        level = random.randint(max(1, player_level - 2), min(max_lvl, player_level + 2))
        
        # Mythic presets override random naming/gender
        name = ""
        gender = random.choice(["Male", "Female"])
        if rarity == "Mythic" and char_class in MYTHIC_CHARACTERS:
            presets = MYTHIC_CHARACTERS[char_class]
            preset = random.choice(presets)
            name = preset["name"]
            gender = preset["gender"]
        else:
            # We leave name blank so AI can generate one, or generate a simple placeholder
            name = f"{race} {char_class} Vô danh"
            
        # Initialize Character base
        character = RPGCharacter(
            character_id=str(uuid.uuid4())[:8],
            name=name,
            race=race,
            char_class=char_class,
            rarity=rarity,
            gender=gender,
            level=level,
            max_level=max_lvl
        )
        cls.init_character_skills(character)
        
        # Calculate stats at level
        cls_stats = BASE_STATS.get(char_class, BASE_STATS["Specialist"])
        character.stats.hp = cls_stats["max_hp"] # Set raw hp value so calc_current_stats caps it correctly
        cls.sync_character_stats(character)
        character.stats.hp = character.stats.max_hp
        
        return character

    @classmethod
    def init_character_skills(cls, character: RPGCharacter) -> None:
        """Initializes special skills for a character based on race, class, and name."""
        race = character.race
        char_class = character.char_class
        name = character.name
        
        special_skills = RPGSpecialSkills()
        if race == "Valkyrie":
            if char_class == "Defender":
                special_skills.passive_skill = "Ma thần bất diệt"
                special_skills.skill_1 = "Võ sĩ đạo"
                special_skills.skill_2 = "Hoả liên trảm quỷ"
            elif char_class == "Guard":
                if name == "SilverAsh the Reignfrost":
                    special_skills.passive_skill = "Kỷ băng hà"
                    special_skills.skill_1 = "Quét kiếm"
                    special_skills.skill_2 = "Băng tuyết vũ"
                else:
                    special_skills.passive_skill = "Hoàng đế"
                    special_skills.skill_1 = "Sư tử hống"
                    special_skills.skill_2 = "Phán quyết cuối cùng"
            elif char_class == "Caster":
                special_skills.passive_skill = "Khai triển"
                special_skills.skill_1 = "Vây hãm"
                special_skills.skill_2 = "Chiếu tướng"
            elif char_class == "Sniper":
                special_skills.passive_skill = "Truy nã"
                special_skills.skill_1 = "Khóa mục tiêu"
                special_skills.skill_2 = "Khai hoả toàn diện"
        elif race == "Angel":
            special_skills.passive_skill = "Hộ vệ thiên sứ"
            special_skills.skill_1 = "Lá chắn"
            special_skills.skill_2 = "Thiên lôi"
        elif race == "Devil":
            special_skills.passive_skill = "Ngạ Quỷ"
            special_skills.skill_1 = "Hấp thụ"
            special_skills.skill_2 = "Huyết quỷ thuật"
        elif race == "Elf":
            special_skills.passive_skill = "Uyển chuyển"
            special_skills.skill_1 = "Mưa tên"
        elif race == "Royalty":
            special_skills.passive_skill = "Chiến tích hoàng gia"
            special_skills.skill_1 = "Phong tước"
        elif race == "Orc":
            special_skills.passive_skill = "Cuồng nộ"
            
        character.special_skills = special_skills

    @classmethod
    def generate_player_character(cls, name: str, gender: str) -> RPGCharacter:
        """Generates the main player character (always Human Specialist, Common starting level 1)."""
        character = RPGCharacter(
            character_id="player",
            name=name,
            race="Human",
            char_class="Specialist",
            rarity="Common",
            gender=gender,
            level=1,
            max_level=99,
            is_player_character=True
        )
        cls_stats = BASE_STATS["Specialist"]
        character.stats.hp = cls_stats["max_hp"]
        cls.sync_character_stats(character)
        character.stats.hp = character.stats.max_hp
        return character

    @classmethod
    def generate_random_item(cls, rarity: str = None, item_type: str = None, rarity_probs: dict[str, float] = None) -> RPGItem:
        """Generates a random item based on catalog and probabilities."""
        if rarity is None:
            probs = rarity_probs if rarity_probs is not None else ITEM_FIND_RARITY_PROBS
            rarity = cls.roll_by_probability(probs)
        if item_type is None:
            item_type = random.choice(["Weapon", "Armor", "Consume"])
            
        rarity_data = ITEM_CATALOG.get(rarity, ITEM_CATALOG["Common"])
        item_data = rarity_data.get(item_type, rarity_data["Consume"])
        
        name = item_data["name"]
        description = item_data.get("description", "")
        if rarity == "Epic" and item_type == "Consume":
            if random.random() < 0.5:
                env_list = ["Đồng bằng", "Đồi núi", "Rừng rậm", "Núi lửa", "Hoang mạc", "Núi tuyết", "Thiên giới"]
                selected_env = random.choice(env_list)
                name = f"Bản đồ cổ {selected_env}"
                description = f"Bản đồ cổ của vùng {selected_env}. Khi mua sẽ tự động mở khóa điểm dịch chuyển đến Kiến trúc lớn của vùng này."

        buy_price = BUY_PRICES.get(rarity, 30)
        if name.startswith("Bản đồ cổ"):
            buy_price = 199

        return RPGItem(
            item_id=str(uuid.uuid4())[:8],
            name=name,
            rarity=rarity,
            item_type=item_type,
            stats_bonus=item_data.get("stats_bonus", {}),
            description=description,
            sell_price=SELL_PRICES.get(rarity, 10),
            buy_price=buy_price
        )

    @classmethod
    def add_exp(cls, character: RPGCharacter, exp_gained: int, active_party_size: int = 1) -> list[str]:
        """Adds experience to a character and handles levels. Returns leveling log."""
        logs = []
        if character.level >= character.max_level:
            return logs
            
        character.exp += exp_gained
        while character.level < character.max_level and character.exp >= character.level:
            character.exp -= character.level
            character.level += 1
            logs.append(f"{character.name} đã thăng cấp lên Cấp {character.level}!")
            # Recalculate stats immediately to update max_hp
            cls.sync_character_stats(character, active_party_size)
            # Heal fully to the new max_hp
            # character.stats.hp = character.stats.max_hp
            
        cls.sync_character_stats(character, active_party_size)
        return logs

# ==================== COMBAT ENGINE ====================

class CombatEngine:

    @classmethod
    def init_combat(cls, party: RPGParty, enemy: RPGCharacter) -> RPGCombatState:
        """Initializes a new combat state copying party members."""
        combat_party = []
        alive_count = sum(1 for c in party.active if c.stats.hp > 0)
        for char in party.active:
            # Sync character stats and reset dynamic flags
            RPGEngine.sync_character_stats(char, alive_count)
            # Create deep copies of stats and skills for combat
            char_copy = char.model_copy(deep=True)
            char_copy.special_skills.passive_activated = False
            char_copy.special_skills.skill_1_activated = False
            char_copy.special_skills.skill_1_activating = False
            char_copy.special_skills.skill_1_countdown = 0
            char_copy.special_skills.skill_2_countdown = 0
            char_copy.special_skills.quan_co_count = 0
            char_copy.special_skills.bullet_count = 0
            char_copy.special_skills.hoshi_passive_countdown = 0
            char_copy.special_skills.lemuen_auto_shots = 0
            combat_party.append(char_copy)
            
        # Reset enemy dynamic flags
        enemy_copy = enemy.model_copy(deep=True)
        enemy_copy.special_skills.passive_activated = False
        enemy_copy.special_skills.skill_1_activated = False
        enemy_copy.special_skills.skill_1_activating = False
        enemy_copy.special_skills.skill_1_countdown = 0
        enemy_copy.special_skills.skill_2_countdown = 0
        enemy_copy.special_skills.quan_co_count = 0
        enemy_copy.special_skills.bullet_count = 0
        enemy_copy.special_skills.hoshi_passive_countdown = 0
        enemy_copy.special_skills.lemuen_auto_shots = 0
        
        # Sort by speed to init speed list logs
        speed_list = sorted(combat_party + [enemy_copy], key=lambda c: c.stats.atk_spd, reverse=True)
        names = ", ".join([f"{c.name} ({c.stats.atk_spd} SPD)" for c in speed_list])
        
        combat_log = [
            f"⚔️ Trận chiến bắt đầu! Đối thủ: {enemy_copy.name} (Rarity: {enemy_copy.rarity}, Class: {enemy_copy.char_class})",
            f"Tốc độ ra đòn: {names}"
        ]
        
        # Lemuen Sniper starting bullet setup
        for char in combat_party:
            if char.special_skills.passive_skill == "Truy nã":
                char.special_skills.bullet_count = 1
                combat_log.append(f"🎯 Lemuen nạp sẵn 1 viên đạn (Truy nã).")

        return RPGCombatState(
            cb_turn_count=1,
            combat_party=combat_party,
            enemy=enemy_copy,
            combat_log=combat_log,
            is_active=True
        )

    @classmethod
    def apply_buff_debuff_ticks(cls, combat_state: RPGCombatState, acted_or_hit_ids: set[str] = None) -> list[str]:
        """Processes bleed/burn tick damage and decrements durations. Returns logs."""
        logs = []
        # Ticks for active party members
        for char in combat_state.combat_party:
            if char.stats.hp <= 0:
                # If Hoshiguma is dead and has revival countdown ticking
                if char.special_skills.hoshi_passive_countdown > 0:
                    char.special_skills.hoshi_passive_countdown -= 1
                    if char.special_skills.hoshi_passive_countdown == 0:
                        char.stats.hp = int(char.stats.max_hp * 0.20)
                        logs.append(f"🛡️ Hoshiguma đã kích hoạt 'Ma thần bất diệt' và hồi sinh với 20% HP ({char.stats.hp}/{char.stats.max_hp})!")
                continue
                
            # Bleed tick (Chảy máu): -10% current HP
            has_bleed = any(d.name == "Chảy máu" for d in char.debuffs)
            if has_bleed:
                dmg = max(1, int(char.stats.hp * 0.10))
                char.stats.hp = max(0, char.stats.hp - dmg)
                logs.append(f"🩸 {char.name} mất {dmg} HP từ Chảy máu (HP còn lại: {char.stats.hp}/{char.stats.max_hp}).")
                cls.check_and_trigger_death(char, combat_state, logs)

            if char.stats.hp <= 0:
                continue

            # Burn tick (Thiêu đốt): -15% current HP
            has_burn = any(d.name == "Thiêu đốt" for d in char.debuffs)
            if has_burn:
                dmg = max(1, int(char.stats.hp * 0.15))
                char.stats.hp = max(0, char.stats.hp - dmg)
                logs.append(f"🔥 {char.name} mất {dmg} HP từ Thiêu đốt (HP còn lại: {char.stats.hp}/{char.stats.max_hp}).")
                cls.check_and_trigger_death(char, combat_state, logs)

            if char.stats.hp <= 0:
                continue

            # Heal tick (Chữa lành/Siêu cấp hồi phục)
            has_heal = any(b.name == "Chữa lành" for b in char.buffs)
            has_super_heal = any(b.name == "Siêu cấp hồi phục" for b in char.buffs)
            
            missing_hp = char.stats.max_hp - char.stats.hp
            heal_amt = 0
            if has_super_heal:
                heal_amt = int(missing_hp * 0.15)
            elif has_heal:
                heal_amt = int(missing_hp * 0.05)
                
            if heal_amt > 0:
                char.stats.hp = min(char.stats.max_hp, char.stats.hp + heal_amt)
                logs.append(f"💚 {char.name} hồi phục {heal_amt} HP từ hiệu ứng chữa lành (HP: {char.stats.hp}/{char.stats.max_hp}).")

            # Devil Passive: Ngạ Quỷ (heal 5% missing HP if did not attack or take damage)
            if char.special_skills.passive_skill == "Ngạ Quỷ" and acted_or_hit_ids is not None:
                if char.character_id not in acted_or_hit_ids and char.stats.hp < char.stats.max_hp:
                    missing_hp = char.stats.max_hp - char.stats.hp
                    heal = max(1, int(missing_hp * 0.05))
                    char.stats.hp = min(char.stats.max_hp, char.stats.hp + heal)
                    logs.append(f"😈 Devil {char.name} kích hoạt nội tại 'Ngạ Quỷ', hồi phục {heal} HP do không hành động hoặc chịu đòn (HP: {char.stats.hp}/{char.stats.max_hp}).")

            # Lemuen auto-firing has been moved to the start of process_turn
            pass

            # Decrement Buffs/Debuffs duration
            for buff in list(char.buffs):
                if buff.duration is not None:
                    buff.duration -= 1
                    if buff.duration <= 0:
                        char.buffs.remove(buff)
                        logs.append(f"Hiệu ứng có lợi '{buff.name}' trên {char.name} đã kết thúc.")
            for debuff in list(char.debuffs):
                if debuff.duration is not None:
                    debuff.duration -= 1
                    if debuff.duration <= 0:
                        char.debuffs.remove(debuff)
                        logs.append(f"Hiệu ứng bất lợi '{debuff.name}' trên {char.name} đã biến mất.")
                        
            # Decrement skill cooldowns
            if char.special_skills.skill_1_countdown > 0:
                char.special_skills.skill_1_countdown -= 1
            if char.special_skills.skill_2_countdown > 0:
                char.special_skills.skill_2_countdown -= 1

        # Ticks for Enemy
        enemy = combat_state.enemy
        if enemy and enemy.stats.hp > 0:
            if any(d.name == "Chảy máu" for d in enemy.debuffs):
                dmg = max(1, int(enemy.stats.hp * 0.10))
                enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                logs.append(f"🩸 {enemy.name} mất {dmg} HP từ Chảy máu (HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                
            if enemy.stats.hp > 0 and any(d.name == "Thiêu đốt" for d in enemy.debuffs):
                dmg = max(1, int(enemy.stats.hp * 0.15))
                enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                logs.append(f"🔥 {enemy.name} mất {dmg} HP từ Thiêu đốt (HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Ngạ Quỷ passive for enemy Devil
            if enemy.special_skills.passive_skill == "Ngạ Quỷ" and acted_or_hit_ids is not None:
                if enemy.character_id not in acted_or_hit_ids and enemy.stats.hp < enemy.stats.max_hp:
                    missing_hp = enemy.stats.max_hp - enemy.stats.hp
                    heal = max(1, int(missing_hp * 0.05))
                    enemy.stats.hp = min(enemy.stats.max_hp, enemy.stats.hp + heal)
                    logs.append(f"😈 Kẻ địch {enemy.name} kích hoạt nội tại 'Ngạ Quỷ', hồi phục {heal} HP (HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                
            # Decrement Enemy buffs/debuffs
            for buff in list(enemy.buffs):
                if buff.duration is not None:
                    buff.duration -= 1
                    if buff.duration <= 0:
                        enemy.buffs.remove(buff)
                        logs.append(f"Hiệu ứng có lợi '{buff.name}' trên {enemy.name} đã kết thúc.")
            for debuff in list(enemy.debuffs):
                if debuff.duration is not None:
                    debuff.duration -= 1
                    if debuff.duration <= 0:
                        enemy.debuffs.remove(debuff)
                        logs.append(f"Hiệu ứng bất lợi '{debuff.name}' trên {enemy.name} đã biến mất.")
                        
            # Decrement enemy cooldowns
            if enemy.special_skills.skill_1_countdown > 0:
                enemy.special_skills.skill_1_countdown -= 1
            if enemy.special_skills.skill_2_countdown > 0:
                enemy.special_skills.skill_2_countdown -= 1

        # Recalculate stats for everyone
        alive_allies_count = sum(1 for c in combat_state.combat_party if c.stats.hp > 0)
        for char in combat_state.combat_party:
            RPGEngine.sync_character_stats(char, alive_allies_count)
        if enemy:
            RPGEngine.sync_character_stats(enemy, 1)

        return logs

    @classmethod
    def check_and_trigger_death(cls, character: RPGCharacter, combat_state: RPGCombatState, logs: list[str]) -> bool:
        """Checks if a character has died and handles revival passives (Angel and Hoshiguma) or death logs."""
        if character.stats.hp > 0:
            return False
            
        # Check Bất tử (immortality) buff
        if any(b.name == "Bất tử" for b in character.buffs):
            character.stats.hp = 1
            logs.append(f"🛡️ {character.name} kích hoạt trạng thái Bất tử và giữ lại 1 HP!")
            return False
            
        logs.append(f"💀 {character.name} đã bị hạ gục!")
        
        # 1. Angel Passive: Hộ vệ thiên sứ (revives a companion once per combat with 5% HP)
        is_ally = any(c.character_id == character.character_id for c in combat_state.combat_party)
        if is_ally and character.special_skills.passive_skill != "Ma thần bất diệt":
            for angel in combat_state.combat_party:
                if angel.stats.hp > 0 and angel.special_skills.passive_skill == "Hộ vệ thiên sứ":
                    if not angel.special_skills.passive_activated and character.character_id != angel.character_id:
                        angel.special_skills.passive_activated = True
                        character.stats.hp = max(1, int(character.stats.max_hp * 0.05))
                        logs.append(f"👼 Angel đã kích hoạt 'Hộ vệ thiên sứ'! Hồi sinh {character.name} với 5% HP ({character.stats.hp}/{character.stats.max_hp}).")
                        return False

        # 2. Hoshiguma Passive: Ma thần bất diệt (revives self after 8 turns)
        if character.special_skills.passive_skill == "Ma thần bất diệt":
            if not character.special_skills.passive_activated:
                character.special_skills.passive_activated = True
                character.special_skills.hoshi_passive_countdown = 8
                logs.append(f"🛡️ Hoshiguma gục xuống nhưng 'Ma thần bất diệt' được kích hoạt. Cô ấy sẽ hồi sinh sau 8 lượt.")
                return False

        # Royalty Passive: Chiến tích hoàng gia (CD reduction for allies on death)
        if character.special_skills.passive_skill == "Chiến tích hoàng gia":
            logs.append(f"👑 Royalty gục xuống! Kích hoạt 'Chiến tích hoàng gia', giảm 2 lượt hồi chiêu cho toàn đội.")
            for char in combat_state.combat_party:
                if char.character_id != character.character_id:
                    char.special_skills.skill_1_countdown = max(0, char.special_skills.skill_1_countdown - 2)
                    char.special_skills.skill_2_countdown = max(0, char.special_skills.skill_2_countdown - 2)

        return True

    @classmethod
    def process_turn(cls, combat_state: RPGCombatState, request: Any) -> tuple[list[str], bool, str | None]:
        """
        Processes a full combat turn containing the player character action and the enemy's turn.
        Returns: (combat_log, is_combat_over, result_string).
        """
        logs = [f"⚔️ ─── LƯỢT ĐẤU THỨ {combat_state.cb_turn_count} ─── ⚔️"]
        attacker_id = request.attacker_id
        skill_name = request.skill_name
        target_id = request.target_id
        defender_id = request.defender_id

        # Track acted or hit character IDs to implement Devil's Ngạ Quỷ passive and Lemuen's Truy nã
        acted_or_hit_ids = set()

        # Kiểm tra nội tại Kỷ băng hà của SilverAsh (phía đồng minh)
        silverash_allies = [c for c in combat_state.combat_party if c.name == "SilverAsh the Reignfrost" and c.stats.hp > 0]
        if silverash_allies:
            enemy = combat_state.enemy
            if enemy and enemy.stats.hp > 0:
                frost_count = sum(1 for d in enemy.debuffs if d.name == "Giá lạnh")
                if frost_count >= 2:
                    enemy.debuffs = [d for d in enemy.debuffs if d.name != "Giá lạnh"]
                    enemy.debuffs.append(RPGDebuff(name="Đông cứng", duration=1))
                    logs.append(f"❄️ Nội tại 'Kỷ băng hà' của SilverAsh kích hoạt! Chuyển {frost_count} tầng Giá lạnh trên {enemy.name} thành Đông cứng (1 lượt)!")
                    RPGEngine.sync_character_stats(enemy, 1)

        # Kiểm tra nội tại Kỷ băng hà của SilverAsh (phía kẻ địch)
        if combat_state.enemy and combat_state.enemy.name == "SilverAsh the Reignfrost" and combat_state.enemy.stats.hp > 0:
            for char in combat_state.combat_party:
                if char.stats.hp > 0:
                    frost_count = sum(1 for d in char.debuffs if d.name == "Giá lạnh")
                    if frost_count >= 2:
                        char.debuffs = [d for d in char.debuffs if d.name != "Giá lạnh"]
                        char.debuffs.append(RPGDebuff(name="Đông cứng", duration=1))
                        logs.append(f"❄️ Kẻ địch {combat_state.enemy.name} kích hoạt nội tại 'Kỷ băng hà'! Chuyển {frost_count} tầng Giá lạnh trên {char.name} thành Đông cứng (1 lượt)!")
                        RPGEngine.sync_character_stats(char, len(combat_state.combat_party))

        # Lemuen Auto-firing at the start of the turn
        for char in combat_state.combat_party:
            if char.special_skills.passive_skill == "Truy nã" and char.stats.hp > 0 and char.special_skills.skill_1_activating:
                if char.special_skills.bullet_count > 0:
                    enemy = combat_state.enemy
                    if enemy and enemy.stats.hp > 0:
                        dmg = max(1, int(random.uniform(0.60, 1.00) * char.stats.atk * (1 - enemy.stats.defense / 100)))
                        enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                        char.special_skills.bullet_count -= 1
                        logs.append(f"🎯 Lemuen tự động bắn 1 viên đạn từ Khóa mục tiêu gây {dmg} sát thương vật lý lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}, Số đạn còn lại: {char.special_skills.bullet_count}).")
                        cls.check_and_trigger_death(enemy, combat_state, logs)
                        
                        if char.special_skills.bullet_count <= 0:
                            char.special_skills.skill_1_activating = False
                            logs.append(f"🎯 Lemuen đã bắn hết đạn Khóa mục tiêu, kết thúc trạng thái khóa.")
                else:
                    char.special_skills.skill_1_activating = False

        # Check combat outcome after auto shots
        is_over, res = cls.check_combat_outcome(combat_state)
        if is_over:
            return logs, is_over, res

        # 1. Fetch character acting
        attacker = next((c for c in combat_state.combat_party if c.character_id == attacker_id), None)
        if not attacker:
            return [f"Lỗi: Không tìm thấy nhân vật {attacker_id} trong đội hình."], True, "lose"
            
        if attacker.stats.hp <= 0:
            return [f"Lỗi: Nhân vật {attacker.name} đã tử trận và không thể hành động."], False, None

        if attacker.special_skills.skill_1_activating:
            return [f"Lỗi: Nhân vật {attacker.name} đang trong chế độ tự động bắn (Khóa mục tiêu), không thể chọn hành động thủ công."], False, None

        # Apply Elf Passive (né tránh) and stuns
        is_stunned = any(d.name in ["Choáng", "Sợ hãi", "Đông cứng"] for d in attacker.debuffs)
        if is_stunned:
            logs.append(f"💤 {attacker.name} bị khống chế (Choáng/Sợ hãi/Đông cứng), bỏ qua lượt này!")
            # Enemy turn proceeds
            cls.enemy_turn(combat_state, defender_id, logs, acted_or_hit_ids)
            round_logs = cls.apply_buff_debuff_ticks(combat_state, acted_or_hit_ids)
            logs.extend(round_logs)
            combat_state.cb_turn_count += 1
            is_over, res = cls.check_combat_outcome(combat_state)
            return logs, is_over, res

        # Check speed comparison for order of action
        enemy = combat_state.enemy
        player_first = attacker.stats.atk_spd >= enemy.stats.atk_spd
        if skill_name == "skill_2" and attacker.special_skills.skill_2 == "Băng tuyết vũ":
            player_first = True
            logs.append(f"⚡ {attacker.name} sử dụng 'Băng tuyết vũ', chớp nhoáng cướp quyền ra đòn trước!")
        
        if player_first:
            # Player attacks first
            cls.execute_action(attacker, skill_name, target_id, combat_state, logs, acted_or_hit_ids)
            
            # Check if enemy is defeated
            if enemy.stats.hp <= 0:
                logs.append(f"🎉 Chiến thắng! Đã tiêu diệt {enemy.name}!")
                combat_state.is_active = False
                return logs, True, "win"
                
            # Enemy attacks back
            cls.enemy_turn(combat_state, defender_id, logs, acted_or_hit_ids)
        else:
            # Enemy attacks first
            cls.enemy_turn(combat_state, defender_id, logs, acted_or_hit_ids)
            
            # Check if party is defeated
            alive_allies = [c for c in combat_state.combat_party if c.stats.hp > 0]
            if not alive_allies:
                logs.append(f"💀 Thất bại! Toàn đội hình đã tử trận.")
                combat_state.is_active = False
                return logs, True, "lose"
                
            # Player attacks back (if still alive and not stunned by enemy attack)
            if attacker.stats.hp > 0 and not any(d.name in ["Choáng", "Sợ hãi"] for d in attacker.debuffs):
                cls.execute_action(attacker, skill_name, target_id, combat_state, logs, acted_or_hit_ids)
                if enemy.stats.hp <= 0:
                    logs.append(f"🎉 Chiến thắng! Đã tiêu diệt {enemy.name}!")
                    combat_state.is_active = False
                    return logs, True, "win"
            else:
                logs.append(f"💤 {attacker.name} không thể tấn công vì bị choáng hoặc tử trận.")

        # Post-combat round checks (Bleed/Burn ticks, buff decay, auto-fire)
        round_logs = cls.apply_buff_debuff_ticks(combat_state, acted_or_hit_ids)
        logs.extend(round_logs)
        
        # Cooldown countdown / bullet update for Sniper idle (passive Truy nã)
        for char in combat_state.combat_party:
            if char.special_skills.passive_skill == "Truy nã" and char.stats.hp > 0:
                # Gained only if she is NOT currently auto-firing, and did not attack or take damage
                if not char.special_skills.skill_1_activating and char.character_id not in acted_or_hit_ids:
                    if char.special_skills.bullet_count < 5:
                        char.special_skills.bullet_count += 1
                        logs.append(f"🎯 Lemuen tích lũy thêm 1 viên đạn (Truy nã) ({char.special_skills.bullet_count}/5).")

        combat_state.cb_turn_count += 1
        is_over, res = cls.check_combat_outcome(combat_state)
        return logs, is_over, res

    @classmethod
    def execute_action(cls, attacker: RPGCharacter, skill_name: str, target_id: str, combat_state: RPGCombatState, logs: list[str], acted_or_hit_ids: set[str] = None) -> None:
        """Executes the specific attack or skill chosen by the player character with boss dodge/block checks."""
        import re
        enemy = combat_state.enemy
        
        # Check enemy block/evasion for Golem, Ma vương Xương Cốt, and Alpha
        dodge_type = None
        if enemy and target_id == enemy.character_id:
            if enemy.name == "Golem" and random.random() < 0.20:
                dodge_type = "golem"
            elif enemy.name == "Ma vương Xương Cốt" and random.random() < 0.10:
                dodge_type = "skeleton"
            elif enemy.name == "Alpha" and enemy.stats.hp / enemy.stats.max_hp < 0.20 and random.random() < 0.20:
                dodge_type = "alpha"

        if dodge_type:
            # We want to run the action to spend energy/skills, but prevent damage
            old_enemy_hp = enemy.stats.hp
            temp_logs = []
            
            # Run the raw action logic
            cls._execute_action_raw(attacker, skill_name, target_id, combat_state, temp_logs, acted_or_hit_ids)
            
            # Restore enemy HP
            enemy.stats.hp = old_enemy_hp
            
            # Print dodge message
            if dodge_type == "golem":
                logs.append(f"🛡️ Golem kích hoạt kỹ năng đặc biệt: Chặn đứng hoàn toàn đòn đánh/chiêu thức từ {attacker.name}!")
            elif dodge_type == "skeleton":
                logs.append(f"💀 Ma vương Xương Cốt kích hoạt kỹ năng đặc biệt: Hóa hư vô, miễn nhiễm đòn đánh/chiêu thức từ {attacker.name}!")
            elif dodge_type == "alpha":
                logs.append(f"🌌 Alpha kích hoạt kỹ năng đặc biệt: Dịch chuyển hư không, né tránh hoàn toàn đòn đánh/chiêu thức từ {attacker.name}!")
                
            # Copy temp_logs to logs, modifying damage messages
            for log in temp_logs:
                # Replace "gây X sát thương" with "gây 0 sát thương (bị né/chặn)"
                log = re.sub(r"gây \d+ sát thương", "gây 0 sát thương (bị né/chặn)", log)
                # Replace "hút X HP" with "hút 0 HP"
                log = re.sub(r"hút \d+ HP", "hút 0 HP", log)
                # Replace HP display "Enemy HP: X/Y"
                log = re.sub(r"Enemy HP: \d+/\d+", f"Enemy HP: {old_enemy_hp}/{enemy.stats.max_hp}", log)
                logs.append(log)
        else:
            cls._execute_action_raw(attacker, skill_name, target_id, combat_state, logs, acted_or_hit_ids)

    @classmethod
    def _execute_action_raw(cls, attacker: RPGCharacter, skill_name: str, target_id: str, combat_state: RPGCombatState, logs: list[str], acted_or_hit_ids: set[str] = None) -> None:
        """The original raw logic of execute_action (without dodge checking)."""
        enemy = combat_state.enemy
        if acted_or_hit_ids is not None:
            acted_or_hit_ids.add(attacker.character_id)
        old_enemy_hp = enemy.stats.hp if enemy else 0
        
        # 1. Basic Attack
        if skill_name == "basic_attack":
            if attacker.char_class == "Supporter":
                # Basic attack is a heal
                target = next((c for c in combat_state.combat_party if c.character_id == target_id), None)
                if not target or target.stats.hp <= 0:
                    logs.append(f"🚑 Trị thương thất bại: mục tiêu không hợp lệ hoặc đã tử trận.")
                    return
                # Heal amount = target_hp * (res / 100) -> Wait, let's use target_max_hp * (res / 100) or res %
                # Let's say: heals max(5, int(target.stats.max_hp * (attacker.stats.res / 100)))
                heal = max(5, int(target.stats.max_hp * (attacker.stats.res / 100)))
                target.stats.hp = min(target.stats.max_hp, target.stats.hp + heal)
                logs.append(f"🚑 {attacker.name} hồi phục {heal} HP cho {target.name} (HP: {target.stats.hp}/{target.stats.max_hp}).")
            else:
                # Normal attack
                # Check misses for Tê liệt (50% miss)
                if any(d.name == "Tê liệt" for d in attacker.debuffs) and random.random() < 0.50:
                    logs.append(f"💨 {attacker.name} bị tê liệt và đánh hụt đòn tấn công!")
                    return
                
                # Check evasion for Elf enemy
                if enemy.special_skills.passive_skill == "Uyển chuyển" and random.random() < 0.20:
                    logs.append(f"💨 {enemy.name} (Elf) nhanh nhẹn né tránh đòn tấn công cơ bản!")
                    return

                is_frozen = any(d.name == "Đông cứng" for d in enemy.debuffs)
                phys_dmg = int(attacker.stats.atk * (1 - enemy.stats.defense / 100))
                mag_dmg = int(attacker.stats.res * (1 - enemy.stats.res_def / 100))
                
                if is_frozen:
                    if attacker.name == "SilverAsh the Reignfrost":
                        phys_dmg = int(phys_dmg * 1.8)
                        logs.append(f"❄️ PHÁ BĂNG! SilverAsh gây x1.8 sát thương vật lý lên {enemy.name} đang bị đông cứng!")
                    else:
                        phys_dmg = int(phys_dmg * 1.5)
                        logs.append(f"❄️ PHÁ BĂNG! {attacker.name} gây x1.5 sát thương vật lý lên {enemy.name} đang bị đông cứng!")
                
                dmg = max(1, phys_dmg, mag_dmg)
                
                # Check shield buff on enemy
                has_shield = any(b.name == "Lá chắn" for b in enemy.buffs)
                if has_shield:
                    dmg = 0
                    # Remove shield
                    enemy.buffs = [b for b in enemy.buffs if b.name != "Lá chắn"]
                    logs.append(f"🛡️ {enemy.name} sử dụng Lá chắn hấp thụ hoàn toàn đòn tấn công cơ bản từ {attacker.name}!")
                else:
                    enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                    logs.append(f"⚔️ {attacker.name} tấn công thường gây {dmg} sát thương lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

        # 2. Skill 1
        elif skill_name == "skill_1":
            if attacker.special_skills.skill_1_countdown > 0:
                logs.append(f"⚠️ Chiêu thức 1 đang hồi ({attacker.special_skills.skill_1_countdown} lượt nữa)!")
                return
                
            # Defender Skill 1: Võ sĩ đạo
            if attacker.special_skills.skill_1 == "Võ sĩ đạo":
                attacker.special_skills.skill_1_activated = True
                attacker.special_skills.skill_1_countdown = 999  # 1 lần duy nhất
                
                alive_allies_count = sum(1 for c in combat_state.combat_party if c.stats.hp > 0)
                old_def = attacker.stats.defense
                old_max_hp = attacker.stats.max_hp
                hp_increase = int(old_def * old_max_hp / 100)
                
                RPGEngine.sync_character_stats(attacker, alive_allies_count)
                attacker.stats.hp = min(attacker.stats.max_hp, attacker.stats.hp + hp_increase)
                
                logs.append(f"🛡️ Hoshiguma kích hoạt 'Võ sĩ đạo' (1 lần duy nhất)! DEF giảm về 0, tăng Max_HP thêm {hp_increase} (HP hiện tại: {attacker.stats.hp}/{attacker.stats.max_hp}, DEF: 0).")
                
            # Guard Skill 1: Sư tử hống (50% sợ hãi + buff team)
            elif attacker.special_skills.skill_1 == "Sư tử hống":
                attacker.special_skills.skill_1_countdown = 8
                logs.append(f"🦁 {attacker.name} sử dụng 'Sư tử hống' gầm rú chấn động chiến trường!")
                
                # Buff team: Gia tăng sĩ khí (+5% stats, duration 2, excluding self)
                buffed_allies = []
                for char in combat_state.combat_party:
                    if char.stats.hp > 0 and char.character_id != attacker.character_id:
                        if not any(b.name == "Gia tăng sĩ khí" for b in char.buffs):
                            char.buffs.append(RPGBuff(name="Gia tăng sĩ khí", duration=2))
                            buffed_allies.append(char.name)
                if buffed_allies:
                    logs.append(f"✨ Đồng minh {', '.join(buffed_allies)} nhận buff 'Gia tăng sĩ khí' (+5% ATK/DEF/SPD) trong 2 lượt.")
                
                # Debuff enemy: 50% Fear (Sợ hãi, 3 turns)
                if random.random() < 0.50:
                    if any(b.name == "Lá chắn phép" for b in enemy.buffs):
                        logs.append(f"✨ {enemy.name} kháng hiệu ứng Sợ hãi nhờ Lá chắn phép.")
                    else:
                        enemy.debuffs.append(RPGDebuff(name="Sợ hãi", duration=3))
                        logs.append(f"😨 {enemy.name} hoảng sợ nhận hiệu ứng 'Sợ hãi' trong 3 lượt!")
                else:
                    logs.append(f"💨 {enemy.name} giữ vững ý chí, chống chịu được tiếng gầm.")

            # Guard Skill 1: Quét kiếm (SilverAsh)
            elif attacker.special_skills.skill_1 == "Quét kiếm":
                attacker.special_skills.skill_1_countdown = 3
                phys_dmg = int(0.80 * attacker.stats.atk * (1 - enemy.stats.defense / 100))
                is_frozen = any(d.name == "Đông cứng" for d in enemy.debuffs)
                if is_frozen:
                    phys_dmg = int(phys_dmg * 1.8)
                    logs.append(f"❄️ PHÁ BĂNG! SilverAsh quét kiếm gây x1.8 sát thương lên {enemy.name} đang bị đông cứng!")
                dmg = max(1, phys_dmg)
                
                # Check shield
                has_shield = any(b.name == "Lá chắn" for b in enemy.buffs)
                if has_shield:
                    enemy.buffs = [b for b in enemy.buffs if b.name != "Lá chắn"]
                    logs.append(f"🛡️ {enemy.name} sử dụng Lá chắn hấp thụ hoàn toàn sát thương Quét kiếm!")
                else:
                    enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                    if any(b.name == "Lá chắn phép" for b in enemy.buffs):
                        logs.append(f"✨ {enemy.name} kháng hiệu ứng Giá lạnh nhờ Lá chắn phép.")
                    else:
                        enemy.debuffs.append(RPGDebuff(name="Giá lạnh", duration=6))
                        logs.append(f"❄️ {attacker.name} quét kiếm gây {dmg} sát thương và để lại 1 tầng Giá lạnh lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                        
                        # Kích hoạt nội tại Kỷ băng hà ngay lập tức
                        frost_count = sum(1 for d in enemy.debuffs if d.name == "Giá lạnh")
                        if frost_count >= 2:
                            enemy.debuffs = [d for d in enemy.debuffs if d.name != "Giá lạnh"]
                            enemy.debuffs.append(RPGDebuff(name="Đông cứng", duration=1))
                            logs.append(f"❄️ Nội tại 'Kỷ băng hà' kích hoạt! Chuyển {frost_count} tầng Giá lạnh thành Đông cứng (1 lượt)!")
                            RPGEngine.sync_character_stats(enemy, 1)

            # Caster Skill 1: Vây hãm (đặt quân cờ/20% nổ)
            elif attacker.special_skills.skill_1 == "Vây hãm":
                attacker.special_skills.skill_1_countdown = 2
                
                # Check 20% explosion of the new piece
                exploded = random.random() < 0.20
                if exploded:
                    dmg = max(1, int(0.50 * attacker.stats.res * (1 - enemy.stats.res_def / 100)))
                    enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                    logs.append(f"💥 Quân cờ mới đặt phát nổ gây {dmg} sát thương ma pháp lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                else:
                    attacker.special_skills.quan_co_count += 1
                    logs.append(f"♟️ {attacker.name} đặt thêm 1 quân cờ lên sân (Tổng cộng: {attacker.special_skills.quan_co_count} quân cờ).")
                
                # 15% chance to double the total count of chess pieces (Passive Khai triển)
                if attacker.special_skills.passive_skill == "Khai triển" and random.random() < 0.15:
                    attacker.special_skills.quan_co_count *= 2
                    logs.append(f"🔮 Nội tại 'Khai triển' kích hoạt! Bộ đếm quân cờ tăng gấp đôi thành {attacker.special_skills.quan_co_count} quân.")

            # Sniper Skill 1: Khóa mục tiêu (auto firing mode setup)
            elif attacker.special_skills.skill_1 == "Khóa mục tiêu":
                if attacker.special_skills.bullet_count <= 0:
                    logs.append(f"⚠️ {attacker.name} không còn đạn để dùng chiêu Khóa mục tiêu!")
                    return
                
                attacker.special_skills.skill_1_activating = True
                attacker.special_skills.skill_1_countdown = 8
                
                # Sau khi kích hoạt Lemuen sẽ bắn ngay 1 viên đạn
                enemy = combat_state.enemy
                if enemy and enemy.stats.hp > 0:
                    dmg = max(1, int(random.uniform(0.60, 1.00) * attacker.stats.atk * (1 - enemy.stats.defense / 100)))
                    enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                    attacker.special_skills.bullet_count -= 1
                    logs.append(f"🎯 Lemuen kích hoạt 'Khóa mục tiêu'! Khởi động trạng thái khóa mục tiêu và bắn ngay 1 viên đạn gây {dmg} sát thương lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}, Số đạn còn lại: {attacker.special_skills.bullet_count}).")
                    cls.check_and_trigger_death(enemy, combat_state, logs)
                    
                    if attacker.special_skills.bullet_count <= 0:
                        attacker.special_skills.skill_1_activating = False
                        logs.append(f"🎯 Lemuen đã bắn hết đạn Khóa mục tiêu, kết thúc trạng thái khóa.")

            # Angel Skill 1: Lá chắn (buff Angel + 1 target ally, duration=2)
            elif attacker.special_skills.skill_1 == "Lá chắn":
                attacker.special_skills.skill_1_countdown = 5
                target = next((c for c in combat_state.combat_party if c.character_id == target_id and c.stats.hp > 0), None)
                
                if not target or target.character_id == attacker.character_id:
                    other_allies = [c for c in combat_state.combat_party if c.character_id != attacker.character_id and c.stats.hp > 0]
                    if other_allies:
                        target = other_allies[0]
                        
                shielded = [attacker]
                if target:
                    shielded.append(target)
                
                for char in shielded:
                    char.buffs = [b for b in char.buffs if b.name != "Lá chắn"]
                    char.buffs.append(RPGBuff(name="Lá chắn", duration=2))
                
                names = " & ".join([c.name for c in shielded])
                logs.append(f"🛡️ Angel ban phước 'Lá chắn' bảo hộ cho {names} trong 2 lượt.")

            # Devil Skill 1: Hấp thụ (hút 15% HP target)
            elif attacker.special_skills.skill_1 == "Hấp thụ":
                attacker.special_skills.skill_1_countdown = 4
                
                target = next((c for c in combat_state.combat_party if c.character_id == target_id), None)
                if not target or target.stats.hp <= 0:
                    target = enemy
                    
                dmg = int(target.stats.hp * 0.15)
                if target.character_id != enemy.character_id:
                    target.stats.hp = max(1, target.stats.hp - dmg)
                    logs.append(f"😈 Devil kích hoạt 'Hấp thụ', hút {dmg} HP từ đồng đội {target.name} (HP của {target.name} còn lại: {target.stats.hp}).")
                else:
                    target.stats.hp = max(0, target.stats.hp - dmg)
                    logs.append(f"😈 Devil kích hoạt 'Hấp thụ', hút {dmg} HP từ kẻ địch {target.name} (Enemy HP: {target.stats.hp}).")
                    
                attacker.stats.hp = min(attacker.stats.max_hp, attacker.stats.hp + dmg)
                logs.append(f"😈 HP của Devil tăng lên: {attacker.stats.hp}/{attacker.stats.max_hp}.")

            # Elf Skill 1: Mưa tên (+20%SPD, 2-5 mũi tên chuẩn)
            elif attacker.special_skills.skill_1 == "Mưa tên":
                attacker.special_skills.skill_1_countdown = 4
                attacker.buffs.append(RPGBuff(name="Tăng tốc", duration=1))
                
                arrows = random.randint(2, 5)
                total_dmg = 0
                for _ in range(arrows):
                    dmg = max(1, int(0.20 * attacker.stats.atk))
                    total_dmg += dmg
                    
                enemy.stats.hp = max(0, enemy.stats.hp - total_dmg)
                logs.append(f"🏹 Elf bắn liên hoàn 'Mưa tên' ({arrows} mũi tên) gây tổng {total_dmg} sát thương chuẩn lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                
                attacker.debuffs.append(RPGDebuff(name="Sơ hở", duration=1))
                logs.append(f"⚠️ {attacker.name} lâm vào trạng thái sơ hở, nhận thêm 20% sát thương từ đòn đánh tiếp theo trong lượt này.")

            # Royalty Skill 1: Phong tước (hy sinh 50% HP reset CD 1 đồng minh chỉ định)
            elif attacker.special_skills.skill_1 == "Phong tước":
                attacker.special_skills.skill_1_countdown = 999  # 1 lần duy nhất
                
                hp_loss = int(attacker.stats.hp * 0.50)
                attacker.stats.hp = max(1, attacker.stats.hp - hp_loss)
                
                target = next((c for c in combat_state.combat_party if c.character_id == target_id), None)
                if target:
                    target.special_skills.skill_1_countdown = 0
                    target.special_skills.skill_2_countdown = 0
                    logs.append(f"👑 Royalty hiến tế {hp_loss} HP của bản thân để phong tước cho {target.name}, làm mới toàn bộ thời gian hồi chiêu của nhân vật này! (Royalty HP: {attacker.stats.hp}/{attacker.stats.max_hp})")
                else:
                    logs.append(f"👑 Royalty hiến tế {hp_loss} HP nhưng không tìm thấy đồng đội hợp lệ.")

        # 3. Skill 2
        elif skill_name == "skill_2":
            if attacker.special_skills.skill_2_countdown > 0:
                logs.append(f"⚠️ Chiêu thức 2 đang hồi ({attacker.special_skills.skill_2_countdown} lượt nữa)!")
                return
                
            # Defender Skill 2: Hoả liên trảm quỷ (6 chém ma pháp)
            if attacker.special_skills.skill_2 == "Hoả liên trảm quỷ":
                attacker.special_skills.skill_2_countdown = 10
                logs.append(f"🔥 {attacker.name} kích hoạt 'Hoả liên trảm quỷ', chém 6 nhát kiếm lửa cuồng bạo và kích hoạt Bất tử trong lượt này!")
                
                attacker.buffs.append(RPGBuff(name="Bất tử", duration=1))
                
                total_dmg = 0
                total_heal = 0
                for i in range(6):
                    hp_lost = attacker.stats.max_hp - attacker.stats.hp
                    dmg = max(1, int(0.60 * hp_lost * (1 - enemy.stats.res_def / 100))) if hp_lost > 0 else 0
                    heal = int(0.05 * hp_lost)
                    
                    enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                    attacker.stats.hp = min(attacker.stats.max_hp, attacker.stats.hp + heal)
                    total_dmg += dmg
                    total_heal += heal
                
                logs.append(f"💥 6 nhát chém lửa phép gây tổng {total_dmg} sát thương phép lên {enemy.name} và hồi {total_heal} HP cho Hoshiguma (Hoshiguma HP: {attacker.stats.hp}/{attacker.stats.max_hp}, Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Guard Skill 2: Phán quyết cuối cùng (60%ATK chuẩn + 40%ATK vật lý)
            elif attacker.special_skills.skill_2 == "Phán quyết cuối cùng":
                attacker.special_skills.skill_2_countdown = 6
                true_dmg = int(attacker.stats.atk * 0.60)
                phys_dmg = int(attacker.stats.atk * 0.40 * (1 - enemy.stats.defense / 100))
                
                crit_triggered = random.random() < 0.20
                crit_dmg = 0
                if crit_triggered:
                    crit_dmg = int(attacker.stats.atk * 0.30)
                
                dmg = max(1, true_dmg + phys_dmg + crit_dmg)
                enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                
                crit_msg = f" (🔥 BẠO KÍCH! +{crit_dmg} sát thương chuẩn)" if crit_triggered else ""
                logs.append(f"⚖️ VinaVictoria hành quyết 'Phán quyết cuối cùng' gây {dmg} sát thương ({true_dmg} chuẩn + {phys_dmg} vật lý{crit_msg}) lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Guard Skill 2: Băng tuyết vũ (SilverAsh - chém 5 nhát vật lý)
            elif attacker.special_skills.skill_2 == "Băng tuyết vũ":
                attacker.special_skills.skill_2_countdown = 8
                logs.append(f"❄️ {attacker.name} kích hoạt 'Băng tuyết vũ', thi triển 5 nhát kiếm chớp nhoáng xé toạc không gian!")
                
                total_dmg = 0
                for i in range(5):
                    # Check né đòn Elf
                    if enemy.special_skills.passive_skill == "Uyển chuyển" and random.random() < 0.20:
                        logs.append(f"   💨 Nhát chém {i+1}: {enemy.name} né tránh thành công!")
                        continue
                        
                    is_frozen = any(d.name == "Đông cứng" for d in enemy.debuffs)
                    phys_dmg = int(attacker.stats.atk * (1 - enemy.stats.defense / 100))
                    
                    if is_frozen:
                        phys_dmg = int(phys_dmg * 1.8)
                        logs.append(f"   ❄️ Nhát chém {i+1}: Gây {phys_dmg} sát thương vật lý lên mục tiêu Đông cứng (x1.8)!")
                    else:
                        logs.append(f"   ⚔️ Nhát chém {i+1}: Gây {phys_dmg} sát thương vật lý.")
                    
                    # Check shield
                    has_shield = any(b.name == "Lá chắn" for b in enemy.buffs)
                    if has_shield:
                        enemy.buffs = [b for b in enemy.buffs if b.name != "Lá chắn"]
                        logs.append(f"      🛡️ Bị Lá chắn của {enemy.name} cản lại!")
                    else:
                        enemy.stats.hp = max(0, enemy.stats.hp - phys_dmg)
                        total_dmg += phys_dmg
                        cls.check_and_trigger_death(enemy, combat_state, logs)
                        if enemy.stats.hp <= 0:
                            break
                            
                logs.append(f"💥 Băng tuyết vũ gây tổng cộng {total_dmg} sát thương vật lý lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Caster Skill 2: Chiếu tướng (30%*count*RES ma pháp)
            elif attacker.special_skills.skill_2 == "Chiếu tướng":
                if attacker.special_skills.quan_co_count == 0:
                    logs.append(f"⚠️ Không có quân cờ nào trên bàn cờ để kích hoạt Chiếu tướng!")
                    return
                attacker.special_skills.skill_2_countdown = 10
                count = attacker.special_skills.quan_co_count
                
                dmg = int(0.30 * count * attacker.stats.res * (1 - enemy.stats.res_def / 100))
                dmg = max(1, dmg)
                
                enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                attacker.special_skills.quan_co_count = 0
                logs.append(f"♟️ Vương cờ kích hoạt 'Chiếu tướng' bùng nổ {count} quân cờ gây {dmg} sát thương ma pháp lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Sniper Skill 2: Khai hoả toàn diện (bắn hết đạn)
            elif attacker.special_skills.skill_2 == "Khai hoả toàn diện":
                if attacker.special_skills.bullet_count == 0:
                    logs.append(f"⚠️ {attacker.name} không còn đạn để kích hoạt Khai hoả toàn diện!")
                    return
                attacker.special_skills.skill_2_countdown = 10
                bullets = attacker.special_skills.bullet_count
                attacker.special_skills.bullet_count = 0
                
                logs.append(f"🔫 Lemuen kích hoạt 'Khai hoả toàn diện', dội bão tên lửa gồm {bullets} viên đạn thường kèm 1 viên đặc biệt!")
                
                total_dmg = 0
                for i in range(bullets):
                    mult = random.uniform(0.80, 1.90)
                    dmg = max(1, int(mult * attacker.stats.atk * (1 - enemy.stats.defense / 100)))
                    total_dmg += dmg
                    logs.append(f"   🚀 Tên lửa {i+1}: gây {dmg} sát thương vật lý.")
                
                # Special bullet
                special_mult = random.uniform(1.00, 3.00)
                special_dmg = max(1, int(special_mult * attacker.stats.atk * (1 - enemy.stats.defense / 100)))
                total_dmg += special_dmg
                logs.append(f"   🔥 Tên lửa đặc biệt: gây {special_dmg} sát thương vật lý.")
                
                enemy.stats.hp = max(0, enemy.stats.hp - total_dmg)
                logs.append(f"💥 Khai hoả toàn diện gây tổng cộng {total_dmg} sát thương lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")

            # Angel Skill 2: Thiên lôi (30 chuẩn, 30% tê liệt)
            elif attacker.special_skills.skill_2 == "Thiên lôi":
                attacker.special_skills.skill_2_countdown = 3
                dmg = 30
                enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                logs.append(f"⚡ Angel triệu hồi 'Thiên lôi' giáng xuống {dmg} sát thương chuẩn lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                if random.random() < 0.30:
                    enemy.debuffs.append(RPGDebuff(name="Tê liệt", duration=2))
                    logs.append(f"⚡ {enemy.name} trúng lôi đình bị 'Tê liệt' trong 2 lượt!")

            # Devil Skill 2: Huyết quỷ thuật (lấy máu team + bùng nổ)
            elif attacker.special_skills.skill_2 == "Huyết quỷ thuật":
                attacker.special_skills.skill_2_countdown = 6
                hp_pool = 0
                
                # Take 20% current HP from other allies
                for char in combat_state.combat_party:
                    if char.character_id != attacker.character_id and char.stats.hp > 0:
                        lost = int(char.stats.hp * 0.20)
                        char.stats.hp = max(1, char.stats.hp - lost)
                        hp_pool += lost
                        logs.append(f"🩸 Devil rút {lost} HP của đồng đội {char.name} làm vật tế.")
                
                # Take 30% current HP of self
                self_lost = int(attacker.stats.hp * 0.30)
                attacker.stats.hp = max(1, attacker.stats.hp - self_lost)
                hp_pool += self_lost
                logs.append(f"🩸 Devil hiến tế {self_lost} HP của bản thân.")
                
                dmg = max(1, int(hp_pool * (1 - enemy.stats.res_def / 100)))
                enemy.stats.hp = max(0, enemy.stats.hp - dmg)
                logs.append(f"🩸 Devil bùng nổ quả cầu Huyết Quỷ gây {dmg} sát thương phép lên {enemy.name} (Enemy HP: {enemy.stats.hp}/{enemy.stats.max_hp}).")
                
                if random.random() < 0.30:
                    if any(b.name == "Lá chắn phép" for b in enemy.buffs):
                        logs.append(f"✨ {enemy.name} kháng hiệu ứng Thiêu đốt nhờ Lá chắn phép.")
                    else:
                        enemy.debuffs.append(RPGDebuff(name="Thiêu đốt", duration=5))
                        logs.append(f"🔥 {enemy.name} trúng huyết hỏa nhận hiệu ứng 'Thiêu đốt' trong 5 lượt!")

        # If enemy took damage, register it
        if enemy and enemy.stats.hp < old_enemy_hp and acted_or_hit_ids is not None:
            acted_or_hit_ids.add(enemy.character_id)

        # Recalculate stats in case HP/buff modifications happened
        alive_allies_count = sum(1 for c in combat_state.combat_party if c.stats.hp > 0)
        RPGEngine.sync_character_stats(attacker, alive_allies_count)
        RPGEngine.sync_character_stats(enemy, 1)

    @classmethod
    def enemy_turn(cls, combat_state: RPGCombatState, defender_id: str | None, logs: list[str], acted_or_hit_ids: set[str] = None) -> None:
        """Executes the automatic enemy action with custom Elite Boss & Alpha skills."""
        enemy = combat_state.enemy
        if not enemy or enemy.stats.hp <= 0:
            return

        # Check if enemy is stunned / feared / frozen
        is_stunned = any(d.name in ["Choáng", "Sợ hãi", "Đông cứng"] for d in enemy.debuffs)
        if is_stunned:
            logs.append(f"💤 {enemy.name} bị khống chế (Choáng/Sợ hãi/Đông cứng), không thể hành động lượt này!")
            return

        if acted_or_hit_ids is not None:
            acted_or_hit_ids.add(enemy.character_id)

        # Determine target: Hoshiguma intercepts first. Else, select a target.
        target = None
        
        # Check if Hoshiguma (Valkyrie Defender) is alive in party (hp > 0 and not failed revival)
        hoshi = next((c for c in combat_state.combat_party if c.name == "Hoshiguma the breacher" and c.stats.hp > 0), None)
        
        if hoshi:
            target = hoshi
            logs.append(f"🛡️ Hoshiguma khiêu khích kẻ địch! {enemy.name} buộc phải hướng đòn tấn công vào cô.")
        else:
            # Random target
            alive_allies = [c for c in combat_state.combat_party if c.stats.hp > 0]
            if not alive_allies:
                return
            target = random.choice(alive_allies)

        # Apply defender shielding if player set a defender and it's not the target
        if not hoshi and defender_id and defender_id != target.character_id:
            defender = next((c for c in combat_state.combat_party if c.character_id == defender_id and c.stats.hp > 0), None)
            if defender:
                # Roll shield success
                def_chance = DEFEND_CHANCES.get(defender.char_class, 20)
                # Apply Tê liệt block penalty on defender
                if any(d.name == "Tê liệt" for d in defender.debuffs):
                    def_chance = 0 # Cannot defend if paralyzed
                    logs.append(f"💨 {defender.name} bị tê liệt nên không thể thực hiện đỡ đòn đỡ hộ!")
                
                if def_chance > 0 and random.uniform(0, 100) <= def_chance:
                    logs.append(f"🛡️ {defender.name} đã đỡ đòn thành công bảo vệ {target.name}!")
                    target = defender
                else:
                    logs.append(f"💨 {defender.name} cố gắng đỡ đòn bảo vệ {target.name} nhưng thất bại!")

        # Execute Enemy Attack
        is_frozen = any(d.name == "Đông cứng" for d in target.debuffs)
        phys_dmg = int(enemy.stats.atk * (1 - target.stats.defense / 100))
        mag_dmg = int(enemy.stats.res * (1 - target.stats.res_def / 100))
        
        if is_frozen:
            if enemy.name == "SilverAsh the Reignfrost":
                phys_dmg = int(phys_dmg * 1.8)
                logs.append(f"❄️ PHÁ BĂNG! SilverAsh của kẻ địch gây x1.8 sát thương vật lý lên {target.name} đang bị đông cứng!")
            else:
                phys_dmg = int(phys_dmg * 1.5)
                logs.append(f"❄️ PHÁ BĂNG! {enemy.name} gây x1.5 sát thương vật lý lên {target.name} đang bị đông cứng!")
                
        dmg = max(1, phys_dmg, mag_dmg)
        
        # Elite Boss Custom Attack Modifiers: WereWolf, Poseidon, Alpha
        if enemy.name == "WereWolf" and enemy.stats.hp / enemy.stats.max_hp < 0.20 and random.random() < 0.20:
            dmg = dmg * 2
            logs.append(f"💥 WereWolf phẫn nộ kích hoạt 'Cuồng loạn' chém x2 sát thương!")
        elif enemy.name == "Poseidon" and random.random() < 0.30:
            dmg = dmg * 2
            logs.append(f"🌊 Poseidon vung đinh ba vạn cân đánh x2 sát thương!")
        elif enemy.name == "Alpha" and random.random() < 0.10:
            dmg = dmg * 3
            logs.append(f"🌌 Alpha vung trường thương đen kích hoạt đánh x3 sát thương!")

        # Apply Elf Mưa tên negative modifier (Sơ hở debuff)
        has_so_ho = any(d.name == "Sơ hở" for d in target.debuffs)
        if has_so_ho:
            dmg = int(dmg * 1.20)
            
        # Check shield on target
        has_shield = any(b.name == "Lá chắn" for b in target.buffs)
        if has_shield:
            dmg = 0
            target.buffs = [b for b in target.buffs if b.name != "Lá chắn"]
            logs.append(f"🛡️ {target.name} chặn hoàn toàn sát thương nhờ Lá chắn!")
        else:
            target.stats.hp = max(0, target.stats.hp - dmg)
            so_ho_msg = " (trúng Sơ hở +20%)" if has_so_ho else ""
            logs.append(f"💥 Kẻ địch {enemy.name} tấn công gây {dmg} sát thương{so_ho_msg} lên {target.name} (HP: {target.stats.hp}/{target.stats.max_hp}).")
            
            if dmg > 0:
                if acted_or_hit_ids is not None:
                    acted_or_hit_ids.add(target.character_id)
                # Check Hoshiguma passive interruption
                if target.special_skills.passive_skill == "Ma thần bất diệt" and target.special_skills.hoshi_passive_countdown > 0:
                    target.special_skills.hoshi_passive_countdown = -1
                    logs.append(f"💥 Hoshiguma đang trong quá trình hồi sinh nhưng nhận sát thương, 'Ma thần bất diệt' bị hủy bỏ hoàn toàn!")
            
            # Elite Boss & Alpha Debuffs & Healing/Lifesteal
            if target.stats.hp > 0:
                has_magic_shield = any(b.name == "Lá chắn phép" for b in target.buffs)
                if has_magic_shield:
                    logs.append(f"✨ {target.name} kháng hoàn toàn hiệu ứng bất lợi từ kẻ địch nhờ Lá chắn phép.")
                else:
                    if enemy.name == "Medusa":
                        if random.random() < 0.20:
                            target.debuffs.append(RPGDebuff(name="Tê liệt", duration=2))
                            logs.append(f"🤢 {target.name} bị tê liệt bởi ánh nhìn của Medusa!")
                        if random.random() < 0.10:
                            target.debuffs.append(RPGDebuff(name="Chảy máu", duration=3))
                            logs.append(f"🤢 {target.name} bị chảy máu bởi nọc độc Medusa!")
                    elif enemy.name == "Vua Goblin":
                        if random.random() < 0.30:
                            target.debuffs.append(RPGDebuff(name="Chảy máu", duration=3))
                            logs.append(f"🤢 {target.name} bị chảy máu bởi đại đao của Vua Goblin!")
                    elif enemy.name == "WereWolf":
                        if enemy.stats.hp / enemy.stats.max_hp >= 0.20 and random.random() < 0.10:
                            target.debuffs.append(RPGDebuff(name="Chảy máu", duration=3))
                            logs.append(f"🤢 {target.name} bị cào rách vai, nhận hiệu ứng Chảy máu!")
                    elif enemy.name == "Dracula":
                        if random.random() < 0.10:
                            target.debuffs.append(RPGDebuff(name="Chảy máu", duration=3))
                            logs.append(f"🤢 {target.name} bị cắn chảy máu xối xả!")
                    elif enemy.name == "Golem":
                        if random.random() < 0.10:
                            target.debuffs.append(RPGDebuff(name="Choáng", duration=1))
                            logs.append(f"🤢 {target.name} bị chấn động mạnh dẫn đến Choáng!")
                    elif enemy.name == "Diablo":
                        if random.random() < 0.20:
                            target.debuffs.append(RPGDebuff(name="Thiêu đốt", duration=3))
                            logs.append(f"🤢 {target.name} bị thiêu đốt bởi ngọn lửa Địa Ngục của Diablo!")
                    elif enemy.name == "Thiên Dực Long Vương":
                        if random.random() < 0.20:
                            target.debuffs.append(RPGDebuff(name="Tê liệt", duration=2))
                            logs.append(f"🤢 {target.name} bị dòng điện của Thiên Dực Long Vương làm tê liệt!")
                    elif enemy.name == "Ma vương Xương Cốt":
                        if random.random() < 0.20:
                            target.debuffs.append(RPGDebuff(name="Chảy máu", duration=3))
                            logs.append(f"🤢 {target.name} bị chảy máu do kiếm khí hắc ám!")
                    elif enemy.name == "Alpha":
                        if random.random() < 0.30:
                            possible_debuffs = ["Chảy máu", "Thiêu đốt", "Tê liệt", "Choáng", "Chậm chạp", "Yếu đuối", "Sợ hãi", "Giá lạnh"]
                            debuff_name = random.choice(possible_debuffs)
                            duration = 2 if debuff_name in ["Choáng", "Tê liệt"] else 3
                            target.debuffs.append(RPGDebuff(name=debuff_name, duration=duration))
                            logs.append(f"🤢 Alpha áp đặt quyền năng hư không, {target.name} chịu hiệu ứng {debuff_name}!")
                    else:
                        debuff_data = ENEMY_DEBUFF_CHANCE.get(enemy.race, {"chance": 0, "debuffs": []})
                        if debuff_data["chance"] > 0 and random.uniform(0, 100) <= debuff_data["chance"]:
                            debuff_name = random.choice(debuff_data["debuffs"])
                            target.debuffs.append(RPGDebuff(name=debuff_name, duration=3))
                            logs.append(f"🤢 {target.name} chịu tác động xấu '{debuff_name}'!")

            # Lifesteal check for Dracula, Diablo, Alpha
            if enemy.stats.hp > 0:
                heal = 0
                if enemy.name == "Dracula" and random.random() < 0.20:
                    heal = int((enemy.stats.max_hp - enemy.stats.hp) * 0.20)
                    logs.append(f"🧛 Dracula hút máu kẻ địch hồi phục {heal} HP!")
                elif enemy.name == "Diablo" and random.random() < 0.10:
                    heal = int((enemy.stats.max_hp - enemy.stats.hp) * 0.30)
                    logs.append(f"😈 Diablo hút hồn hồi phục {heal} HP!")
                elif enemy.name == "Alpha" and random.random() < 0.10:
                    heal = int((enemy.stats.max_hp - enemy.stats.hp) * 0.40)
                    logs.append(f"🌌 Alpha đảo ngược thời gian hồi phục {heal} HP!")

                if heal > 0:
                    enemy.stats.hp = min(enemy.stats.max_hp, enemy.stats.hp + heal)
                    RPGEngine.sync_character_stats(enemy, 1)

            # Splash damage check for Thiên Dực Long Vương
            if enemy.name == "Thiên Dực Long Vương" and random.random() < 0.10:
                other_allies = [c for c in combat_state.combat_party if c.character_id != target.character_id and c.stats.hp > 0]
                if other_allies:
                    other = random.choice(other_allies)
                    splash = int(dmg * 0.50)
                    other.stats.hp = max(0, other.stats.hp - splash)
                    logs.append(f"🔥 Thiên Dực Long Vương quật đuôi gây {splash} sát thương lan lên {other.name}!")
                    cls.check_and_trigger_death(other, combat_state, logs)
                    RPGEngine.sync_character_stats(other, len(combat_state.combat_party))

            # Trigger death checks on target
            cls.check_and_trigger_death(target, combat_state, logs)

        # Sync stats
        RPGEngine.sync_character_stats(target, len(combat_state.combat_party))
    @classmethod
    def check_combat_outcome(cls, combat_state: RPGCombatState) -> tuple[bool, str | None]:
        """Checks if combat is over. Returns (is_over, result)."""
        if combat_state.enemy.stats.hp <= 0:
            combat_state.is_active = False
            return True, "win"
            
        player_char = next((c for c in combat_state.combat_party if c.is_player_character), None)
        if player_char and player_char.stats.hp <= 0:
            combat_state.is_active = False
            return True, "lose"

        alive_allies = [c for c in combat_state.combat_party if c.stats.hp > 0]
        if not alive_allies:
            combat_state.is_active = False
            return True, "lose"
            
        return False, None

    @classmethod
    def check_combat_outcome_non_mutating(cls, combat_state: RPGCombatState) -> tuple[bool, str | None]:
        """Same as above but doesn't change active status (read-only checking)."""
        if combat_state.enemy.stats.hp <= 0:
            return True, "win"
            
        player_char = next((c for c in combat_state.combat_party if c.is_player_character), None)
        if player_char and player_char.stats.hp <= 0:
            return True, "lose"
            
        alive_allies = [c for c in combat_state.combat_party if c.stats.hp > 0]
        if not alive_allies:
            return True, "lose"
        return False, None


# ==================== EVENT SYSTEM ====================

class EventEngine:



    @staticmethod
    def apply_monk_blessing(party: RPGParty, inventory: RPGInventory) -> tuple[list[str], RPGParty, RPGInventory]:
        """Applies blessing from monk. Full heal, clear debuffs, +1 Holy Water item."""
        logs = []
        for char in party.active + party.reserve:
            # if char.stats.hp > 0: # Only heal living companions
            char.stats.hp = char.stats.max_hp
            char.debuffs = []
            logs.append(f"😇 {char.name} được giải trừ tai kiếp, phục hồi sinh lực (HP: {char.stats.hp}/{char.stats.max_hp}).")
                
        # Generate Holy Water (Bình nước thánh, Epic consume)
        holy_water = RPGItem(
            item_id=str(uuid.uuid4())[:8],
            name="Bình nước thánh",
            rarity="Epic",
            item_type="Consume",
            stats_bonus={},
            description="Hồi HP = 70% Max_HP, xóa Debuff",
            sell_price=SELL_PRICES["Epic"],
            buy_price=BUY_PRICES["Epic"]
        )
        
        # Add to inventory
        existing = next((i for i in inventory.items if i.name == holy_water.name), None)
        if existing:
            existing.quantity += 1
        else:
            inventory.items.append(holy_water)
            
        logs.append(f"🎒 Bạn được tu sĩ tặng 1x Bình nước thánh (thêm vào hành trang).")
        return logs, party, inventory

    @staticmethod
    def roll_item_pickup(inventory: RPGInventory, rarity_probs: dict[str, float] = None) -> tuple[list[str], RPGInventory]:
        """Rolls item drop event. 1-3 items + 5-80 gold."""
        if rarity_probs is None:
            rarity_probs = ITEM_FIND_RARITY_PROBS
            
        logs = []
        item_count = random.randint(1, 3)
        gold_found = random.randint(5, 80)
        
        inventory.gold += gold_found
        logs.append(f"💰 Tìm thấy túi tiền chứa {gold_found} vàng! (Vàng hiện tại: {inventory.gold})")
        
        for _ in range(item_count):
            item = RPGEngine.generate_random_item(rarity_probs=rarity_probs)
            existing = next((i for i in inventory.items if i.name == item.name), None)
            if existing:
                existing.quantity += 1
            else:
                inventory.items.append(item)
            logs.append(f"🎁 Lượm được vật phẩm: [{item.rarity}] {item.name} ({item.item_type}).")
            
        return logs, inventory

    @staticmethod
    def calculate_combat_drops(enemy: RPGCharacter) -> tuple[int, int, list[RPGItem]]:
        """Calculates gold, EXP, and items dropped when an enemy is killed."""
        if enemy.name in ["Medusa", "Vua Goblin", "WereWolf", "Dracula", "Golem"]:
            gold_gained = 200
            exp_gained = 200
            items_count = 5
            probs = {"Mythic": 10, "Legendary": 20, "Epic": 25, "Rare": 30, "Uncommon": 10, "Common": 5}
        elif enemy.name in ["Poseidon", "Diablo", "Thiên Dực Long Vương", "Ma vương Xương Cốt"]:
            gold_gained = 360
            exp_gained = 360
            items_count = 6
            probs = {"Mythic": 10, "Legendary": 20, "Epic": 25, "Rare": 30, "Uncommon": 10, "Common": 5}
        elif enemy.name == "Alpha":
            gold_gained = 600
            exp_gained = 600
            items_count = 10
            probs = {"Mythic": 10, "Legendary": 20, "Epic": 25, "Rare": 30, "Uncommon": 10, "Common": 5}
        else:
            rarity = enemy.rarity
            drop_data = DROP_TABLE.get(rarity, DROP_TABLE["Common"])
            gold_gained = drop_data["gold"]
            exp_gained = drop_data["exp"]
            items_count = drop_data["items"]
            probs = drop_data["probs"]
        
        dropped_items = []
        for _ in range(items_count):
            item_rarity = RPGEngine.roll_by_probability(probs)
            item = RPGEngine.generate_random_item(rarity=item_rarity)
            dropped_items.append(item)
            
        return gold_gained, exp_gained, dropped_items


# ==================== SHOP ENGINE ====================

class ShopEngine:

    @staticmethod
    def generate_shop_stock(shop_level: int, player_level: int) -> tuple[list[RPGItem], list[RPGCharacter]]:
        """Generates shop catalog items & mercenaries for sale based on level."""
        slots_count = SHOP_SLOTS.get(shop_level, 4)
        rarity_probs = SHOP_RARITY_PROBS.get(shop_level, SHOP_RARITY_PROBS[1])
        
        items_stock = []
        mercenaries_stock = []
        
        for _ in range(slots_count):
            # Generate Item
            item_rarity = RPGEngine.roll_by_probability(rarity_probs)
            item = RPGEngine.generate_random_item(rarity=item_rarity)
            items_stock.append(item)
            
            # Generate Mercenary
            merc_rarity = RPGEngine.roll_by_probability(rarity_probs)
            # Create a custom temp probs to force specific rarity
            force_probs = {merc_rarity: 100.0}
            merc = RPGEngine.generate_random_character(player_level=player_level, rarity_probs=force_probs)
            mercenaries_stock.append(merc)
            
        return items_stock, mercenaries_stock

    @staticmethod
    def upgrade_shop(shop: RPGShopState, inventory: RPGInventory) -> tuple[bool, str, RPGShopState, RPGInventory]:
        """Upgrades the shop to the next level."""
        if shop.level >= 6:
            return False, "Shop đã đạt cấp tối đa (Cấp 6)!", shop, inventory
            
        cost = SHOP_UPGRADE_COSTS.get(shop.level, 100)
        if inventory.gold < cost:
            return False, f"Không đủ vàng! Cần {cost} vàng để nâng cấp (Bạn có {inventory.gold} vàng).", shop, inventory
            
        inventory.gold -= cost
        shop.level += 1
        return True, f"Nâng cấp shop thành công lên Cấp {shop.level}! (Đã tiêu {cost} vàng)", shop, inventory

    @staticmethod
    def buy_item(shop: RPGShopState, inventory: RPGInventory, item_index: int) -> tuple[bool, str, RPGShopState, RPGInventory]:
        """Buys an item from the shop stock."""
        if item_index < 0 or item_index >= len(shop.items_for_sale):
            return False, "Chỉ số vật phẩm không hợp lệ!", shop, inventory
            
        item = shop.items_for_sale[item_index]
        cost = item.buy_price if item.buy_price > 0 else BUY_PRICES.get(item.rarity, 30)
        
        if inventory.gold < cost:
            return False, f"Không đủ vàng! Giá mua: {cost} vàng (Bạn có {inventory.gold} vàng).", shop, inventory
            
        inventory.gold -= cost
        # Remove item from shop and put in inventory
        shop.items_for_sale.pop(item_index)
        
        # Add to inventory
        existing = next((i for i in inventory.items if i.name == item.name), None)
        if existing:
            existing.quantity += 1
        else:
            inventory.items.append(item)
            
        return True, f"Mua thành công [{item.rarity}] {item.name} với giá {cost} vàng!", shop, inventory

    @staticmethod
    def buy_mercenary(shop: RPGShopState, party: RPGParty, inventory: RPGInventory, merc_index: int) -> tuple[bool, str, RPGShopState, RPGParty, RPGInventory]:
        """Hires a mercenary from the shop stock."""
        if merc_index < 0 or merc_index >= len(shop.mercenaries_for_sale):
            return False, "Chỉ số lính thuê không hợp lệ!", shop, party, inventory
            
        merc = shop.mercenaries_for_sale[merc_index]
        cost = MERC_PRICES.get(merc.rarity, 50)
        
        if inventory.gold < cost:
            return False, f"Không đủ vàng! Giá thuê: {cost} vàng (Bạn có {inventory.gold} vàng).", shop, party, inventory
            
        # Check active + reserve limits
        total_party_count = len(party.active) + len(party.reserve)
        if total_party_count >= 9: # 4 active + 5 reserve max
            return False, "Đội hình đã đầy (Tối đa 4 chính thức + 5 dự bị)!", shop, party, inventory
            
        inventory.gold -= cost
        # Remove from shop stock
        shop.mercenaries_for_sale.pop(merc_index)
        
        # Add to reserve first, or active if active is not full (max 4)
        if len(party.active) < 4:
            party.active.append(merc)
            # Recalculate stats for VinaVictoria/others
            for c in party.active:
                RPGEngine.sync_character_stats(c, len(party.active))
            msg = f"Đã thuê [{merc.rarity}] {merc.name} gia nhập Đội hình chính thức!"
        else:
            party.reserve.append(merc)
            msg = f"Đã thuê [{merc.rarity}] {merc.name} đưa vào Đội hình dự bị!"
            
        return True, f"{msg} (Đã thanh toán {cost} vàng)", shop, party, inventory

    @staticmethod
    def sell_item(inventory: RPGInventory, item_id: str) -> tuple[bool, str, RPGInventory]:
        """Sells an item from inventory."""
        item = next((i for i in inventory.items if i.item_id == item_id), None)
        if not item:
            return False, "Không tìm thấy vật phẩm này trong hành trang!", inventory
            
        price = SELL_PRICES.get(item.rarity, 10)
        
        if item.quantity > 1:
            item.quantity -= 1
        else:
            inventory.items.remove(item)
            
        inventory.gold += price
        return True, f"Bán thành công {item.name} nhận lại {price} vàng!", inventory
