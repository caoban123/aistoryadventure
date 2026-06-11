import os

file_path = "d:/hcmus/HK4/Tư duy tính toán cho TTNT/final/aistoryadventure/app/services/rpg_service.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Replace imports
old_import = "from app.services.rpg_engine import RPGEngine, CombatEngine, EventEngine, ShopEngine"
new_import = """from app.services.rpg_engine import RPGEngine, CombatEngine, EventEngine, ShopEngine
from app.services.quest_engine import QuestEngine
from app.services.achievement_engine import AchievementEngine
from app.domain.rpg_models import RPGBuff, RPGDebuff"""

if old_import in content:
    content = content.replace(old_import, new_import)
else:
    print("Warning: Import statement not found!")

# 2. Add REGION_CATALOG & Helpers before RPGService class
class_declaration = "class RPGService:"
catalog_code = """REGION_CATALOG = {
    "Đồng bằng": {
        "major": "Vương đô Victoria",
        "minor": ["Ngôi làng của nhân loại", "Hang tối", "Tháp canh phòng thủ", "Phế tích bỏ hoang"],
        "dungeon": "Hầm ngục Đồng bằng"
    },
    "Đồi núi": {
        "major": "Long kinh thành",
        "minor": ["Ngôi làng của nhân loại", "Tiền đồn cướp bóc", "Tháp canh phòng thủ", "Hang tối", "Khu mỏ bỏ hoang"],
        "dungeon": "Hầm ngục Đồi núi"
    },
    "Rừng rậm": {
        "major": "Vương đô Londinium",
        "minor": ["Ngôi làng của Elf", "Tiền đồn cướp bóc", "Tháp canh phòng thủ của Elf", "Hang tối", "Đền cổ rừng sâu"],
        "dungeon": "Hầm ngục Rừng rậm"
    },
    "Núi lửa": {
        "major": "Tòa Thành Chúa Quỷ",
        "minor": ["Tiền đồn cướp bóc của Devil", "Hang tối", "Bệ triệu hồi quỷ dữ"],
        "dungeon": "Hầm ngục Núi lửa"
    },
    "Hoang mạc": {
        "major": "Thành Phố Tự Do",
        "minor": ["Ngôi làng của nhân loại", "Tiền đồn cướp bóc", "Tháp canh phòng thủ", "Kim tự tháp"],
        "dungeon": "Hầm ngục Hoang mạc"
    },
    "Núi tuyết": {
        "major": "Pháo Đài Mùa Đông",
        "minor": ["Ngôi làng của nhân loại", "Tiền đồn cướp bóc", "Tháp canh phòng thủ", "Hang tối", "Nhà thờ lớn bị bỏ hoang"],
        "dungeon": "Hầm ngục Núi tuyết"
    },
    "Thiên giới": {
        "major": "Thánh Đường Tối Cao The Light Heavens",
        "minor": ["Ngôi làng của Angel", "Tháp canh phòng thủ", "Vườn địa đàng"],
        "dungeon": "Hầm ngục Thiên giới"
    }
}

def sanitize_rolled_character(char, party) -> RPGCharacter:
    recruited_mythics = {c.name for c in party.active + party.reserve if c.rarity == "Mythic"}
    if char.rarity == "Mythic" and char.name in recruited_mythics:
        legendary_probs = {"Mythic": 0, "Legendary": 100, "Epic": 0, "Rare": 0, "Uncommon": 0, "Common": 0}
        new_char = RPGEngine.generate_random_character(char.level, legendary_probs)
        return new_char
    return char

class RPGService:"""

if class_declaration in content:
    content = content.replace(class_declaration, catalog_code)
else:
    print("Error: class RPGService not found!")
    exit(1)

# 3. Replace start_rpg_game definition
old_start_state = """        # Determine starting environment / region
        starting_region = request.region or ""
        ENVIRONMENTS = ["Đồng bằng", "Đồi núi", "Rừng rậm", "Núi lửa", "Hoang mạc", "Núi tuyết", "Thiên giới"]
        if starting_region == "Ngẫu nhiên" or not starting_region:
            starting_region = random.choice(ENVIRONMENTS)
            
        # 2. Build initial empty RPG Game State
        rpg_state = RPGGameState(
            turn_count=0,
            past_turn_is_special=False,
            party=RPGParty(active=[player_char], reserve=[]),
            inventory=RPGInventory(items=[], gold=0),
            shop=RPGShopState(level=1, items_for_sale=[], mercenaries_for_sale=[]),
            player_character=player_char,
            current_event=None,
            region=starting_region,
            environment=starting_region,
            current_region=None,
            objective=request.objective or ""
        )"""

new_start_state = """        # Determine starting environment / region
        starting_region = request.region or ""
        ENVIRONMENTS = ["Đồng bằng", "Đồi núi", "Rừng rậm", "Núi lửa", "Hoang mạc", "Núi tuyết", "Thiên giới"]
        if starting_region == "Ngẫu nhiên" or not starting_region:
            starting_region = random.choice(ENVIRONMENTS)
            
        # 2. Build initial empty RPG Game State
        rpg_state = RPGGameState(
            turn_count=0,
            past_turn_is_special=False,
            party=RPGParty(active=[player_char], reserve=[]),
            inventory=RPGInventory(items=[], gold=0),
            shop=RPGShopState(level=1, items_for_sale=[], mercenaries_for_sale=[]),
            player_character=player_char,
            current_event=None,
            region=starting_region,
            environment=starting_region,
            current_region=None,
            objective=request.objective or "",
            explored_regions=[],
            unlocked_fast_travel=[],
            dungeon_state=None,
            active_quests=[],
            achievements_progress=AchievementEngine.initialize_progress()
        )
        rpg_state.active_quests = QuestEngine.generate_initial_quests(rpg_state)"""

if old_start_state in content:
    content = content.replace(old_start_state, new_start_state)
else:
    # Let's try to match with windows CRLF line endings
    old_start_state_crlf = old_start_state.replace("\n", "\r\n")
    new_start_state_crlf = new_start_state.replace("\n", "\r\n")
    if old_start_state_crlf in content:
        content = content.replace(old_start_state_crlf, new_start_state_crlf)
    else:
        print("Warning: start_rpg_game state pattern not found!")

# 4. Insert generate_dungeon_enemy and roll_stranger_for_location methods inside RPGService class
methods_to_insert = """    def generate_dungeon_enemy(self, floor: int, environment: str) -> RPGCharacter:
        if floor == 1:
            race = random.choice(["Goblin", "Orc"])
            enemy = RPGEngine.generate_random_character(50, {"Mythic": 0, "Legendary": 0, "Epic": 0, "Rare": 0, "Uncommon": 50, "Common": 50})
            enemy.race = race
            enemy.name = f"{race} Hầm Ngục"
            RPGEngine.sync_character_stats(enemy, 1)
            enemy.stats.hp = enemy.stats.max_hp
            return enemy
        elif floor == 2:
            is_elite = random.random() < 0.50
            if is_elite:
                elites = ["Medusa", "Golem", "WereWolf", "Dracula", "Vua Goblin"]
                boss_name = random.choice(elites)
                enemy = RPGEngine.generate_random_character(50, {"Mythic": 0, "Legendary": 0, "Epic": 100, "Rare": 0, "Uncommon": 0, "Common": 0})
                enemy.name = boss_name
                if boss_name == "Medusa":
                    enemy.stats.max_hp = 500
                    enemy.stats.atk = 80
                    enemy.stats.defense = 40
                    enemy.stats.res = 100
                    enemy.stats.res_def = 60
                    enemy.stats.atk_spd = 90
                elif boss_name == "Vua Goblin":
                    enemy.stats.max_hp = 500
                    enemy.stats.atk = 100
                    enemy.stats.defense = 70
                    enemy.stats.res = 60
                    enemy.stats.res_def = 30
                    enemy.stats.atk_spd = 60
                elif boss_name == "WereWolf":
                    enemy.stats.max_hp = 500
                    enemy.stats.atk = 120
                    enemy.stats.defense = 60
                    enemy.stats.res = 20
                    enemy.stats.res_def = 20
                    enemy.stats.atk_spd = 70
                elif boss_name == "Dracula":
                    enemy.stats.max_hp = 500
                    enemy.stats.atk = 60
                    enemy.stats.defense = 40
                    enemy.stats.res = 120
                    enemy.stats.res_def = 40
                    enemy.stats.atk_spd = 80
                elif boss_name == "Golem":
                    enemy.stats.max_hp = 800
                    enemy.stats.atk = 100
                    enemy.stats.defense = 90
                    enemy.stats.res = 20
                    enemy.stats.res_def = 50
                    enemy.stats.atk_spd = 30
                enemy.stats.hp = enemy.stats.max_hp
                enemy.base_stats = enemy.stats.model_copy()
                return enemy
            else:
                enemy = RPGEngine.generate_random_character(50, {"Mythic": 0, "Legendary": 100, "Epic": 0, "Rare": 0, "Uncommon": 0, "Common": 0})
                enemy.race = "Devil"
                enemy.name = "Devil Hầm Ngục"
                RPGEngine.sync_character_stats(enemy, 1)
                enemy.stats.hp = enemy.stats.max_hp
                return enemy
        else: # floor == 3
            is_elite2 = random.random() < 0.50
            if is_elite2:
                elites2 = ["Poseidon", "Diablo", "Thiên Dực Long Vương", "Ma vương Xương Cốt"]
                boss_name = random.choice(elites2)
                enemy = RPGEngine.generate_random_character(50, {"Mythic": 0, "Legendary": 100, "Epic": 0, "Rare": 0, "Uncommon": 0, "Common": 0})
                enemy.name = boss_name
                if boss_name == "Poseidon":
                    enemy.race = "Fishman"
                    enemy.stats.max_hp = 1000
                    enemy.stats.atk = 150
                    enemy.stats.defense = 60
                    enemy.stats.res = 80
                    enemy.stats.res_def = 60
                    enemy.stats.atk_spd = 80
                elif boss_name == "Diablo":
                    enemy.race = "Devil"
                    enemy.stats.max_hp = 1000
                    enemy.stats.atk = 100
                    enemy.stats.defense = 70
                    enemy.stats.res = 150
                    enemy.stats.res_def = 40
                    enemy.stats.atk_spd = 70
                elif boss_name == "Thiên Dực Long Vương":
                    enemy.race = "Dragon"
                    enemy.stats.max_hp = 1000
                    enemy.stats.atk = 80
                    enemy.stats.defense = 60
                    enemy.stats.res = 160
                    enemy.stats.res_def = 40
                    enemy.stats.atk_spd = 60
                elif boss_name == "Ma vương Xương Cốt":
                    enemy.race = "Undead"
                    enemy.stats.max_hp = 1000
                    enemy.stats.atk = 100
                    enemy.stats.defense = 90
                    enemy.stats.res = 80
                    enemy.stats.res_def = 60
                    enemy.stats.atk_spd = 70
                enemy.stats.hp = enemy.stats.max_hp
                enemy.base_stats = enemy.stats.model_copy()
                return enemy
            else:
                elites = ["Medusa", "Golem", "WereWolf", "Dracula", "Vua Goblin"]
                boss_name = random.choice(elites)
                enemy = RPGEngine.generate_random_character(50, {"Mythic": 0, "Legendary": 0, "Epic": 100, "Rare": 0, "Uncommon": 0, "Common": 0})
                enemy.name = boss_name
                if boss_name == "Medusa":
                    enemy.stats.max_hp = 500
                    enemy.stats.atk = 80
                    enemy.stats.defense = 40
                    enemy.stats.res = 100
                    enemy.stats.res_def = 60
                    enemy.stats.atk_spd = 90
                elif boss_name == "Vua Goblin":
                    enemy.stats.max_hp = 500
                    enemy.stats.atk = 100
                    enemy.stats.defense = 70
                    enemy.stats.res = 60
                    enemy.stats.res_def = 30
                    enemy.stats.atk_spd = 60
                elif boss_name == "WereWolf":
                    enemy.stats.max_hp = 500
                    enemy.stats.atk = 120
                    enemy.stats.defense = 60
                    enemy.stats.res = 20
                    enemy.stats.res_def = 20
                    enemy.stats.atk_spd = 70
                elif boss_name == "Dracula":
                    enemy.stats.max_hp = 500
                    enemy.stats.atk = 60
                    enemy.stats.defense = 40
                    enemy.stats.res = 120
                    enemy.stats.res_def = 40
                    enemy.stats.atk_spd = 80
                elif boss_name == "Golem":
                    enemy.stats.max_hp = 800
                    enemy.stats.atk = 100
                    enemy.stats.defense = 90
                    enemy.stats.res = 20
                    enemy.stats.res_def = 50
                    enemy.stats.atk_spd = 30
                enemy.stats.hp = enemy.stats.max_hp
                enemy.base_stats = enemy.stats.model_copy()
                return enemy

    def roll_stranger_for_location(self, location: str, environment: str, level: int) -> RPGCharacter:
        # Custom probabilities for major regions
        if location in ["Vương đô Victoria", "Vương đô Londinium", "Long kinh thành", "Tòa Thành Chúa Quỷ", "Pháo Đài Mùa Đông", "Thánh Đường Tối Cao The Light Heavens", "Thành Phố Tự Do"]:
            r_roll = random.random()
            rarity = "Common"
            race = "Human"
            char_class = "Guard"
            gender = random.choice(["Male", "Female"])
            
            # Map specific major locations
            if location == "Vương đô Victoria":
                # Mythic 5% VinaVictoria, Legendary 8% (80% Angel, 20% Devil), Epic 12% Elf, Rare 20% Royalty, Uncommon 5% Orc, Common 50% (80% Human, 20% Goblin)
                if r_roll < 0.05:
                    rarity, race, char_class, gender = "Mythic", "Valkyrie", "Guard", "Female"
                elif r_roll < 0.13:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.80 else "Devil")
                elif r_roll < 0.25:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.45:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.50:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.80 else "Goblin")
            elif location == "Vương đô Londinium":
                # Mythic 0%, Legendary 5% (80% Angel, 20% Devil), Epic 20% Elf, Rare 20% Royalty, Uncommon 5% Orc, Common 50% (80% Human, 20% Goblin)
                if r_roll < 0.05:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.80 else "Devil")
                elif r_roll < 0.25:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.45:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.50:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.80 else "Goblin")
            elif location == "Long kinh thành":
                # Mythic 5% Wang, Legendary 8% (50% Angel, 50% Devil), Epic 12% Elf, Rare 15% Royalty, Uncommon 15% Orc, Common 45% (60% Human, 40% Goblin)
                if r_roll < 0.05:
                    rarity, race, char_class, gender = "Mythic", "Valkyrie", "Caster", "Male"
                elif r_roll < 0.13:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.25:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.40:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.55:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.60 else "Goblin")
            elif location == "Tòa Thành Chúa Quỷ":
                # Mythic 5% Hoshiguma, Legendary 15% (1% Angel, 99% Devil), Epic 8% Elf, Rare 12% Royalty, Uncommon 30% Orc, Common 30% (20% Human, 80% Goblin)
                if r_roll < 0.05:
                    rarity, race, char_class, gender = "Mythic", "Valkyrie", "Defender", "Female"
                elif r_roll < 0.20:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.01 else "Devil")
                elif r_roll < 0.28:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.40:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.70:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.20 else "Goblin")
            elif location == "Pháo Đài Mùa Đông":
                # Mythic 5% SilverAsh, Legendary 8% (50% Angel, 50% Devil), Epic 12% Elf, Rare 20% Royalty, Uncommon 10% Orc, Common 45% (60% Human, 40% Goblin)
                if r_roll < 0.05:
                    rarity, race, char_class, gender = "Mythic", "Valkyrie", "Guard", "Male"
                elif r_roll < 0.13:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.25:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.45:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.55:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.60 else "Goblin")
            elif location == "Thánh Đường Tối Cao The Light Heavens":
                # Mythic 5% Lemuen, Legendary 15% (99% Angel, 1% Devil), Epic 15% Elf, Rare 15% Royalty, Uncommon 5% Orc, Common 45% (90% Human, 10% Goblin)
                if r_roll < 0.05:
                    rarity, race, char_class, gender = "Mythic", "Valkyrie", "Sniper", "Female"
                elif r_roll < 0.20:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.99 else "Devil")
                elif r_roll < 0.35:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.50:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.55:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.90 else "Goblin")
            else: # "Thành Phố Tự Do"
                # Mythic 0%, Legendary 5% (40% Angel, 60% Devil), Epic 10% Elf, Rare 15% Royalty, Uncommon 25% Orc, Common 45% (40% Human, 60% Goblin)
                if r_roll < 0.05:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.40 else "Devil")
                elif r_roll < 0.15:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.30:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.55:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.40 else "Goblin")

            if rarity != "Mythic":
                char_class = random.choice(["Defender", "Guard", "Caster", "Sniper", "Supporter"])
            
            max_lvl = RARITY_MAX_LEVEL.get(rarity, 50)
            lvl = random.randint(max(1, level - 2), min(max_lvl, level + 2))
            
            char = RPGEngine.generate_random_character(lvl, {"Mythic": 0, "Legendary": 0, "Epic": 0, "Rare": 0, "Uncommon": 0, "Common": 100})
            char.rarity = rarity
            char.race = race
            char.char_class = char_class
            char.gender = gender
            if rarity == "Mythic":
                if char_class == "Defender":
                    char.name = "Hoshiguma the breacher"
                elif char_class == "Guard":
                    char.name = "VinaVictoria" if gender == "Female" else "SilverAsh the Reignfrost"
                elif char_class == "Caster":
                    char.name = "Wang"
                else:
                    char.name = "Lemuen"
            else:
                char.name = f"{race} Vô danh"
            RPGEngine.sync_character_stats(char, 1)
            char.stats.hp = char.stats.max_hp
            return char
            
        return RPGEngine.generate_random_character(level)"""

# We insert this method at the end of the start_rpg_game definition
# Let's find end of start_rpg_game: return { "session_id": ... }
old_start_return = """        return {
            "session_id": session.session_id,
            "player_character": player_char.model_dump(),
            "rpg_state": rpg_state.model_dump()
        }"""

new_start_return = """        return {
            "session_id": session.session_id,
            "player_character": player_char.model_dump(),
            "rpg_state": rpg_state.model_dump()
        }

""" + methods_to_insert

if old_start_return in content:
    content = content.replace(old_start_return, new_start_return)
else:
    old_start_return_crlf = old_start_return.replace("\n", "\r\n")
    new_start_return_crlf = new_start_return.replace("\n", "\r\n")
    if old_start_return_crlf in content:
        content = content.replace(old_start_return_crlf, new_start_return_crlf)
    else:
        print("Warning: start_rpg_game return pattern not found!")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Modification stage 1 completed!")
