import json
import random
import re
import uuid
from time import perf_counter
from typing import Any
from fastapi import BackgroundTasks
from app.config import get_settings
from app.ai.provider import get_text_provider
from app.ai.output_parser import _try_parse_json, _fallback_story
from app.ai.rpg_prompt import (
    build_rpg_start_prompt,
    build_rpg_turn_prompt,
    build_rpg_npc_description_prompt,
    build_rpg_combat_narrative_prompt,
    build_rpg_suggest_names_prompt,
    build_rpg_suggest_objectives_prompt,
    build_rpg_suggest_appearance_prompt
)
from app.domain.models import SessionState, Message, utc_now_iso
from app.domain.rpg_models import (
    RPGGameState, RPGCharacter, RPGItem, RPGEquipment,
    RPGParty, RPGInventory, RPGShopState, RPGCombatState, RPGCharacterStats
)
from app.services.rpg_engine import RPGEngine, CombatEngine, EventEngine, ShopEngine, RARITY_MAX_LEVEL
from app.services.quest_engine import QuestEngine
from app.services.achievement_engine import AchievementEngine
from app.domain.rpg_models import RPGBuff, RPGDebuff
from app.memory.firebase_store import FirebaseStore
from app.services.admin_service import AdminControlService
from app.services.safety_service import SafetyFilterService

def estimate_token_count(value: str) -> int:
    text = str(value or "")
    if not text:
        return 0
    return max(1, (len(text) + 3) // 4)

def parse_rpg_output(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    data = _try_parse_json(text)
    if not isinstance(data, dict):
        data = {}
        
    story = data.get("story", "")
    if not story:
        story = _fallback_story(text)
        
    choices = data.get("choices", [])
    if not isinstance(choices, list):
        choices = []
        
    cleaned_choices = []
    for item in choices:
        if isinstance(item, str):
            c_text = re.sub(r"^\s*[-*\d.)]+\s*", "", item).strip()
            if c_text:
                cleaned_choices.append(c_text)
                
    if not cleaned_choices:
        cleaned_choices = ["Đi sâu vào vùng đất mới", "Khám phá ngóc ngách xung quanh", "Tiếp tục di chuyển"]
        
    return {
        "story": story,
        "choices": cleaned_choices[:3]
    }

def copy_template_images(session_id: str):
    import os
    import shutil
    template_dir = os.path.join("frontend", "assets", "default_characters")
    dest_dir = os.path.join("frontend", "assets", "generated")
    os.makedirs(dest_dir, exist_ok=True)
    os.makedirs(template_dir, exist_ok=True)
    # Copy the Valkyries from root if they exist
    valkyries = {
        "Hoshiguma_the_Breacher.png": "Hoshiguma_the_breacher.png",
        "Lemuen.png": "Lemuen.png",
        "Vina_Victoria.png": "VinaVictoria.png",
        "Wang.png": "Wang.png",
        "SilverAsh_the_Reignfrost.png": "SilverAsh_the_Reignfrost.png"
    }
    for src_name, dest_name in valkyries.items():
        dest_path = os.path.join(template_dir, dest_name)
        if not os.path.exists(dest_path) and os.path.exists(src_name):
            try:
                shutil.copy(src_name, dest_path)
            except Exception as e:
                print(f"Error copying valkyrie {src_name}: {e}")

    # Now copy all templates for this session
    if os.path.exists(template_dir):
        for filename in os.listdir(template_dir):
            if filename.endswith(".png"):
                src_file = os.path.join(template_dir, filename)
                dest_file = os.path.join(dest_dir, f"{session_id}_{filename}")
                try:
                    shutil.copy(src_file, dest_file)
                except Exception as e:
                    print(f"Error copying template {filename}: {e}")

async def call_kaggle_api(url: str, data: dict) -> dict:
    import urllib.request
    import urllib.parse
    import json
    import asyncio
    
    def sync_post():
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=90) as response:
            return json.loads(response.read().decode("utf-8"))
            
    return await asyncio.to_thread(sync_post)

def save_base64_image(base64_str: str, dest_filename: str) -> str:
    import os
    import base64
    from app.config import get_settings
    
    settings = get_settings()
    if settings.is_production:
        dest_dir = "/data/ai-story/generated"
    else:
        dest_dir = os.path.join("frontend", "assets", "generated")
        
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, dest_filename)
    
    if "," in base64_str:
        base64_str = base64_str.split(",")[1]
        
    img_data = base64.b64decode(base64_str)
    with open(dest_path, "wb") as f:
        f.write(img_data)
        
    return f"assets/generated/{dest_filename}"

REGION_CATALOG = {
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

ENVIRONMENT_MAP = {
    "Đồng bằng & thảo nguyên": "Đồng bằng",
    "Đồng bằng thảo nguyên": "Đồng bằng",
    "Đồng bằng": "Đồng bằng",
    "Đồi núi & thung lũng": "Đồi núi",
    "Đồi núi": "Đồi núi",
    "Thung lũng": "Đồi núi",
    "Rừng rậm đại ngàn": "Rừng rậm",
    "Rừng rậm": "Rừng rậm",
    "Núi lửa & vực thẳm": "Núi lửa",
    "Núi lửa": "Núi lửa",
    "Sa mạc & hoang mạc": "Hoang mạc",
    "Hoang mạc & sa mạc": "Hoang mạc",
    "Hoang mạc": "Hoang mạc",
    "Sa mạc": "Hoang mạc",
    "Núi tuyết băng giá": "Núi tuyết",
    "Núi tuyết": "Núi tuyết",
    "Thiên giới linh thiêng": "Thiên giới",
    "Thiên giới": "Thiên giới"
}

ENVIRONMENT_EVENT_PROBS = {
    "Đồng bằng": {"stranger": 10, "merchant": 5, "monk": 5, "item": 10, "normal": 70},
    "Đồi núi": {"stranger": 10, "merchant": 5, "monk": 5, "item": 10, "normal": 70},
    "Rừng rậm": {"stranger": 10, "merchant": 5, "monk": 5, "item": 10, "normal": 70},
    "Núi lửa": {"stranger": 10, "merchant": 0, "monk": 0, "item": 20, "normal": 70},
    "Hoang mạc": {"stranger": 10, "merchant": 5, "monk": 5, "item": 10, "normal": 70},
    "Núi tuyết": {"stranger": 10, "merchant": 5, "monk": 5, "item": 10, "normal": 70},
    "Thiên giới": {"stranger": 10, "merchant": 5, "monk": 5, "item": 10, "normal": 70}
}

REGION_EVENT_PROBS = {
    # Major Locations
    "Vương đô Victoria": {"stranger": 20, "merchant": 10, "monk": 10, "item": 10, "normal": 50},
    "Thành Phố Tự Do": {"stranger": 20, "merchant": 10, "monk": 0, "item": 20, "normal": 50},
    "Vương đô Londinium": {"stranger": 20, "merchant": 10, "monk": 10, "item": 10, "normal": 50},
    "Long kinh thành": {"stranger": 20, "merchant": 10, "monk": 10, "item": 10, "normal": 50},
    "Tòa Thành Chúa Quỷ": {"stranger": 20, "merchant": 0, "monk": 0, "item": 30, "normal": 50},
    "Pháo Đài Mùa Đông": {"stranger": 20, "merchant": 10, "monk": 10, "item": 10, "normal": 50},
    "Thánh Đường Tối Cao The Light Heavens": {"stranger": 20, "merchant": 10, "monk": 10, "item": 10, "normal": 50},
    # Minor Locations
    "Ngôi làng của nhân loại": {"stranger": 20, "merchant": 10, "monk": 10, "item": 10, "normal": 50},
    "Hang tối": {"stranger": 20, "merchant": 0, "monk": 0, "item": 20, "normal": 60},
    "Tháp canh phòng thủ": {"stranger": 20, "merchant": 0, "monk": 10, "item": 10, "normal": 60},
    "Phế tích bỏ hoang": {"stranger": 20, "merchant": 0, "monk": 0, "item": 30, "normal": 50},
    "Tiền đồn cướp bóc": {"stranger": 20, "merchant": 0, "monk": 0, "item": 20, "normal": 60},
    "Kim tự tháp": {"stranger": 20, "merchant": 0, "monk": 0, "item": 30, "normal": 50},
    "Ngôi làng của Elf": {"stranger": 20, "merchant": 10, "monk": 10, "item": 10, "normal": 50},
    "Tháp canh phòng thủ của Elf": {"stranger": 20, "merchant": 0, "monk": 10, "item": 10, "normal": 60},
    "Đền cổ rừng sâu": {"stranger": 20, "merchant": 0, "monk": 0, "item": 30, "normal": 50},
    "Khu mỏ bỏ hoang": {"stranger": 20, "merchant": 0, "monk": 0, "item": 30, "normal": 50},
    "Tiền đồn cướp bóc của Devil": {"stranger": 20, "merchant": 0, "monk": 0, "item": 20, "normal": 60},
    "Bệ triệu hồi quỷ dữ": {"stranger": 20, "merchant": 0, "monk": 0, "item": 30, "normal": 50},
    "Nhà thờ lớn bị bỏ hoang": {"stranger": 20, "merchant": 0, "monk": 0, "item": 30, "normal": 50},
    "Ngôi làng của Angel": {"stranger": 20, "merchant": 10, "monk": 10, "item": 10, "normal": 50},
    "Tháp canh phòng thủ của Angel": {"stranger": 20, "merchant": 0, "monk": 10, "item": 10, "normal": 60},
    "Vườn địa đàng": {"stranger": 20, "merchant": 0, "monk": 10, "item": 20, "normal": 50}
}

def roll_event_from_probs(probs: dict[str, int]) -> str:
    roll = random.randint(1, 100)
    cumulative = 0
    for event, weight in probs.items():
        cumulative += weight
        if roll <= cumulative:
            return event
    return "normal"

def sanitize_rolled_character(char, party) -> RPGCharacter:
    recruited_mythics = {c.name.lower().replace(" ", "").replace("_", "") for c in party.active + party.reserve if c.rarity == "Mythic"}
    char_name_norm = char.name.lower().replace(" ", "").replace("_", "")
    if char.rarity == "Mythic" and char_name_norm in recruited_mythics:
        legendary_probs = {"Mythic": 0, "Legendary": 100, "Epic": 0, "Rare": 0, "Uncommon": 0, "Common": 0}
        new_char = RPGEngine.generate_random_character(char.level, legendary_probs)
        return new_char
    return char

class RPGService:
    def __init__(self) -> None:
        self.provider = get_text_provider()
        self.store = FirebaseStore()
        self.admin_control = AdminControlService()
        self.safety_filter = SafetyFilterService()

    def generate_monk_or_merchant(self, character_type: str, level: int) -> RPGCharacter:
        gender = random.choice(["Male", "Female"])
        race = random.choice(["Elf", "Royalty", "Human"])
        gender_viet = "Nam" if gender == "Male" else "Nữ"
        type_viet = "Tu sĩ" if character_type == "monk" else "Thương nhân"
        name = f"{gender_viet} {type_viet} tộc {race}"
        char_class = "Supporter" if character_type == "monk" else "Specialist"
        return RPGCharacter(
            character_id=f"{character_type}_{str(uuid.uuid4())[:8]}",
            name=name,
            race=race,
            char_class=char_class,
            rarity="Common",
            gender=gender,
            description=f"Một {type_viet.lower()} thuộc tộc {race}.",
            level=level,
            stats=RPGCharacterStats(
                max_hp=100,
                hp=100,
                atk=10,
                res=10,
                defense=10,
                res_def=10,
                atk_spd=10
            )
        )

    def copy_character_avatar(self, session_id: str, char: RPGCharacter):
        import os
        import shutil
        from app.config import get_settings
        
        settings = get_settings()
        if settings.is_production:
            dest_dir = "/data/ai-story/generated"
        else:
            dest_dir = os.path.join("frontend", "assets", "generated")
            
        src_filename = f"{session_id}_{char.race}_{char.char_class}.png".replace(" ", "_")
        dest_filename = f"{session_id}_{char.character_id}.png"
        
        src_path = os.path.join(dest_dir, src_filename)
        dest_path = os.path.join(dest_dir, dest_filename)
        
        if os.path.exists(src_path):
            try:
                shutil.copy(src_path, dest_path)
            except Exception as e:
                print(f"Error copying companion avatar: {e}")
        else:
            # Fallback to templates
            template_path = os.path.join("frontend", "assets", "default_characters", f"{char.race}_{char.char_class}.png")
            if os.path.exists(template_path):
                try:
                    shutil.copy(template_path, dest_path)
                except Exception as e:
                    print(f"Error copying from template: {e}")

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

    async def start_rpg_game(self, request: Any, user_id: str) -> dict[str, Any]:
        """Creates the initial SessionState and game models for RPG mode."""
        self.safety_filter.validate_input(request.player_name, "Tên người chơi")
        
        # 1. Create Specialist player character
        player_char = RPGEngine.generate_player_character(request.player_name, request.gender)
        if hasattr(request, "appearance_desc") and request.appearance_desc:
            player_char.description = request.appearance_desc
        
        # Determine starting environment / region
        starting_region = request.region or ""
        ENVIRONMENTS = ["Đồng bằng", "Đồi núi", "Rừng rậm", "Núi lửa", "Hoang mạc", "Núi tuyết", "Thiên giới"]
        if starting_region == "Thánh Đường Tối Cao":
            starting_region = "Thánh Đường Tối Cao The Light Heavens"
            
        start_env = None
        start_current_reg = None
        
        for env_name, data in REGION_CATALOG.items():
            if data.get("major") == starting_region:
                start_env = env_name
                start_current_reg = starting_region
                break
                
        if not start_env:
            if starting_region in ENVIRONMENTS:
                start_env = starting_region
            else:
                start_env = random.choice(ENVIRONMENTS)
                starting_region = start_env
                
        unlocked_list = []
        if start_current_reg:
            unlocked_list.append(start_current_reg)
            
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
            environment=start_env,
            current_region=start_current_reg,
            objective=request.objective or "",
            explored_regions=[],
            unlocked_fast_travel=unlocked_list,
            dungeon_state=None,
            active_quests=[],
            achievements_progress=AchievementEngine.initialize_progress()
        )
        rpg_state.active_quests = QuestEngine.generate_initial_quests(rpg_state)
        
        session = SessionState(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            is_saved=False,
            title=f"Hành trình RPG của {request.player_name}",
            mode="rpg",
            rpg_state=rpg_state.model_dump()
        )
        
        await self.store.create_session(session)
        return {
            "session_id": session.session_id,
            "player_character": player_char.model_dump(),
            "rpg_state": rpg_state.model_dump()
        }

    @staticmethod
    def _scale_boss_stats_by_level(enemy: RPGCharacter, player_level: int) -> None:
        """Scales boss stats by 1% per player level (excludes defense and res_def which remain fixed)."""
        if player_level <= 1:
            return
        scale = 1.0 + (player_level - 1) * 0.01
        enemy.stats.max_hp = int(enemy.stats.max_hp * scale)
        enemy.stats.hp = enemy.stats.max_hp
        enemy.stats.atk = int(enemy.stats.atk * scale)
        enemy.stats.res = int(enemy.stats.res * scale)
        enemy.stats.atk_spd = int(enemy.stats.atk_spd * scale)
        # DEF and Res_DEF are intentionally NOT scaled

    def generate_dungeon_enemy(self, floor: int, environment: str, player_level: int = 1) -> RPGCharacter:
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
                enemy.race = "Bí ẩn"
                enemy.char_class = "Bí ẩn"
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
                self._scale_boss_stats_by_level(enemy, player_level)
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
                enemy.race = "Bí ẩn"
                enemy.char_class = "Bí ẩn"
                if boss_name == "Poseidon":
                    enemy.stats.max_hp = 1000
                    enemy.stats.atk = 150
                    enemy.stats.defense = 60
                    enemy.stats.res = 80
                    enemy.stats.res_def = 60
                    enemy.stats.atk_spd = 80
                elif boss_name == "Diablo":
                    enemy.stats.max_hp = 1000
                    enemy.stats.atk = 100
                    enemy.stats.defense = 70
                    enemy.stats.res = 150
                    enemy.stats.res_def = 40
                    enemy.stats.atk_spd = 70
                elif boss_name == "Thiên Dực Long Vương":
                    enemy.stats.max_hp = 1000
                    enemy.stats.atk = 80
                    enemy.stats.defense = 60
                    enemy.stats.res = 160
                    enemy.stats.res_def = 40
                    enemy.stats.atk_spd = 60
                elif boss_name == "Ma vương Xương Cốt":
                    enemy.stats.max_hp = 1000
                    enemy.stats.atk = 100
                    enemy.stats.defense = 90
                    enemy.stats.res = 80
                    enemy.stats.res_def = 60
                    enemy.stats.atk_spd = 70
                enemy.stats.hp = enemy.stats.max_hp
                self._scale_boss_stats_by_level(enemy, player_level)
                enemy.base_stats = enemy.stats.model_copy()
                return enemy
            else:
                elites = ["Medusa", "Golem", "WereWolf", "Dracula", "Vua Goblin"]
                boss_name = random.choice(elites)
                enemy = RPGEngine.generate_random_character(50, {"Mythic": 0, "Legendary": 0, "Epic": 100, "Rare": 0, "Uncommon": 0, "Common": 0})
                enemy.name = boss_name
                enemy.race = "Bí ẩn"
                enemy.char_class = "Bí ẩn"
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
                self._scale_boss_stats_by_level(enemy, player_level)
                enemy.base_stats = enemy.stats.model_copy()
                return enemy

    def roll_stranger_for_location(self, location: str | None, environment: str, level: int, force_rarity: str | None = None) -> RPGCharacter:
        if force_rarity:
            for _ in range(1000):
                char = self.roll_stranger_for_location(location, environment, level, force_rarity=None)
                if char.rarity == force_rarity:
                    return char
            char = self.roll_stranger_for_location(location, environment, level, force_rarity=None)
            char.rarity = force_rarity
            max_lvl = RARITY_MAX_LEVEL.get(force_rarity, 50)
            char.level = min(char.level, max_lvl)
            RPGEngine.sync_character_stats(char, 1)
            char.stats.hp = char.stats.max_hp
            return char

        std_env = ENVIRONMENT_MAP.get(environment, environment)
        r_roll = random.random()
        rarity = "Common"
        race = "Human"
        char_class = "Guard"
        gender = random.choice(["Male", "Female"])

        # 1. Nếu location là None -> roll theo phân bổ của Environment
        if location is None:
            if std_env == "Đồng bằng":
                if r_roll < 0.02:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.10:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.25:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.50:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.60 else "Goblin")
            elif std_env == "Hoang mạc":
                if r_roll < 0.02:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.10:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.25:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.55:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.20 else "Goblin")
            elif std_env == "Núi lửa":
                if r_roll < 0.05:
                    rarity, race = "Legendary", "Devil"
                elif r_roll < 0.15:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.30:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.65:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.10 else "Goblin")
            elif std_env == "Núi tuyết":
                if r_roll < 0.05:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.15:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.35:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.65:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.60 else "Goblin")
            elif std_env == "Đồi núi":
                if r_roll < 0.02:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.10:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.25:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.55:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.40 else "Goblin")
            elif std_env == "Rừng rậm":
                if r_roll < 0.02:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.12:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.27:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.45:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.40 else "Goblin")
            else: # std_env == "Thiên giới"
                if r_roll < 0.05:
                    rarity, race = "Legendary", "Angel"
                elif r_roll < 0.15:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.35:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.45:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.90 else "Goblin")

        # 2. Nếu location là minor location
        elif location in [
            "Ngôi làng của nhân loại", "Hang tối", "Tháp canh phòng thủ", "Phế tích bỏ hoang",
            "Tiền đồn cướp bóc", "Kim tự tháp", "Ngôi làng của Elf", "Tháp canh phòng thủ của Elf",
            "Đền cổ rừng sâu", "Khu mỏ bỏ hoang", "Tiền đồn cướp bóc của Devil", "Bệ triệu hồi quỷ dữ",
            "Nhà thờ lớn bị bỏ hoang", "Ngôi làng của Angel", "Tháp canh phòng thủ của Angel", "Vườn địa đàng"
        ]:
            if location == "Ngôi làng của nhân loại":
                if r_roll < 0.02:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.10:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.25:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.40:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.80 else "Goblin")
            elif location == "Hang tối":
                if r_roll < 0.05:
                    rarity, race = "Legendary", "Devil"
                elif r_roll < 0.40:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.20 else "Goblin")
            elif location == "Tháp canh phòng thủ":
                if r_roll < 0.02:
                    rarity, race = "Legendary", "Angel"
                elif r_roll < 0.10:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.30:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.40:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.90 else "Goblin")
            elif location == "Phế tích bỏ hoang":
                if r_roll < 0.05:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.13:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.25:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.50:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.40 else "Goblin")
            elif location == "Tiền đồn cướp bóc":
                if r_roll < 0.02:
                    rarity, race = "Legendary", "Devil"
                elif r_roll < 0.05:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.10:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.40:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.10 else "Goblin")
            elif location == "Kim tự tháp":
                if r_roll < 0.05:
                    rarity, race = "Legendary", "Devil"
                elif r_roll < 0.13:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.25:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.50:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.40 else "Goblin")
            elif location == "Ngôi làng của Elf":
                if r_roll < 0.02:
                    rarity, race = "Legendary", "Angel"
                elif r_roll < 0.17:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.37:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.45:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.80 else "Goblin")
            elif location == "Tháp canh phòng thủ của Elf":
                if r_roll < 0.02:
                    rarity, race = "Legendary", "Angel"
                elif r_roll < 0.22:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.37:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.45:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.90 else "Goblin")
            elif location == "Đền cổ rừng sâu":
                if r_roll < 0.05:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.15:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.30:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.50:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.40 else "Goblin")
            elif location == "Khu mỏ bỏ hoang":
                if r_roll < 0.02:
                    rarity, race = "Legendary", "Devil"
                elif r_roll < 0.07:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.20:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.50:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.20 else "Goblin")
            elif location == "Tiền đồn cướp bóc của Devil":
                if r_roll < 0.08:
                    rarity, race = "Legendary", "Devil"
                elif r_roll < 0.13:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.25:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.60:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.10 else "Goblin")
            elif location == "Bệ triệu hồi quỷ dữ":
                if r_roll < 0.10:
                    rarity, race = "Legendary", "Devil"
                elif r_roll < 0.20:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.30:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.60:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.10 else "Goblin")
            elif location == "Nhà thờ lớn bị bỏ hoang":
                if r_roll < 0.05:
                    rarity, race = "Legendary", ("Angel" if random.random() < 0.50 else "Devil")
                elif r_roll < 0.15:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.30:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.55:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.20 else "Goblin")
            elif location == "Ngôi làng của Angel":
                if r_roll < 0.08:
                    rarity, race = "Legendary", "Angel"
                elif r_roll < 0.23:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.45:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.50:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.90 else "Goblin")
            elif location == "Tháp canh phòng thủ của Angel":
                if r_roll < 0.10:
                    rarity, race = "Legendary", "Angel"
                elif r_roll < 0.25:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.45:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.50:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.90 else "Goblin")
            else: # "Vườn địa đàng"
                if r_roll < 0.10:
                    rarity, race = "Legendary", "Angel"
                elif r_roll < 0.30:
                    rarity, race = "Epic", "Elf"
                elif r_roll < 0.50:
                    rarity, race = "Rare", "Royalty"
                elif r_roll < 0.55:
                    rarity, race = "Uncommon", "Orc"
                else:
                    rarity, race = "Common", ("Human" if random.random() < 0.90 else "Goblin")

        # 3. Nếu location là major region chính
        elif location in ["Vương đô Victoria", "Vương đô Londinium", "Long kinh thành", "Tòa Thành Chúa Quỷ", "Pháo Đài Mùa Đông", "Thánh Đường Tối Cao The Light Heavens", "Thành Phố Tự Do"]:
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
        else:
            return RPGEngine.generate_random_character(level)

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
        RPGEngine.init_character_skills(char)
        RPGEngine.sync_character_stats(char, 1)
        char.stats.hp = char.stats.max_hp
        return char

    async def roll_gold(self, session_id: str, user_id: str) -> dict[str, Any]:
        """Rolls a 6-sided die to obtain starting gold."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Bạn không có quyền truy cập session này.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        if rpg_state.turn_count > 0:
            raise ValueError("Chỉ có thể tung xúc xắc nhận vàng khi bắt đầu game.")
            
        dice_roll = random.randint(1, 6)
        gold = dice_roll * 50
        
        rpg_state.inventory.gold = gold
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "dice_roll": dice_roll,
            "gold_gained": gold,
            "rpg_state": session.rpg_state
        }

    async def roll_equipment(self, session_id: str, user_id: str) -> dict[str, Any]:
        """Rolls a 6-sided die to obtain a starting equipment (Weapon/Armor)."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Bạn không có quyền truy cập session này.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        if rpg_state.turn_count > 0:
            raise ValueError("Chỉ có thể nhận trang bị khởi đầu khi bắt đầu game.")
            
        dice_roll = random.randint(1, 6)
        item_type = "Weapon" if dice_roll <= 3 else "Armor"
        
        # Roll starter item
        item = RPGEngine.generate_random_item(rarity="Common", item_type=item_type)
        
        # Auto equip to player
        player = rpg_state.player_character
        if item.item_type == "Weapon":
            player.equipment.weapon = item
        else:
            player.equipment.armor = item
            
        # Recalculate player stats
        RPGEngine.sync_character_stats(player, len(rpg_state.party.active))
        
        # Update character copy inside party.active
        for char in rpg_state.party.active:
            if char.character_id == player.character_id:
                char.equipment = player.equipment
                RPGEngine.sync_character_stats(char, len(rpg_state.party.active))
                
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "dice_roll": dice_roll,
            "item": item.model_dump(),
            "rpg_state": session.rpg_state
        }

    async def start_rpg_story(self, session_id: str, user_id: str, region: str = None, objective: str = None, appearance_desc: str = None) -> dict[str, Any]:
        """Generates the opening narrative for the game."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        if appearance_desc:
            rpg_state.player_character.description = appearance_desc
            for c in rpg_state.party.active:
                if c.character_id == "player":
                    c.description = appearance_desc
        
        # Copy pre-generated template images to this session
        copy_template_images(session_id)
        
        if region:
            rpg_state.region = region
        if objective:
            rpg_state.objective = objective
            
        region_val = rpg_state.region or "Khu Rừng Đom Đóm"
        objective_val = rpg_state.objective or "Giải thoát Linh hồn Cây Cổ Thụ"
        
        prompt = build_rpg_start_prompt(
            player_name=rpg_state.player_character.name,
            gender=rpg_state.player_character.gender,
            region=region_val,
            objective=objective_val,
            gold=rpg_state.inventory.gold,
            equipment=rpg_state.player_character.equipment.model_dump()
        )
        
        raw_output = await self._generate_text_logged(
            prompt,
            user_id=user_id,
            session_id=session_id,
            operation="start_rpg.narrative"
        )
        
        parsed = parse_rpg_output(raw_output)
        
        # Advance turn count to 1
        rpg_state.turn_count = 1
        session.rpg_state = rpg_state.model_dump()
        
        # Create message log
        msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="ai",
            content=parsed["story"],
            choices=parsed["choices"]
        )
        await self.store.add_message(msg)
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "story": parsed["story"],
            "choices": parsed["choices"],
            "rpg_state": session.rpg_state,
            "message_id": msg.message_id
        }

    async def suggest_names(self, gender: str, user_id: str) -> dict[str, Any]:
        """Suggests 4 names via Gemini based on gender."""
        prompt = build_rpg_suggest_names_prompt(gender)
        raw_output = await self._generate_text_logged(
            prompt,
            user_id=user_id,
            session_id="global_rpg_setup",
            operation="rpg.suggest_names"
        )
        parsed = _try_parse_json(raw_output)
        # Handle parsed dict or string cases
        if isinstance(parsed, dict) and "names" in parsed:
            names = parsed["names"]
        else:
            names = ["Anh Hùng", "Hiệp Sĩ", "Chiến Binh", "Nhân Vật"]
        return {"names": names}

    async def suggest_objectives(self, user_id: str) -> dict[str, Any]:
        """Suggests 4 adventure objectives via Gemini."""
        prompt = build_rpg_suggest_objectives_prompt()
        raw_output = await self._generate_text_logged(
            prompt,
            user_id=user_id,
            session_id="global_rpg_setup",
            operation="rpg.suggest_objectives"
        )
        parsed = _try_parse_json(raw_output)
        if isinstance(parsed, dict) and "objectives" in parsed:
            objectives = parsed["objectives"]
        else:
            objectives = [
                "Khám phá ngôi đền cổ bị lãng quên",
                "Tìm kiếm báu vật vô giá",
                "Tiêu diệt Ma Vương chấn giữ biên giới",
                "Giải cứu dân làng bị bắt cóc"
            ]
        return {"objectives": objectives}

    async def suggest_appearance(
        self,
        player_name: str,
        gender: str,
        region: str,
        objective: str,
        gold: int,
        equipment_name: str,
        user_id: str
    ) -> dict[str, Any]:
        """Suggests appearance description via Gemini."""
        prompt = build_rpg_suggest_appearance_prompt(
            player_name=player_name,
            gender=gender,
            region=region,
            objective=objective,
            gold=gold,
            equipment_name=equipment_name
        )
        raw_output = await self._generate_text_logged(
            prompt,
            user_id=user_id,
            session_id="global_rpg_setup",
            operation="rpg.suggest_appearance"
        )
        return {"appearance": raw_output.strip()}

    async def process_turn(self, session_id: str, choice_index: int, user_id: str, background_tasks: BackgroundTasks | None = None) -> dict[str, Any]:
        """Executes a standard turn choice, processing event triggers or normal narrative flow."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        # Track old state values for background see-world and avatar triggers
        old_env = rpg_state.environment
        old_region = rpg_state.current_region
        old_offered = rpg_state.offered_event
        old_monk = rpg_state.current_monk
        old_merchant = rpg_state.current_merchant
        old_combat = rpg_state.combat
        old_stranger = rpg_state.current_stranger
        
        # Get last message to obtain the choice text
        messages = await self.store.get_messages(session_id, limit=100)
        last_msg = messages[-1] if messages else None
        choice_text = last_msg.choices[choice_index] if last_msg and len(last_msg.choices) > choice_index else "Tiếp tục đi tới"

        # Log player choice as user message
        user_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=choice_text
        )
        await self.store.add_message(user_msg)

        # 0. Đặc biệt: Check nếu đang ở Safe Zone của Dungeon
        if rpg_state.dungeon_state and rpg_state.dungeon_state.get("in_safe_zone"):
            story_text = ""
            choices = []
            if choice_index == 0:
                # Tiếp tục leo tháp
                floor = rpg_state.dungeon_state.get("floor", 1)
                rpg_state.dungeon_state["in_safe_zone"] = False
                
                # Sinh quái cho tầng tiếp theo
                player_level = rpg_state.player_character.level if rpg_state.player_character else 1
                enemy = self.generate_dungeon_enemy(floor, rpg_state.environment, player_level=player_level)
                
                # Tạo combat mới
                rpg_state.combat = RPGCombatState(
                    cb_turn_count=0,
                    combat_party=[c.model_copy() for c in rpg_state.party.active],
                    enemy=enemy,
                    combat_log=[],
                    is_active=True
                )
                rpg_state.current_event = None
                
                # AI viết truyện dẫn vào trận đấu
                prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả tổ đội bước tiếp lên tầng {floor} của hầm ngục và chạm trán kẻ địch hắc ám: {enemy.name}."
                story_text = await self._generate_text_logged(
                    prompt, user_id=user_id, session_id=session_id, operation=f"dungeon.floor_{floor}"
                )
                
                # Cập nhật quest/achievement nếu có
                rpg_state.turn_count += 1
                session.rpg_state = rpg_state.model_dump()
                await self.store.update_session(session)
                
                # Return combat format
                ai_msg = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="ai",
                    content=story_text,
                    choices=[] # Combat choices được sinh động từ client
                )
                await self.store.add_message(ai_msg)
                
                return {
                    "session_id": session_id,
                    "story": story_text,
                    "choices": [],
                    "event_type": None,
                    "rpg_state": session.rpg_state,
                    "message_id": ai_msg.message_id
                }
            else:
                # Rút lui khỏi hầm ngục
                # Nhận thưởng loot ảo
                gold_gained = rpg_state.dungeon_state.get("accumulated_gold", 0)
                exp_gained = rpg_state.dungeon_state.get("accumulated_exp", 0)
                items_gained = rpg_state.dungeon_state.get("accumulated_items", [])
                
                rpg_state.inventory.gold += gold_gained
                
                exp_logs = []
                if exp_gained > 0 and rpg_state.party.active:
                    exp_per_member = max(1, int(exp_gained / len(rpg_state.party.active)))
                    for char in rpg_state.party.active:
                        if char.stats.hp > 0:
                            lvl_logs = RPGEngine.add_exp(char, exp_gained, len(rpg_state.party.active))
                            exp_logs.extend(lvl_logs)
                            
                for char in rpg_state.party.active:
                    if char.is_player_character:
                        rpg_state.player_character = char
                        
                item_names = []
                for item in items_gained:
                    r_item = RPGItem.model_validate(item) if isinstance(item, dict) else item
                    existing = next((i for i in rpg_state.inventory.items if i.name == r_item.name), None)
                    if existing:
                        existing.quantity += 1
                    else:
                        rpg_state.inventory.items.append(r_item)
                    item_names.append(f"[{r_item.rarity}] {r_item.name}")
                    
                # Hủy dungeon state
                rpg_state.dungeon_state = None
                rpg_state.current_region = None
                rpg_state.current_event = None
                
                prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả tổ đội rút lui an toàn khỏi hầm ngục, mang theo đầy ắp tài bảo tích lũy. Thưởng: +{gold_gained} Vàng, +{exp_gained} EXP."
                story_text = await self._generate_text_logged(
                    prompt, user_id=user_id, session_id=session_id, operation="dungeon.leave"
                )
                
                drop_summary = f"\n\n💰 Nhận {gold_gained} vàng. (Tổng vàng: {rpg_state.inventory.gold})"
                drop_summary += f"\n📈 Toàn đội nhận +{exp_gained} EXP."
                if exp_logs:
                    drop_summary += "\n" + "\n".join(exp_logs)
                if item_names:
                    drop_summary += f"\n🎁 Vật phẩm mang về: {', '.join(item_names)}"
                story_text += drop_summary
                
                # Lượt di chuyển bình thường tiếp theo
                rpg_state.turn_count += 1
                
                # Check quest
                quest_notifs = QuestEngine.update_quest_progress(rpg_state, "sell_gold", {"gold": 0})
                ach_notifs = AchievementEngine.update_progress(rpg_state, "gold_accumulated", 0)
                
                if quest_notifs:
                    story_text += "\n\n" + "\n".join(quest_notifs)
                if ach_notifs:
                    story_text += "\n\n" + "\n".join(ach_notifs)
                    
                session.rpg_state = rpg_state.model_dump()
                
                # Lấy choices di chuyển ngoài map
                choices = ["Khám phá vùng đất mới", "Khám phá ngóc ngách xung quanh", "Tiếp tục di chuyển"]
                ai_msg = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="ai",
                    content=story_text,
                    choices=choices
                )
                await self.store.add_message(ai_msg)
                await self.store.update_session(session)
                
                return {
                    "session_id": session_id,
                    "story": story_text,
                    "choices": choices,
                    "event_type": None,
                    "rpg_state": session.rpg_state,
                    "message_id": ai_msg.message_id
                }

        # 0b. Đặc biệt: Check ending choice sau khi thắng Alpha
        if rpg_state.offered_event == "ending_choice":
            story_text = ""
            choices = []
            
            if choice_index == 0:
                # Good Ending
                prompt = "Viết bằng tiếng Việt (dưới 150 từ) miêu tả kết cục Good Ending: Người chơi bước qua cánh cổng ánh sáng trở về thế giới thực, lục địa hồi sinh, họ trở thành vị anh hùng cứu thế bất diệt đi vào lịch sử."
                story_text = await self._generate_text_logged(
                    prompt, user_id=user_id, session_id=session_id, operation="ending.good"
                )
                story_text = "✨ GOOD ENDING: CỨU THẾ HOÀN MỸ ✨\n\n" + story_text
                rpg_state.offered_event = None
                choices = []
            elif choice_index == 1:
                # Bad Ending
                prompt = "Viết bằng tiếng Việt (dưới 150 từ) miêu tả kết cục Bad Ending: Người chơi quyết định hấp thụ sức mạnh hư không, bị đồng hóa linh hồn và trở thành thực thể Alpha tiếp theo, mãi mãi canh giữ hố sâu vô tận."
                story_text = await self._generate_text_logged(
                    prompt, user_id=user_id, session_id=session_id, operation="ending.bad"
                )
                story_text = "💀 BAD ENDING: THỰC THỂ HƯ KHÔNG MỚI 💀\n\n" + story_text
                rpg_state.offered_event = None
                choices = []
            else:
                # Continue Ending
                prompt = "Viết bằng tiếng Việt (dưới 150 từ) miêu tả kết cục Continue Ending: Người chơi chém đôi cánh cổng hư không, kiên quyết ở lại thế giới này để bảo vệ đồng đội và tiếp tục những cuộc phiêu lưu bất tận khác."
                story_text = await self._generate_text_logged(
                    prompt, user_id=user_id, session_id=session_id, operation="ending.continue"
                )
                story_text = "⚔️ CONTINUE ENDING: HÀNH TRÌNH VÔ TẬN ⚔️\n\n" + story_text
                rpg_state.offered_event = None
                rpg_state.current_region = None
                # Hồi phục cả đội
                for c in rpg_state.party.active:
                    c.stats.hp = c.stats.max_hp
                if rpg_state.player_character:
                    rpg_state.player_character.stats.hp = rpg_state.player_character.stats.max_hp
                choices = ["Khám phá vùng đất mới", "Khám phá ngóc ngách xung quanh", "Tiếp tục di chuyển"]
                
            rpg_state.turn_count += 1
            session.rpg_state = rpg_state.model_dump()
            
            ai_msg = Message(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                role="ai",
                content=story_text,
                choices=choices
            )
            await self.store.add_message(ai_msg)
            await self.store.update_session(session)
            
            return {
                "session_id": session_id,
                "story": story_text,
                "choices": choices,
                "event_type": None,
                "rpg_state": session.rpg_state,
                "message_id": ai_msg.message_id
            }

        # 0c. Đặc biệt: Check người chơi chọn Rời khỏi region thường
        if rpg_state.current_region and not rpg_state.dungeon_state and ("Rời khỏi" in choice_text or "leave" in choice_text.lower()):
            rpg_state.current_region = None
            rpg_state.past_turn_is_special = True
            rpg_state.offered_event = None
            
            prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả cảnh tổ đội rời khỏi địa điểm khám phá và quay lại môi trường bản đồ thế giới {rpg_state.environment} rộng lớn."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="region.leave"
            )
            
            rpg_state.turn_count += 1
            session.rpg_state = rpg_state.model_dump()
            
            choices = ["Khám phá vùng đất mới", "Khám phá ngóc ngách xung quanh", "Tiếp tục di chuyển"]
            ai_msg = Message(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                role="ai",
                content=story_text,
                choices=choices
            )
            await self.store.add_message(ai_msg)
            await self.store.update_session(session)
            
            return {
                "session_id": session_id,
                "story": story_text,
                "choices": choices,
                "event_type": None,
                "rpg_state": session.rpg_state,
                "message_id": ai_msg.message_id
            }

        # 1. Handle event checking
        event_rolled = None
        offered_event_occurred = False
        
        if rpg_state.offered_event:
            # An event was offered in the previous turn.
            if choice_index == 0:
                # Player accepted the event (Choice 1) -> enter event now!
                rpg_state.current_event = rpg_state.offered_event
                event_rolled = rpg_state.current_event
                rpg_state.offered_event = None
                rpg_state.past_turn_is_special = True
                
                # Check if it was region or dungeon
                if event_rolled.startswith("region:"):
                    region_name = event_rolled.split(":", 1)[1]
                    rpg_state.current_region = region_name
                    
                    # Update explored major region
                    catalog = REGION_CATALOG.get(rpg_state.environment, {})
                    is_major = catalog.get("major") == region_name
                    if is_major:
                        if region_name not in rpg_state.explored_regions:
                            rpg_state.explored_regions.append(region_name)
                        if region_name not in rpg_state.unlocked_fast_travel:
                            rpg_state.unlocked_fast_travel.append(region_name)
                            
                    # Update quest meet
                    QuestEngine.update_quest_progress(rpg_state, "meet", {"target": "region"})
                    event_rolled = None
                    rpg_state.current_event = None
                elif event_rolled.startswith("dungeon:"):
                    dungeon_name = event_rolled.split(":", 1)[1]
                    rpg_state.current_region = dungeon_name
                    
                    # Khởi động hầm ngục ải 1
                    rpg_state.dungeon_state = {
                        "active": True,
                        "floor": 1,
                        "accumulated_gold": 0,
                        "accumulated_exp": 0,
                        "accumulated_items": [],
                        "in_safe_zone": False
                    }
                    player_level = rpg_state.player_character.level if rpg_state.player_character else 1
                    enemy = self.generate_dungeon_enemy(1, rpg_state.environment, player_level=player_level)
                    rpg_state.combat = RPGCombatState(
                        cb_turn_count=0,
                        combat_party=[c.model_copy() for c in rpg_state.party.active],
                        enemy=enemy,
                        combat_log=[],
                        is_active=True
                    )
                    
                    # AI viết truyện dẫn vào hầm ngục
                    prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả cảnh tổ đội dũng cảm tiến vào {dungeon_name} u ám, sương khói mờ nhân ảnh và chạm trán quái ải 1: {enemy.name}."
                    story_text = await self._generate_text_logged(
                        prompt, user_id=user_id, session_id=session_id, operation="dungeon.enter"
                    )
                    
                    rpg_state.current_event = None
                    rpg_state.offered_event = None
                    rpg_state.turn_count += 1
                    session.rpg_state = rpg_state.model_dump()
                    
                    ai_msg = Message(
                        message_id=str(uuid.uuid4()),
                        session_id=session_id,
                        role="ai",
                        content=story_text,
                        choices=[]
                    )
                    await self.store.add_message(ai_msg)
                    await self.store.update_session(session)
                    
                    return {
                        "session_id": session_id,
                        "story": story_text,
                        "choices": [],
                        "event_type": None,
                        "rpg_state": session.rpg_state,
                        "message_id": ai_msg.message_id
                    }
            else:
                # Player bypassed the event (Choice 2 or 3) -> proceed with normal story
                if rpg_state.offered_event and (rpg_state.offered_event.startswith("region:") or rpg_state.offered_event.startswith("dungeon:")):
                    rpg_state.bypass_region_turn = True
                rpg_state.offered_event = None
                event_rolled = None
        else:
            # Check if past turn was special or region was bypassed. If so, reset flag, no event rolled.
            if rpg_state.past_turn_is_special or rpg_state.bypass_region_turn:
                rpg_state.past_turn_is_special = False
                rpg_state.bypass_region_turn = False
            else:
                # Only choice_index == 0 can trigger random events/regions (Adventure choice)
                if choice_index == 0:
                    forced_event = rpg_state.debug_cheats.get("next_event")
                    forced_region = rpg_state.debug_cheats.get("next_region")
                    
                    if forced_region or forced_event:
                        if "next_event" in rpg_state.debug_cheats:
                            del rpg_state.debug_cheats["next_event"]
                        if "next_region" in rpg_state.debug_cheats:
                            del rpg_state.debug_cheats["next_region"]
                            
                        catalog = REGION_CATALOG.get(rpg_state.environment, {})
                        if forced_region == "main" and catalog.get("major"):
                            rpg_state.offered_event = f"region:{catalog['major']}"
                            offered_event_occurred = True
                        elif forced_region == "sub" and catalog.get("minor"):
                            rpg_state.offered_event = f"region:{random.choice(catalog['minor'])}"
                            offered_event_occurred = True
                        elif forced_region == "dungeon" and catalog.get("dungeon"):
                            rpg_state.offered_event = f"dungeon:{catalog['dungeon']}"
                            offered_event_occurred = True
                        elif forced_region == "none":
                            rpg_state.offered_event = None
                            event_rolled = "normal"
                            
                        if forced_event and forced_event != "normal":
                            rpg_state.offered_event = forced_event
                            offered_event_occurred = True
                            event_rolled = forced_event
                    elif rpg_state.current_region is None:
                        r_roll = random.random()
                        catalog = REGION_CATALOG.get(rpg_state.environment, {})
                        
                        if r_roll < 0.10 and catalog.get("major"):
                            # Gặp major
                            major_name = catalog["major"]
                            rpg_state.offered_event = f"region:{major_name}"
                            offered_event_occurred = True
                        elif r_roll < 0.30 and catalog.get("minor"):
                            # Gặp minor
                            minor_name = random.choice(catalog["minor"])
                            rpg_state.offered_event = f"region:{minor_name}"
                            offered_event_occurred = True
                        elif r_roll < 0.35 and catalog.get("dungeon"):
                            # Gặp dungeon
                            dungeon_name = catalog["dungeon"]
                            rpg_state.offered_event = f"dungeon:{dungeon_name}"
                            offered_event_occurred = True
                        else:
                            # Gặp sự kiện thường ngoài hoang dã (dựa trên environment)
                            std_env = ENVIRONMENT_MAP.get(rpg_state.environment, rpg_state.environment)
                            probs = ENVIRONMENT_EVENT_PROBS.get(std_env, {"stranger": 10, "merchant": 5, "monk": 5, "item": 10, "normal": 70})
                            event_rolled = roll_event_from_probs(probs)
                            if event_rolled and event_rolled != "normal":
                                rpg_state.offered_event = event_rolled
                                offered_event_occurred = True
                    else:
                        # Ở trong region, chỉ roll sự kiện thường (dựa trên region)
                        reg_name = rpg_state.current_region
                        probs = REGION_EVENT_PROBS.get(reg_name, {"stranger": 10, "merchant": 5, "monk": 5, "item": 10, "normal": 70})
                        event_rolled = roll_event_from_probs(probs)
                        if event_rolled and event_rolled != "normal":
                            rpg_state.offered_event = event_rolled
                            offered_event_occurred = True

        # 2. Process story and choices
        story_text = ""
        choices = []
        
        if event_rolled and event_rolled != "normal" and not offered_event_occurred:
            # Active event flow: Player is inside the event
            event_ctx = ""
            if event_rolled == "monk":
                choices = ["Trò chuyện", "Nhận phước lành", "Tạm biệt"]
                rpg_state.current_monk = self.generate_monk_or_merchant("monk", rpg_state.player_character.level)
                rpg_state.current_merchant = None
                event_ctx = f"Gặp {rpg_state.current_monk.name}."
                QuestEngine.update_quest_progress(rpg_state, "meet", {"target": "monk"})
            elif event_rolled == "merchant":
                choices = ["Trò chuyện", "Xem cửa hàng", "Tạm biệt"]
                rpg_state.current_merchant = self.generate_monk_or_merchant("merchant", rpg_state.player_character.level)
                rpg_state.current_monk = None
                event_ctx = f"Gặp {rpg_state.current_merchant.name}."
                items, mercs = ShopEngine.generate_shop_stock(rpg_state.shop.level, rpg_state.player_character.level)
                
                # Sanitize mythic rolled character
                sanitized_mercs = []
                for merc in mercs:
                    sanitized_mercs.append(sanitize_rolled_character(merc, rpg_state.party))
                
                rpg_state.shop.items_for_sale = items
                rpg_state.shop.mercenaries_for_sale = sanitized_mercs
                QuestEngine.update_quest_progress(rpg_state, "meet", {"target": "merchant"})
            elif event_rolled == "stranger":
                choices = ["Trò chuyện", "Tấn công", "Tránh xung đột"]
                
                # Stranger based on environment major location probability
                catalog = REGION_CATALOG.get(rpg_state.environment, {})
                loc = rpg_state.current_region or catalog.get("major", "")
                force_rarity = rpg_state.debug_cheats.get("next_stranger_rarity")
                if "next_stranger_rarity" in rpg_state.debug_cheats:
                    del rpg_state.debug_cheats["next_stranger_rarity"]
                stranger = self.roll_stranger_for_location(loc, rpg_state.environment, rpg_state.player_character.level, force_rarity=force_rarity)
                
                # Sanitize mythic rolled character
                stranger = sanitize_rolled_character(stranger, rpg_state.party)
                
                desc_prompt = build_rpg_npc_description_prompt(stranger)
                stranger.description = await self._generate_text_logged(
                    desc_prompt, user_id=user_id, session_id=session_id, operation="stranger.description"
                )
                rpg_state.current_stranger = stranger
                rpg_state.sympathy = 0
                event_ctx = f"Gặp người lạ mặt tên: {stranger.name} ({stranger.race} {stranger.char_class})."
                QuestEngine.update_quest_progress(rpg_state, "meet", {"target": "stranger"})
            elif event_rolled == "item":
                choices = ["Thu thập", "Bỏ qua"]
                event_ctx = "Một chiếc rương cũ lấp ló sau tàn đá."
                
            prompt = build_rpg_turn_prompt(
                session=session,
                recent_messages=messages + [user_msg],
                relevant_memories=[],
                player_input=choice_text,
                rpg_state_dict=rpg_state.model_dump(),
                event_type=event_rolled,
                event_context=event_ctx
            )
            raw_output = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation=f"event.{event_rolled}"
            )
            parsed = parse_rpg_output(raw_output)
            story_text = parsed["story"]
            
        elif offered_event_occurred:
            # Offered event flow: Player is NOT in event yet, we offer the trigger choice
            prompt = build_rpg_turn_prompt(
                session=session,
                recent_messages=messages + [user_msg],
                relevant_memories=[],
                player_input=choice_text,
                rpg_state_dict=rpg_state.model_dump(),
                event_type=None,
                offered_event=rpg_state.offered_event
            )
            raw_output = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation=f"offer_event.{rpg_state.offered_event}"
            )
            parsed = parse_rpg_output(raw_output)
            story_text = parsed["story"]
            ai_choices = parsed["choices"]
            
            trigger_text = ""
            if rpg_state.offered_event == "monk":
                trigger_text = "Đi đến gặp tu sĩ"
            elif rpg_state.offered_event == "merchant":
                trigger_text = "Đi đến gặp thương nhân"
            elif rpg_state.offered_event == "stranger":
                trigger_text = "Đi đến gặp kẻ lạ mặt"
            elif rpg_state.offered_event == "item":
                trigger_text = "Thu thập vật phẩm cho vào túi"
            elif rpg_state.offered_event.startswith("region:"):
                reg_name = rpg_state.offered_event.split(":", 1)[1]
                trigger_text = f"Khám phá {reg_name}"
            elif rpg_state.offered_event.startswith("dungeon:"):
                dun_name = rpg_state.offered_event.split(":", 1)[1]
                trigger_text = f"Tiến vào hầm ngục {dun_name}"
                
            choices = [trigger_text]
            if len(ai_choices) >= 1:
                choices.append(ai_choices[0])
            else:
                choices.append("Tiếp tục hành trình")
                
            if len(ai_choices) >= 2:
                choices.append(ai_choices[1])
            else:
                choices.append("Đi hướng khác")
                
        else:
            # Normal story flow
            prompt = build_rpg_turn_prompt(
                session=session,
                recent_messages=messages + [user_msg],
                relevant_memories=[],
                player_input=choice_text,
                rpg_state_dict=rpg_state.model_dump(),
                event_type=None
            )
            raw_output = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="story.turn"
            )
            parsed = parse_rpg_output(raw_output)
            story_text = parsed["story"]
            ai_choices = parsed["choices"]
            
            choices = ai_choices

        rpg_state.turn_count += 1
        
        # Check travels achievement progress
        if choice_index == 0:
            ach_notifs = AchievementEngine.update_progress(rpg_state, "travels", 1)
            if ach_notifs:
                story_text += "\n\n" + "\n".join(ach_notifs)
                
        session.rpg_state = rpg_state.model_dump()
        
        # Check if environment, region, or offered region changed to schedule background see-world image generation
        if background_tasks:
            new_env = rpg_state.environment
            new_region = rpg_state.current_region
            new_offered = rpg_state.offered_event
            
            env_changed = old_env != new_env
            region_changed = old_region != new_region
            offered_changed = (old_offered != new_offered) and (new_offered and (new_offered.startswith("region:") or new_offered.startswith("dungeon:")))
            
            if env_changed or region_changed or offered_changed:
                background_tasks.add_task(self.generate_world_image, session_id, user_id)
                
            # If dynamic monk/merchant were created, schedule their avatar generation in background
            if not old_monk and rpg_state.current_monk:
                background_tasks.add_task(self.refresh_character_image, session_id, rpg_state.current_monk.character_id, user_id)
            elif not old_merchant and rpg_state.current_merchant:
                background_tasks.add_task(self.refresh_character_image, session_id, rpg_state.current_merchant.character_id, user_id)
                
            # If a new combat enemy was set, schedule their avatar generation in background
            if rpg_state.combat and rpg_state.combat.is_active and rpg_state.combat.enemy:
                if not old_combat or not old_combat.is_active or (old_combat.enemy and old_combat.enemy.character_id != rpg_state.combat.enemy.character_id):
                    background_tasks.add_task(self.refresh_character_image, session_id, rpg_state.combat.enemy.character_id, user_id)
            
            # If a new stranger was set, schedule their avatar generation in background
            if rpg_state.current_stranger and (not old_stranger or old_stranger.character_id != rpg_state.current_stranger.character_id):
                background_tasks.add_task(self.refresh_character_image, session_id, rpg_state.current_stranger.character_id, user_id)
        
        # Save output message
        ai_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="ai",
            content=story_text,
            choices=choices
        )
        await self.store.add_message(ai_msg)
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "story": story_text,
            "choices": choices,
            "event_type": rpg_state.current_event,
            "rpg_state": session.rpg_state,
            "message_id": ai_msg.message_id
        }

    async def process_turn_prompt(self, session_id: str, player_input: str, user_id: str, background_tasks: BackgroundTasks | None = None) -> dict[str, Any]:
        """Handles custom text prompt entry instead of clicking preset choices."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        # Track old state values for background see-world triggers
        old_env = rpg_state.environment
        old_region = rpg_state.current_region
        old_offered = rpg_state.offered_event
        self.safety_filter.validate_input(player_input, "Nội dung người chơi viết")

        messages = await self.store.get_messages(session_id, limit=100)
        user_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=player_input
        )
        await self.store.add_message(user_msg)

        # Prompt turn resolves normally, resets special turn event checks
        rpg_state.past_turn_is_special = False
        
        prompt = build_rpg_turn_prompt(
            session=session,
            recent_messages=messages + [user_msg],
            relevant_memories=[],
            player_input=player_input,
            rpg_state_dict=rpg_state.model_dump(),
            event_type=None
        )
        
        raw_output = await self._generate_text_logged(
            prompt, user_id=user_id, session_id=session_id, operation="story.custom_turn"
        )
        parsed = parse_rpg_output(raw_output)
        
        rpg_state.turn_count += 1
        session.rpg_state = rpg_state.model_dump()
        
        # Check if environment or region changed to schedule background see-world image generation
        if background_tasks:
            new_env = rpg_state.environment
            new_region = rpg_state.current_region
            new_offered = rpg_state.offered_event
            
            env_changed = old_env != new_env
            region_changed = old_region != new_region
            offered_changed = (old_offered != new_offered) and (new_offered and (new_offered.startswith("region:") or new_offered.startswith("dungeon:")))
            
            if env_changed or region_changed or offered_changed:
                background_tasks.add_task(self.generate_world_image, session_id, user_id)
        
        ai_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="ai",
            content=parsed["story"],
            choices=parsed["choices"]
        )
        await self.store.add_message(ai_msg)
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "story": parsed["story"],
            "choices": parsed["choices"],
            "event_type": None,
            "rpg_state": session.rpg_state,
            "message_id": ai_msg.message_id
        }

    # ==================== SPECIAL EVENT ACTIONS ====================

    async def process_monk_action(self, session_id: str, action: str, user_id: str) -> dict[str, Any]:
        """Processes user decisions during the Monk blessing encounter."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        if rpg_state.current_event != "monk":
            raise ValueError("Không ở trong sự kiện tu sĩ.")

        # Log player action as user message
        user_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=action
        )
        await self.store.add_message(user_msg)
            
        messages = await self.store.get_messages(session_id, limit=100)
        
        story_text = ""
        choices = ["Trò chuyện", "Nhận phước lành", "Tạm biệt"]
        
        if action == "Trò chuyện":
            # AI dialogue narrative
            prompt = f"Viết tiếp lời thoại bằng tiếng việt (dưới 70 từ) khi người chơi chào hỏi vị tu sĩ trong đền thờ thiêng liêng. Tu sĩ chia sẻ một lời triết lý sâu sắc."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="monk.chat"
            )
            
        elif action == "Nhận phước lành":
            logs, party, inv = EventEngine.apply_monk_blessing(rpg_state.party, rpg_state.inventory)
            rpg_state.party = party
            rpg_state.inventory = inv
            
            # Recalculate stats & update player character
            for c in rpg_state.party.active:
                RPGEngine.sync_character_stats(c, len(rpg_state.party.active))
                if c.is_player_character:
                    rpg_state.player_character = c
                
            prompt = f"Viết một đoạn văn bằng tiếng Việt (dưới 80 từ) miêu tả vị tu sĩ tụng kinh cầu nguyện. Ánh sáng vàng rực bao phủ cơ thể cả đội, chữa lành mọi vết thương và tiêu trừ tà khí. Tu sĩ đưa một chai nước thánh cổ xưa."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="monk.bless"
            )
            choices = ["Tạm biệt"] # Only option left
            
        elif action == "Tạm biệt":
            # End event
            rpg_state.current_event = None
            rpg_state.past_turn_is_special = True
            
            prompt = f"Viết câu chuyện bằng tiếng Việt (dưới 80 từ) người chơi từ biệt tu sĩ hành hương, tiếp tục cất bước lên đường phiêu lưu."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="monk.farewell"
            )
            # Roll standard choices from AI
            ai_choices_prompt = build_rpg_turn_prompt(
                session=session,
                recent_messages=messages,
                relevant_memories=[],
                player_input="Từ biệt tu sĩ",
                rpg_state_dict=rpg_state.model_dump(),
                event_type=None
            )
            raw = await self._generate_text_logged(
                ai_choices_prompt, user_id=user_id, session_id=session_id, operation="monk.transition"
            )
            parsed = parse_rpg_output(raw)
            choices = parsed["choices"]

        session.rpg_state = rpg_state.model_dump()
        ai_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="ai",
            content=story_text,
            choices=choices
        )
        await self.store.add_message(ai_msg)
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "story": story_text,
            "choices": choices,
            "event_type": rpg_state.current_event,
            "rpg_state": session.rpg_state,
            "message_id": ai_msg.message_id
        }

    async def process_merchant_action(self, session_id: str, action: str, user_id: str) -> dict[str, Any]:
        """Processes user decisions during the Merchant encounter."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        if rpg_state.current_event != "merchant":
            raise ValueError("Không ở trong sự kiện thương nhân.")

        # Log player action as user message
        user_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=action
        )
        await self.store.add_message(user_msg)
            
        messages = await self.store.get_messages(session_id, limit=100)
        
        story_text = ""
        choices = ["Trò chuyện", "Xem cửa hàng", "Tạm biệt"]
        
        if action == "Trò chuyện":
            prompt = "Viết tiếp lời thoại hóm hỉnh của thương nhân lang thang bằng tiếng việt (dưới 60 từ) tiếp thị các cổ vật hiếm lạ."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="merchant.chat"
            )
            
        elif action == "Xem cửa hàng":
            # Just return a narrative note and trigger the front-end stock UI overlay
            prompt = "Viết bằng tiếng việt (dưới 50 từ) miêu tả thương nhân cười tươi mở tấm rèm phủ, hé lộ vô số bình thuốc, giáp trụ và lính đánh thuê sẵn sàng nhận vàng."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="merchant.browse"
            )
            
        elif action == "Tạm biệt":
            rpg_state.current_event = None
            rpg_state.past_turn_is_special = True
            
            prompt = "Viết câu chuyện bằng tiếng Việt (dưới 80 từ) người chơi gói ghém đồ đạc rời khỏi quầy của thương nhân lang thang, cất bước đi tiếp."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="merchant.farewell"
            )
            ai_choices_prompt = build_rpg_turn_prompt(
                session=session,
                recent_messages=messages,
                relevant_memories=[],
                player_input="Từ biệt thương nhân",
                rpg_state_dict=rpg_state.model_dump(),
                event_type=None
            )
            raw = await self._generate_text_logged(
                ai_choices_prompt, user_id=user_id, session_id=session_id, operation="merchant.transition"
            )
            parsed = parse_rpg_output(raw)
            choices = parsed["choices"]

        session.rpg_state = rpg_state.model_dump()
        ai_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="ai",
            content=story_text,
            choices=choices
        )
        await self.store.add_message(ai_msg)
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "story": story_text,
            "choices": choices,
            "event_type": rpg_state.current_event,
            "rpg_state": session.rpg_state,
            "message_id": ai_msg.message_id
        }

    async def process_stranger_action(self, session_id: str, action: str, user_id: str) -> dict[str, Any]:
        """Processes choices for the Stranger encounter (Talk, Attack, Avoid)."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        if rpg_state.current_event != "stranger" or not rpg_state.current_stranger:
            raise ValueError("Không ở trong sự kiện kẻ lạ mặt.")

        # Log player action as user message
        user_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=action
        )
        await self.store.add_message(user_msg)
            
        messages = await self.store.get_messages(session_id, limit=100)
        stranger = rpg_state.current_stranger
        
        story_text = ""
        choices = ["Trò chuyện", "Tấn công", "Tránh xung đột"]
        is_combat = False
        
        if action == "Trò chuyện":
            # Sympathy check: success chance base 30% + 10% * sympathy level
            success_chance = 30 + rpg_state.sympathy * 10
            roll = random.randint(1, 100)
            
            if roll <= success_chance:
                # Success! Joining the party
                total_party = len(rpg_state.party.active) + len(rpg_state.party.reserve)
                if total_party < 9:
                    if len(rpg_state.party.active) < 4:
                        rpg_state.party.active.append(stranger)
                        self.copy_character_avatar(session_id, stranger)
                        # Sync VinaVictoria/other stats
                        for c in rpg_state.party.active:
                            RPGEngine.sync_character_stats(c, len(rpg_state.party.active))
                        joined_msg = "đội hình chính thức"
                    else:
                        rpg_state.party.reserve.append(stranger)
                        self.copy_character_avatar(session_id, stranger)
                        joined_msg = "đội hình dự bị"
                        
                    prompt = f"Viết một đoạn bằng tiếng Việt (dưới 90 từ) miêu tả người lạ mặt cảm nhận được tấm lòng của người chơi và đồng ý gia nhập cuộc phiêu lưu. Tên họ là {stranger.name}."
                    story_text = await self._generate_text_logged(
                        prompt, user_id=user_id, session_id=session_id, operation="stranger.join_success"
                    )
                    story_text += f"\n\n👥 {stranger.name} đã gia nhập {joined_msg}!"
                else:
                    prompt = f"Viết bằng tiếng Việt (dưới 80 từ) miêu tả người lạ mặt cảm động muốn đồng hành cùng người chơi nhưng thấy quân đoàn quá đông đúc, nên chỉ tặng một ít lộ phí và chúc may mắn."
                    story_text = await self._generate_text_logged(
                        prompt, user_id=user_id, session_id=session_id, operation="stranger.join_full"
                    )
                    rpg_state.inventory.gold += 30
                    story_text += "\n\n💰 Nhận được 30 vàng làm quà tri ân!"
                    
                # End event
                rpg_state.current_event = None
                rpg_state.current_stranger = None
                rpg_state.past_turn_is_special = True
                
                ai_choices_prompt = build_rpg_turn_prompt(
                    session=session,
                    recent_messages=messages,
                    relevant_memories=[],
                    player_input="Tuyển dụng người lạ mặt thành công",
                    rpg_state_dict=rpg_state.model_dump(),
                    event_type=None
                )
                raw = await self._generate_text_logged(
                    ai_choices_prompt, user_id=user_id, session_id=session_id, operation="stranger.join.transition"
                )
                parsed = parse_rpg_output(raw)
                choices = parsed["choices"]
                
            else:
                # Failure outcomes: 20% combat, 30% sympathy boost, 50% stranger leaves
                fail_roll = random.randint(1, 100)
                if fail_roll <= 20:
                    # Combat starts!
                    is_combat = True
                    rpg_state.combat = CombatEngine.init_combat(rpg_state.party, stranger)
                    
                    prompt = f"Viết bằng tiếng Việt (dưới 90 từ) kể về việc người lạ mặt {stranger.name} bỗng giận dữ trước lời lẽ của bạn, tuốt gươm báu khai chiến!"
                    story_text = await self._generate_text_logged(
                        prompt, user_id=user_id, session_id=session_id, operation="stranger.chat_fail_combat"
                    )
                    choices = [] # Combat controls take over
                    
                elif fail_roll <= 50:
                    # Sympathy increase
                    rpg_state.sympathy += 2
                    prompt = f"Viết bằng tiếng Việt (dưới 70 từ) miêu tả người lạ mặt còn ngập ngừng nửa tin nửa ngờ câu chuyện của bạn (Hảo cảm +2). Họ chưa sẵn sàng gia nhập ngay."
                    story_text = await self._generate_text_logged(
                        prompt, user_id=user_id, session_id=session_id, operation="stranger.chat_fail_sympathy"
                    )
                    
                else:
                    # Leaves
                    rpg_state.current_event = None
                    rpg_state.current_stranger = None
                    rpg_state.past_turn_is_special = True
                    
                    prompt = f"Viết bằng tiếng Việt (dưới 80 từ) miêu tả người lạ mặt {stranger.name} từ chối khéo rồi lặng lẽ cất bước rời đi, biến mất vào làn sương rừng."
                    story_text = await self._generate_text_logged(
                        prompt, user_id=user_id, session_id=session_id, operation="stranger.chat_fail_leave"
                    )
                    ai_choices_prompt = build_rpg_turn_prompt(
                        session=session,
                        recent_messages=messages,
                        relevant_memories=[],
                        player_input="Kẻ lạ mặt rời đi",
                        rpg_state_dict=rpg_state.model_dump(),
                        event_type=None
                    )
                    raw = await self._generate_text_logged(
                        ai_choices_prompt, user_id=user_id, session_id=session_id, operation="stranger.leave.transition"
                    )
                    parsed = parse_rpg_output(raw)
                    choices = parsed["choices"]

        elif action == "Tấn công":
            is_combat = True
            rpg_state.combat = CombatEngine.init_combat(rpg_state.party, stranger)
            
            prompt = f"Viết bằng tiếng Việt (dưới 90 từ) kể về việc bạn rút vũ khí tấn công chớp nhoáng người lạ mặt {stranger.name}. Họ hoảng hốt vào tư thế tự vệ chiến đấu!"
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="stranger.attack"
            )
            choices = []

        elif action == "Tránh xung đột":
            rpg_state.current_event = None
            rpg_state.current_stranger = None
            rpg_state.past_turn_is_special = True
            
            prompt = "Viết câu chuyện bằng tiếng Việt (dưới 80 từ) người chơi bước vòng qua kẻ lạ mặt một cách cẩn trọng, né tránh phiền toái tiếp tục hành trình."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="stranger.avoid"
            )
            ai_choices_prompt = build_rpg_turn_prompt(
                session=session,
                recent_messages=messages,
                relevant_memories=[],
                player_input="Tránh xung đột với kẻ lạ",
                rpg_state_dict=rpg_state.model_dump(),
                event_type=None
            )
            raw = await self._generate_text_logged(
                ai_choices_prompt, user_id=user_id, session_id=session_id, operation="stranger.avoid.transition"
            )
            parsed = parse_rpg_output(raw)
            choices = parsed["choices"]

        session.rpg_state = rpg_state.model_dump()
        ai_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="ai",
            content=story_text,
            choices=choices
        )
        await self.store.add_message(ai_msg)
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "story": story_text,
            "choices": choices,
            "is_combat_triggered": is_combat,
            "event_type": rpg_state.current_event,
            "rpg_state": session.rpg_state,
            "message_id": ai_msg.message_id
        }

    async def process_item_action(self, session_id: str, action: str, user_id: str) -> dict[str, Any]:
        """Processes choices for the Item encounter (Collect, Ignore)."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        if rpg_state.current_event != "item":
            raise ValueError("Không ở trong sự kiện vật phẩm.")

        # Log player action as user message
        user_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=action
        )
        await self.store.add_message(user_msg)
            
        messages = await self.store.get_messages(session_id, limit=100)
        
        story_text = ""
        
        # End event flags
        rpg_state.current_event = None
        rpg_state.past_turn_is_special = True
        
        if action == "Thu thập":
            logs, inv = EventEngine.roll_item_pickup(rpg_state.inventory)
            rpg_state.inventory = inv
            
            prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả niềm vui sướng khi mở rương hoặc lục lọi tàn tích tìm thấy vàng bạc vật phẩm hữu ích. Log thu hoạch: {', '.join(logs)}"
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="item.collect"
            )
            story_text += "\n\n" + "\n".join(logs)
            
        else: # Bỏ qua
            prompt = "Viết bằng tiếng Việt (dưới 70 từ) miêu tả người chơi cảnh giác rương bẫy nên ngoảnh mặt lướt qua rương gỗ bám đầy tơ nhện dơ dáy."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="item.ignore"
            )

        ai_choices_prompt = build_rpg_turn_prompt(
            session=session,
            recent_messages=messages,
            relevant_memories=[],
            player_input=f"Sự kiện vật phẩm ({action})",
            rpg_state_dict=rpg_state.model_dump(),
            event_type=None
        )
        raw = await self._generate_text_logged(
            ai_choices_prompt, user_id=user_id, session_id=session_id, operation="item.transition"
        )
        parsed = parse_rpg_output(raw)
        choices = parsed["choices"]

        session.rpg_state = rpg_state.model_dump()
        ai_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="ai",
            content=story_text,
            choices=choices
        )
        await self.store.add_message(ai_msg)
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "story": story_text,
            "choices": choices,
            "event_type": rpg_state.current_event,
            "rpg_state": session.rpg_state,
            "message_id": ai_msg.message_id
        }

    # ==================== COMBAT ACTIONS ====================

    async def process_combat_action(self, session_id: str, request: Any, user_id: str) -> dict[str, Any]:
        """Processes one round of combat turn calculations."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        combat_state = rpg_state.combat
        if not combat_state or not combat_state.is_active:
            raise ValueError("Không ở trong trận đấu đang kích hoạt.")
            
        # Execute turn logic in combat engine
        combat_log, is_over, result = CombatEngine.process_turn(combat_state, request)
        combat_state.combat_log.extend(combat_log)
        
        # 1. Generate exciting AI description of this round
        ai_narr_prompt = build_rpg_combat_narrative_prompt(combat_log)
        ai_narrative = await self._generate_text_logged(
            ai_narr_prompt, user_id=user_id, session_id=session_id, operation="combat.round_narrative"
        )
        
        rpg_state.combat = combat_state
        
        # Handle player death or dungeon penalty if result is "lose"
        if result == "lose":
            if rpg_state.dungeon_state:
                # Dungeon defeat penalty
                rpg_state.inventory.gold = 0
                rpg_state.inventory.items = []
                for c in rpg_state.party.active:
                    c.stats.hp = 1
                for c in rpg_state.party.reserve:
                    c.stats.hp = 1
                if rpg_state.player_character:
                    rpg_state.player_character.stats.hp = 1
                    
                rpg_state.dungeon_state = None
                rpg_state.current_region = None
                rpg_state.combat = None
                rpg_state.current_event = None
                
                prompt = "Viết bằng tiếng Việt (dưới 100 từ) miêu tả tổ đội bại trận thảm hại trong hầm ngục hắc ám. Họ may mắn được dịch chuyển ra ngoài cửa hầm ngục nhưng bị cướp sạch toàn bộ vàng bạc và vật phẩm mang theo, toàn thân kiệt quệ với chỉ 1 HP."
                ai_narrative = await self._generate_text_logged(
                    prompt, user_id=user_id, session_id=session_id, operation="dungeon.defeat_story"
                )
                
                ai_msg = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="ai",
                    content=f"💀 THẤT BẠI TRONG HẦM NGỤC!\n\n{ai_narrative}",
                    choices=["Tiếp tục hành trình với 1 HP"]
                )
                await self.store.add_message(ai_msg)
                
                session.rpg_state = rpg_state.model_dump()
                await self.store.update_session(session)
                
                return {
                    "session_id": session_id,
                    "combat_log": combat_log,
                    "story": ai_msg.content,
                    "combat_state": None,
                    "is_combat_over": True,
                    "result": "lose",
                    "rpg_state": session.rpg_state
                }
            else:
                # Set player HP to 0 explicitly
                rpg_state.player_character.stats.hp = 0
                for c in rpg_state.party.active:
                    if c.is_player_character:
                        c.stats.hp = 0
                        
                rpg_state.combat = None
                rpg_state.current_event = None
                
                # Save Game Over story segment
                ai_msg = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="ai",
                    content=f"💀 GAME OVER! Bạn đã tử trận.\n\n{ai_narrative}",
                    choices=[]
                )
                await self.store.add_message(ai_msg)
                
        elif result == "win":
            # Check if Dummy was defeated
            if combat_state.enemy and combat_state.enemy.character_id == "dummy":
                rpg_state.combat = None
                if rpg_state.dummy_combat_backup:
                    rpg_state.party = rpg_state.dummy_combat_backup
                    rpg_state.dummy_combat_backup = None
                
                prompt = "Viết bằng tiếng Việt (dưới 100 từ) miêu tả tổ đội hoàn thành bài đấu tập xuất sắc với hình nộm Dummy, toàn đội thu hồi vũ khí khí giới và phục hồi trạng thái nguyên vẹn."
                ai_narrative = await self._generate_text_logged(
                    prompt, user_id=user_id, session_id=session_id, operation="combat.dummy_win"
                )
                
                ai_msg = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="ai",
                    content=f"⚔️ HOÀN THÀNH ĐẤU TẬP DUMMY!\n\n{ai_narrative}",
                    choices=[]
                )
                await self.store.add_message(ai_msg)
                
                session.rpg_state = rpg_state.model_dump()
                await self.store.update_session(session)
                
                return {
                    "session_id": session_id,
                    "combat_log": combat_log,
                    "story": ai_msg.content,
                    "combat_state": None,
                    "is_combat_over": True,
                    "result": "win",
                    "rpg_state": session.rpg_state
                }

            # Check if final boss Alpha was defeated
            elif combat_state.enemy and combat_state.enemy.name == "Alpha":
                rpg_state.combat = None
                rpg_state.current_event = None
                
                # Update achievement progress
                AchievementEngine.update_progress(rpg_state, "final_boss_defeated", 1)
                
                # Set offered event for endings
                rpg_state.offered_event = "ending_choice"
                
                prompt = "Viết bằng tiếng Việt (dưới 120 từ) miêu tả cảnh trùm cuối Alpha bị đánh bại thảm hại, thân hình khổng lồ của hắn vỡ tan thành ngàn mảnh sáng hư không. Thế giới rung chuyển, một cánh cổng ánh sáng và năng lượng hư không cổ xưa hiện ra mở ra 3 ngả đường số phận."
                ai_narrative = await self._generate_text_logged(
                    prompt, user_id=user_id, session_id=session_id, operation="combat.alpha_defeat"
                )
                
                ai_msg = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="ai",
                    content=f"👑 ALPHA ĐÃ BẠI TRẬN!\n\n{ai_narrative}",
                    choices=[
                        "Trở về thế giới thực với vinh quang cứu thế",
                        "Đồng hóa với Hư Không và trở thành Alpha tiếp theo",
                        "Từ chối kết cục, tiếp tục hành trình vô tận"
                    ]
                )
                await self.store.add_message(ai_msg)
                
                session.rpg_state = rpg_state.model_dump()
                await self.store.update_session(session)
                
                return {
                    "session_id": session_id,
                    "combat_log": combat_log,
                    "story": ai_msg.content,
                    "combat_state": None,
                    "is_combat_over": True,
                    "result": "win",
                    "rpg_state": session.rpg_state
                }
            elif combat_state.enemy and (combat_state.enemy.name in ["Medusa", "Golem", "WereWolf", "Dracula", "Vua Goblin", "Poseidon", "Diablo", "Thiên Dực Long Vương", "Ma vương Xương Cốt"] or combat_state.enemy.char_class == "Boss") and not (rpg_state.dungeon_state and rpg_state.dungeon_state.get("active")):
                # Auto loot and end combat for Bosses
                self._sync_combat_party_back(rpg_state)
                rpg_state.combat = None
                rpg_state.current_event = None
                rpg_state.current_stranger = None
                rpg_state.past_turn_is_special = True
                
                gold_gained, exp_gained, items = EventEngine.calculate_combat_drops(combat_state.enemy)
                rpg_state.inventory.gold += gold_gained
                
                exp_logs = []
                for char in rpg_state.party.active:
                    if char.stats.hp > 0:
                        lvl_logs = RPGEngine.add_exp(char, exp_gained, len(rpg_state.party.active))
                        exp_logs.extend(lvl_logs)
                
                for char in rpg_state.party.active:
                    if char.is_player_character:
                        rpg_state.player_character = char
                        
                item_names = []
                for item in items:
                    existing = next((i for i in rpg_state.inventory.items if i.name == item.name), None)
                    if existing:
                        existing.quantity += 1
                    else:
                        rpg_state.inventory.items.append(item)
                    item_names.append(f"[{item.rarity}] {item.name}")
                    
                prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả cảnh kết liễu Boss {combat_state.enemy.name} và thu nhặt toàn bộ vật phẩm quý hiếm rơi ra. Phần thưởng: +{gold_gained} Vàng, +{exp_gained} EXP."
                story_text = await self._generate_text_logged(
                    prompt, user_id=user_id, session_id=session_id, operation="combat.boss_loot"
                )
                
                drop_summary = f"\n\n🏆 ĐÃ TIÊU DIỆT BOSS {combat_state.enemy.name.upper()}!"
                drop_summary += f"\n💰 Nhận {gold_gained} vàng. (Tổng vàng: {rpg_state.inventory.gold})"
                drop_summary += f"\n📈 Toàn đội nhận +{exp_gained} EXP."
                if exp_logs:
                    drop_summary += "\n" + "\n".join(exp_logs)
                if item_names:
                    drop_summary += f"\n🎁 Vật phẩm nhặt được: {', '.join(item_names)}"
                story_text += drop_summary
                
                messages = await self.store.get_messages(session_id, limit=100)
                ai_choices_prompt = build_rpg_turn_prompt(
                    session=session,
                    recent_messages=messages,
                    relevant_memories=[],
                    player_input=f"Hạ gục Boss {combat_state.enemy.name} (loot)",
                    rpg_state_dict=rpg_state.model_dump(),
                    event_type=None
                )
                raw = await self._generate_text_logged(
                    ai_choices_prompt, user_id=user_id, session_id=session_id, operation="combat.boss.transition"
                )
                parsed = parse_rpg_output(raw)
                choices = parsed["choices"]
                
                session.rpg_state = rpg_state.model_dump()
                ai_msg = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="ai",
                    content=story_text,
                    choices=choices
                )
                await self.store.add_message(ai_msg)
                await self.store.update_session(session)
                
                return {
                    "session_id": session_id,
                    "combat_log": combat_log,
                    "story": story_text,
                    "combat_state": None,
                    "is_combat_over": True,
                    "result": "win",
                    "choices": choices,
                    "rpg_state": session.rpg_state
                }
            
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "combat_log": combat_log,
            "story": ai_narrative,
            "combat_state": combat_state.model_dump() if combat_state else None,
            "is_combat_over": is_over,
            "result": result,
            "rpg_state": session.rpg_state
        }

    def _sync_combat_party_back(self, rpg_state: RPGGameState):
        combat = rpg_state.combat
        if combat and combat.combat_party:
            for char in rpg_state.party.active:
                combat_char = next((c for c in combat.combat_party if c.character_id == char.character_id), None)
                if combat_char:
                    char.buffs = []
                    char.debuffs = []
                    char.special_skills.skill_1_countdown = 0
                    char.special_skills.skill_2_countdown = 0
                    char.special_skills.skill_1_activated = False
                    char.special_skills.skill_1_activating = False
                    char.special_skills.passive_activated = False
                    if hasattr(char.special_skills, "hoshi_passive_countdown"):
                        char.special_skills.hoshi_passive_countdown = 0
                    if hasattr(char.special_skills, "lemuen_auto_shots"):
                        char.special_skills.lemuen_auto_shots = 0
                    RPGEngine.sync_character_stats(char, len(rpg_state.party.active))
                    char.stats.hp = min(combat_char.stats.hp, char.stats.max_hp)
                    if char.is_player_character:
                        rpg_state.player_character = char

    @staticmethod
    def _trigger_supporter_rest_phase(rpg_state: RPGGameState) -> str:
        active_members = rpg_state.party.active
        supporters = [c for c in active_members if c.char_class == "Supporter" and c.stats.hp > 0]
        if not supporters:
            return "Không có Supporter nào còn sống để kích hoạt kỹ năng bị động hồi phục."
            
        race_priority = {"Angel": 1, "Elf": 2, "Royalty": 3, "Human": 4}
        supporters.sort(key=lambda c: race_priority.get(c.race, 99))
        best_supporter = supporters[0]
        
        msg = f"✨ Kỹ năng bị động của Supporter {best_supporter.name} (Tộc {best_supporter.race}) tự động kích hoạt ở Rest Phase:\n"
        
        if best_supporter.race == "Angel":
            revived = []
            for c in active_members:
                if c.stats.hp <= 0:
                    c.stats.hp = c.stats.max_hp
                    revived.append(c.name)
            if revived:
                msg += f"😇 [Angel Passive] Hồi sinh {', '.join(revived)} và hồi phục 100% HP!"
            else:
                msg += "😇 [Angel Passive] Tất cả đồng đội đều còn sống, không cần hồi sinh."
        elif best_supporter.race == "Elf":
            revived = []
            for c in active_members:
                c.debuffs = []
                if c.stats.hp <= 0:
                    c.stats.hp = int(c.stats.max_hp * 0.10)
                    revived.append(c.name)
            msg += "🧝 [Elf Passive] Giải trừ toàn bộ hiệu ứng xấu của cả đội."
            if revived:
                msg += f" Hồi sinh {', '.join(revived)} với 10% HP!"
        elif best_supporter.race == "Royalty":
            healed = []
            for c in active_members:
                c.debuffs = []
                if c.stats.hp > 0:
                    lost_hp = c.stats.max_hp - c.stats.hp
                    heal_amount = int(lost_hp * 0.20)
                    if heal_amount > 0:
                        c.stats.hp = min(c.stats.max_hp, c.stats.hp + heal_amount)
                        healed.append(f"{c.name} (+{heal_amount} HP)")
            msg += "👑 [Royalty Passive] Giải trừ toàn bộ hiệu ứng xấu của cả đội."
            if healed:
                msg += f" Hồi 20% HP đã mất cho: {', '.join(healed)}."
        elif best_supporter.race == "Human":
            injured = [c for c in active_members if c.stats.hp > 0 and c.stats.hp < c.stats.max_hp]
            if injured:
                injured.sort(key=lambda c: c.stats.max_hp - c.stats.hp, reverse=True)
                target = injured[0]
                heal_amount = target.stats.max_hp - target.stats.hp
                target.stats.hp = target.stats.max_hp
                msg += f"🧑 [Human Passive] Hồi phục 100% HP đã mất cho {target.name} (+{heal_amount} HP)!"
            else:
                msg += "🧑 [Human Passive] Không có đồng minh nào bị thương."
        return msg

    async def _process_dungeon_win(self, session: SessionState, rpg_state: RPGGameState, user_id: str) -> dict[str, Any]:
        floor = rpg_state.dungeon_state.get("floor", 1)
        
        # 1. Tính loot và exp
        gold_gained = 0
        exp_gained = 0
        items = []
        
        if floor == 1:
            gold_gained = random.randint(50, 100)
            exp_gained = random.randint(50, 100)
            num_items = random.randint(2, 4)
            for _ in range(num_items):
                rarity = "Rare" if random.random() < 0.30 else "Common"
                item = RPGEngine.generate_random_item(rarity=rarity)
                items.append(item)
        elif floor == 2:
            gold_gained = random.randint(80, 130)
            exp_gained = random.randint(80, 130)
            num_items = random.randint(2, 3)
            for _ in range(num_items):
                rarity = "Epic" if random.random() < 0.40 else "Rare"
                item = RPGEngine.generate_random_item(rarity=rarity)
                items.append(item)
        elif floor == 3:
            gold_gained = random.randint(120, 200)
            exp_gained = random.randint(120, 200)
            # Tặng mảnh khóa Mythic
            key_fragment = RPGItem(
                item_id=str(uuid.uuid4()),
                name=f"Mảnh vỡ chìa khoá vĩ đại {rpg_state.environment}",
                rarity="Mythic",
                item_type="Consumable",
                description=f"Một trong 7 mảnh khóa vĩ đại dùng để kích hoạt Cánh Cổng Hư Không khiêu chiến Alpha. Thu thập tại {rpg_state.environment}.",
                quantity=1
            )
            items.append(key_fragment)
            
        # 2. Cộng dồn vào dungeon_state
        rpg_state.dungeon_state["accumulated_gold"] += gold_gained
        rpg_state.dungeon_state["accumulated_exp"] += exp_gained
        for item in items:
            rpg_state.dungeon_state["accumulated_items"].append(item.model_dump())
            
        # 3. Sync stats back
        self._sync_combat_party_back(rpg_state)
        rpg_state.combat = None
        rpg_state.current_event = None
        
        story_text = ""
        choices = []
        
        if floor == 3:
            # Vượt dungeon thành công!
            tot_gold = rpg_state.dungeon_state["accumulated_gold"]
            tot_exp = rpg_state.dungeon_state["accumulated_exp"]
            tot_items = rpg_state.dungeon_state["accumulated_items"]
            
            rpg_state.inventory.gold += tot_gold
            
            exp_logs = []
            if tot_exp > 0 and rpg_state.party.active:
                for char in rpg_state.party.active:
                    if char.stats.hp > 0:
                        lvl_logs = RPGEngine.add_exp(char, tot_exp, len(rpg_state.party.active))
                        exp_logs.extend(lvl_logs)
            
            for char in rpg_state.party.active:
                if char.is_player_character:
                    rpg_state.player_character = char
                    
            item_names = []
            for it in tot_items:
                r_item = RPGItem.model_validate(it)
                existing = next((i for i in rpg_state.inventory.items if i.name == r_item.name), None)
                if existing:
                    existing.quantity += 1
                else:
                    rpg_state.inventory.items.append(r_item)
                item_names.append(f"[{r_item.rarity}] {r_item.name}")
                
            rpg_state.dungeon_state = None
            rpg_state.current_region = None
            
            # Update achievements
            ach_logs = AchievementEngine.update_progress(rpg_state, "elite2_defeated", 1)
            ach_logs.extend(AchievementEngine.update_progress(rpg_state, "gold_accumulated", 0))
            
            prompt = f"Viết bằng tiếng Việt (dưới 120 từ) miêu tả tổ đội hoàn thành vượt qua ải cuối cùng của hầm ngục, đánh bại Boss hung tợn và nhận được bảo vật truyền thuyết Mảnh Vỡ Chìa Khóa Vĩ Đại của vùng {rpg_state.environment}."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session.session_id, operation="dungeon.win_floor_3"
            )
            
            drop_summary = f"\n\n🏆 CHÚC MỪNG VƯỢT DUNGEON THÀNH CÔNG!"
            drop_summary += f"\n💰 Tổng vàng nhận được: +{tot_gold} Vàng. (Tổng vàng: {rpg_state.inventory.gold})"
            drop_summary += f"\n📈 Toàn đội nhận +{tot_exp} EXP."
            if exp_logs:
                drop_summary += "\n" + "\n".join(exp_logs)
            if item_names:
                drop_summary += f"\n🎁 Vật phẩm nhặt được: {', '.join(item_names)}"
            if ach_logs:
                drop_summary += "\n" + "\n".join(ach_logs)
            story_text += drop_summary
            
            choices = ["Khám phá vùng đất mới", "Khám phá ngóc ngách xung quanh", "Tiếp tục di chuyển"]
            
        else:
            # Chuyển lên tầng tiếp theo, Safe Zone
            rpg_state.dungeon_state["floor"] += 1
            rpg_state.dungeon_state["in_safe_zone"] = True
            
            # Kích hoạt Supporter
            rest_msg = self._trigger_supporter_rest_phase(rpg_state)
            
            # Update achievements
            AchievementEngine.update_progress(rpg_state, "elite1_defeated", 1)
            
            prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả tổ đội an toàn rút về một khu vực nghỉ chân tĩnh lặng (Safe Zone) sau khi vượt qua Ải {floor} của hầm ngục."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session.session_id, operation=f"dungeon.safe_zone_floor_{floor}"
            )
            story_text = f"🛡️ ĐÃ VƯỢT ẢI {floor} - AN TOÀN 🛡️\n\n" + story_text
            story_text += f"\n\n✨ {rest_msg}"
            story_text += f"\n🎁 Loot tích lũy tạm thời: +{rpg_state.dungeon_state['accumulated_gold']} vàng, {len(rpg_state.dungeon_state['accumulated_items'])} vật phẩm."
            
            choices = [
                f"Tiếp tục leo tháp (Ải {floor + 1})",
                "Rút lui khỏi hầm ngục và nhận thưởng"
            ]
            
        # Cập nhật quest
        quest_notifs = QuestEngine.update_quest_progress(rpg_state, "defeat", {"race": "", "is_boss": True, "boss_category": "Elite2" if floor == 3 else "Elite1"})
        if quest_notifs:
            story_text += "\n\n" + "\n".join(quest_notifs)
            
        rpg_state.past_turn_is_special = True
        session.rpg_state = rpg_state.model_dump()
        
        # Save output message
        ai_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session.session_id,
            role="ai",
            content=story_text,
            choices=choices
        )
        await self.store.add_message(ai_msg)
        await self.store.update_session(session)
        
        return {
            "session_id": session.session_id,
            "story": story_text,
            "choices": choices,
            "event_type": None,
            "rpg_state": session.rpg_state,
            "message_id": ai_msg.message_id
        }

    async def process_combat_end_action(self, session_id: str, action: str, user_id: str, custom_name: str | None = None) -> dict[str, Any]:
        """Resolves the victory rewards choice after winning combat against a stranger."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        # 1. Nếu đang ở trong Dungeon và thắng trận, bỏ qua stranger rewards thông thường
        if rpg_state.dungeon_state and rpg_state.dungeon_state.get("active"):
            return await self._process_dungeon_win(session, rpg_state, user_id)
            
        combat = rpg_state.combat
        
        # We need a copy of the enemy to resolve drops
        enemy = combat.enemy if combat else rpg_state.current_stranger
        if not enemy:
            raise ValueError("Không có thông tin đối thủ đã hạ gục.")
            
        # Sync stats from combat copy back to main active party characters
        if combat and combat.combat_party:
            for char in rpg_state.party.active:
                combat_char = next((c for c in combat.combat_party if c.character_id == char.character_id), None)
                if combat_char:
                    # Clear buffs and debuffs outside combat
                    char.buffs = []
                    char.debuffs = []
                    
                    # Reset skill countdowns and active flags
                    char.special_skills.skill_1_countdown = 0
                    char.special_skills.skill_2_countdown = 0
                    char.special_skills.skill_1_activated = False
                    char.special_skills.skill_1_activating = False
                    char.special_skills.passive_activated = False
                    if hasattr(char.special_skills, "hoshi_passive_countdown"):
                        char.special_skills.hoshi_passive_countdown = 0
                    if hasattr(char.special_skills, "lemuen_auto_shots"):
                        char.special_skills.lemuen_auto_shots = 0
                    
                    # Recalculate original stats (restoring Max HP and DEF of Hoshiguma)
                    RPGEngine.sync_character_stats(char, len(rpg_state.party.active))
                    
                    # Keep HP but cap at original max HP
                    char.stats.hp = min(combat_char.stats.hp, char.stats.max_hp)
                    
                    if char.is_player_character:
                        rpg_state.player_character = char
            
        messages = await self.store.get_messages(session_id, limit=100)
        story_text = ""
        choices = []
        
        # End combat / stranger event
        rpg_state.combat = None
        rpg_state.current_event = None
        rpg_state.current_stranger = None
        rpg_state.past_turn_is_special = True
        
        if action == "loot": # Kết liễu
            gold_gained, exp_gained, items = EventEngine.calculate_combat_drops(enemy)
            rpg_state.inventory.gold += gold_gained
            
            # EXP distribution
            exp_logs = []
            for char in rpg_state.party.active:
                if char.stats.hp > 0:
                    lvl_logs = RPGEngine.add_exp(char, exp_gained, len(rpg_state.party.active))
                    exp_logs.extend(lvl_logs)
                    
            # Update player main profile
            for char in rpg_state.party.active:
                if char.is_player_character:
                    rpg_state.player_character = char
                    
            item_names = []
            for item in items:
                existing = next((i for i in rpg_state.inventory.items if i.name == item.name), None)
                if existing:
                    existing.quantity += 1
                else:
                    rpg_state.inventory.items.append(item)
                item_names.append(f"[{item.rarity}] {item.name}")
                
            prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả cảnh kết liễu kẻ địch {enemy.name} và thu nhặt toàn bộ vật phẩm rơi ra. Phần thưởng: +{gold_gained} Vàng, +{exp_gained} EXP."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="combat.end.loot"
            )
            
            # Format logs
            drop_summary = f"\n\n💰 Nhận {gold_gained} vàng. (Tổng vàng: {rpg_state.inventory.gold})"
            drop_summary += f"\n📈 Toàn đội nhận +{exp_gained} EXP."
            if exp_logs:
                drop_summary += "\n" + "\n".join(exp_logs)
            if item_names:
                drop_summary += f"\n🎁 Vật phẩm nhặt được: {', '.join(item_names)}"
            story_text += drop_summary
            
        elif action == "recruit": # Thu phục
            roll = random.randint(1, 100)
            if roll <= 80: # 80% recruit success
                total_party = len(rpg_state.party.active) + len(rpg_state.party.reserve)
                if total_party < 9:
                    if custom_name and enemy.rarity != "Mythic":
                        enemy.name = custom_name.strip()
                    # Revive them with 10% hp
                    enemy.stats.hp = int(enemy.stats.max_hp * 0.10)
                    enemy.debuffs = []
                    enemy.buffs = []
                    
                    if len(rpg_state.party.active) < 4:
                        rpg_state.party.active.append(enemy)
                        # Recalculate stats
                        for c in rpg_state.party.active:
                            RPGEngine.sync_character_stats(c, len(rpg_state.party.active))
                        joined_msg = "đội hình chính thức"
                    else:
                        rpg_state.party.reserve.append(enemy)
                        RPGEngine.sync_character_stats(enemy, 1)
                        joined_msg = "đội hình dự bị"
                        
                    prompt = f"Viết bằng tiếng Việt (dưới 90 từ) miêu tả cảnh người chơi đưa tay kéo {enemy.name} dậy, tha thứ cho đụng độ và trao họ lòng tin gia nhập đội."
                    story_text = await self._generate_text_logged(
                        prompt, user_id=user_id, session_id=session_id, operation="combat.end.recruit_success"
                    )
                    story_text += f"\n\n👥 {enemy.name} đã thề trung thành và gia nhập {joined_msg}!"
                else:
                    prompt = f"Viết bằng tiếng Việt (dưới 90 từ) miêu tả {enemy.name} chịu thua muốn quy phục nhưng đội hình đầy nên họ biếu vàng lộ phí xin tha mạng."
                    story_text = await self._generate_text_logged(
                        prompt, user_id=user_id, session_id=session_id, operation="combat.end.recruit_full"
                    )
                    rpg_state.inventory.gold += 80
                    story_text += "\n\n💰 Nhận thêm 80 vàng lộ phí xin tha mạng!"
            else:
                prompt = f"Viết bằng tiếng Việt (dưới 90 từ) miêu tả cảnh {enemy.name} nhổ bọt từ chối quy phục, bất ngờ quăng bom khói tẩu thoát vào bóng đêm."
                story_text = await self._generate_text_logged(
                    prompt, user_id=user_id, session_id=session_id, operation="combat.end.recruit_fail"
                )
                story_text += f"\n\n💨 {enemy.name} đã trốn thoát thành công!"
                
        elif action == "leave": # Tha bổng
            exp_gained = 40
            exp_logs = []
            for char in rpg_state.party.active:
                if char.stats.hp > 0:
                    lvl_logs = RPGEngine.add_exp(char, exp_gained, len(rpg_state.party.active))
                    exp_logs.extend(lvl_logs)
            
            # Sync player stats
            for char in rpg_state.party.active:
                if char.is_player_character:
                    rpg_state.player_character = char
                    
            prompt = f"Viết bằng tiếng Việt (dưới 90 từ) miêu tả người chơi cất vũ khí, tha thứ thả đối thủ rời đi. Kẻ địch cảm tạ và biến mất."
            story_text = await self._generate_text_logged(
                prompt, user_id=user_id, session_id=session_id, operation="combat.end.leave"
            )
            
            drop_summary = f"\n\n📈 Toàn đội nhận +{exp_gained} EXP triết lý."
            if exp_logs:
                drop_summary += "\n" + "\n".join(exp_logs)
            story_text += drop_summary

        # Reset active party HP to full for combat members when returning to story mode?
        # No, dynamic HP must remain! We restore combat state copies to main state.
        for char in rpg_state.party.active:
            if char.is_player_character:
                rpg_state.player_character = char
        
        # Roll standard transitions
        ai_choices_prompt = build_rpg_turn_prompt(
            session=session,
            recent_messages=messages,
            relevant_memories=[],
            player_input=f"Kết thúc chiến đấu ({action})",
            rpg_state_dict=rpg_state.model_dump(),
            event_type=None
        )
        raw = await self._generate_text_logged(
            ai_choices_prompt, user_id=user_id, session_id=session_id, operation="combat.end.transition"
        )
        parsed = parse_rpg_output(raw)
        choices = parsed["choices"]

        session.rpg_state = rpg_state.model_dump()
        ai_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="ai",
            content=story_text,
            choices=choices
        )
        await self.store.add_message(ai_msg)
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "story": story_text,
            "choices": choices,
            "rpg_state": session.rpg_state,
            "message_id": ai_msg.message_id
        }

    # ==================== SHOP ACTIONS ====================

    async def process_shop_refresh(self, session_id: str, user_id: str) -> dict[str, Any]:
        """Refreshes shop inventory slots costing 5 gold."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        if rpg_state.inventory.gold < 5:
            raise ValueError("Không đủ vàng (Cần 5 vàng để refresh shop).")
            
        rpg_state.inventory.gold -= 5
        
        # Re-roll stock
        items, mercs = ShopEngine.generate_shop_stock(rpg_state.shop.level, rpg_state.player_character.level)
        rpg_state.shop.items_for_sale = items
        rpg_state.shop.mercenaries_for_sale = mercs
        
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "shop": rpg_state.shop.model_dump(),
            "inventory": rpg_state.inventory.model_dump(),
            "message": "Đã làm mới quầy hàng hết 5 vàng.",
            "rpg_state": session.rpg_state
        }

    async def process_shop_upgrade(self, session_id: str, user_id: str) -> dict[str, Any]:
        """Upgrades the shop to the next level."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        success, msg, shop, inv = ShopEngine.upgrade_shop(rpg_state.shop, rpg_state.inventory)
        if not success:
            raise ValueError(msg)
            
        rpg_state.shop = shop
        rpg_state.inventory = inv
        
        # Regenerate stock for new level
        items, mercs = ShopEngine.generate_shop_stock(rpg_state.shop.level, rpg_state.player_character.level)
        rpg_state.shop.items_for_sale = items
        rpg_state.shop.mercenaries_for_sale = mercs
        
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "shop": rpg_state.shop.model_dump(),
            "inventory": rpg_state.inventory.model_dump(),
            "message": msg,
            "rpg_state": session.rpg_state
        }

    async def process_shop_buy_item(self, session_id: str, item_index: int, user_id: str) -> dict[str, Any]:
        """Buys a shop item."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        success, msg, shop, inv = ShopEngine.buy_item(rpg_state.shop, rpg_state.inventory, item_index)
        if not success:
            raise ValueError(msg)
            
        rpg_state.shop = shop
        rpg_state.inventory = inv
        
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "shop": rpg_state.shop.model_dump(),
            "inventory": rpg_state.inventory.model_dump(),
            "message": msg,
            "rpg_state": session.rpg_state
        }

    async def process_shop_buy_merc(self, session_id: str, merc_index: int, user_id: str, custom_name: str | None = None) -> dict[str, Any]:
        """Hires a shop mercenary."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        # Rename mercenary before buying if custom name is provided
        if merc_index >= 0 and merc_index < len(rpg_state.shop.mercenaries_for_sale):
            merc_to_buy = rpg_state.shop.mercenaries_for_sale[merc_index]
            if custom_name and merc_to_buy.rarity != "Mythic":
                merc_to_buy.name = custom_name.strip()
                
        success, msg, shop, party, inv = ShopEngine.buy_mercenary(
            rpg_state.shop, rpg_state.party, rpg_state.inventory, merc_index
        )
        if not success:
            raise ValueError(msg)
            
        rpg_state.shop = shop
        rpg_state.party = party
        rpg_state.inventory = inv
        
        # Update recruitment quest progress
        bought_merc = party.active[-1] if len(party.active) > len(rpg_state.party.active) else (party.reserve[-1] if len(party.reserve) > len(rpg_state.party.reserve) else None)
        if bought_merc:
            self.copy_character_avatar(session_id, bought_merc)
            QuestEngine.update_quest_progress(rpg_state, "recruit", {"race": bought_merc.race})
            
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "shop": rpg_state.shop.model_dump(),
            "inventory": rpg_state.inventory.model_dump(),
            "message": msg,
            "rpg_state": session.rpg_state
        }

    async def process_shop_sell_item(self, session_id: str, item_id: str, user_id: str) -> dict[str, Any]:
        """Sells an inventory item."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        # Verify item not currently equipped on anyone
        for char in rpg_state.party.active + rpg_state.party.reserve:
            if (char.equipment.weapon and char.equipment.weapon.item_id == item_id) or \
               (char.equipment.armor and char.equipment.armor.item_id == item_id):
                raise ValueError("Không thể bán vật phẩm đang trang bị trên người nhân vật.")
                
        success, msg, inv = ShopEngine.sell_item(rpg_state.inventory, item_id)
        if not success:
            raise ValueError(msg)
            
        rpg_state.inventory = inv
        
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "shop": rpg_state.shop.model_dump(),
            "inventory": rpg_state.inventory.model_dump(),
            "message": msg,
            "rpg_state": session.rpg_state
        }

    # ==================== PARTY MANAGEMENT ====================

    async def swap_party_members(self, session_id: str, from_pos: str, to_pos: str, user_id: str) -> dict[str, Any]:
        """Swaps active and reserve party characters."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        party = rpg_state.party
        
        # Parse tags like "active_0" or "reserve_2"
        f_type, f_idx_str = from_pos.split("_")
        t_type, t_idx_str = to_pos.split("_")
        f_idx = int(f_idx_str)
        t_idx = int(t_idx_str)
        
        # Fetch targets
        from_list = party.active if f_type == "active" else party.reserve
        to_list = party.active if t_type == "active" else party.reserve
        
        if f_idx < 0 or f_idx >= len(from_list):
            raise ValueError(f"Vị trí nguồn {from_pos} không hợp lệ.")
            
        char_from = from_list[f_idx]
        
        if t_idx < 0 or t_idx > len(to_list):
            raise ValueError(f"Vị trí đích {to_pos} không hợp lệ.")
            
        if t_idx == len(to_list):
            # Move to end of list (append)
            # Verify capacity limits
            if t_type == "active" and len(party.active) >= 4:
                raise ValueError("Đội hình chính thức đã đầy (Tối đa 4 người).")
            if t_type == "reserve" and len(party.reserve) >= 5:
                raise ValueError("Đội hình dự bị đã đầy (Tối đa 5 người).")
                
            from_list.pop(f_idx)
            to_list.append(char_from)
        else:
            # Swap
            char_to = to_list[t_idx]
            from_list[f_idx] = char_to
            to_list[t_idx] = char_from
            
        # Ensure player character cannot be moved out of active party?
        # Standard: player character is always active, but we can let them swap. Let's make sure player character is not lost.
        has_player = any(c.is_player_character for c in party.active)
        if not has_player:
            # Rollback by raising error
            raise ValueError("Không thể chuyển nhân vật chính khỏi Đội hình chính thức!")
            
        # Re-sync stats for all active party members (as active party size changes, VinaVictoria passive shifts)
        for char in party.active:
            RPGEngine.sync_character_stats(char, len(party.active))
        for char in party.reserve:
            RPGEngine.sync_character_stats(char, 1)
            
        rpg_state.party = party
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "party": rpg_state.party.model_dump(),
            "message": "Thay đổi vị trí đội hình thành công!"
        }

    async def equip_item(self, session_id: str, character_id: str, item_id: str, user_id: str) -> dict[str, Any]:
        """Equips an item onto a character."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        # 1. Fetch item from inventory
        item = next((i for i in rpg_state.inventory.items if i.item_id == item_id), None)
        if not item:
            raise ValueError("Không tìm thấy vật phẩm này trong hành trang.")
            
        if item.item_type not in ["Weapon", "Armor"]:
            raise ValueError("Vật phẩm tiêu hao không thể trang bị.")
            
        # 2. Fetch character from party
        char = next((c for c in rpg_state.party.active + rpg_state.party.reserve if c.character_id == character_id), None)
        if not char:
            raise ValueError("Không tìm thấy nhân vật.")
            
        # Specialist can equip everything.
        # Other classes have weapon/armor compatibility checks if we want, but let's allow general equips as per prompt catalog.
        
        # Swap existing equipment back to inventory
        old_item = None
        if item.item_type == "Weapon":
            old_item = char.equipment.weapon
            char.equipment.weapon = item
        else:
            old_item = char.equipment.armor
            char.equipment.armor = item
            
        # Remove item from inventory
        if item.quantity > 1:
            item.quantity -= 1
        else:
            rpg_state.inventory.items.remove(item)
            
        # Put old item back in inventory
        if old_item:
            existing = next((i for i in rpg_state.inventory.items if i.name == old_item.name), None)
            if existing:
                existing.quantity += 1
            else:
                # Reset quantity/id to avoid duplicate issues
                old_item.item_id = str(uuid.uuid4())[:8]
                old_item.quantity = 1
                rpg_state.inventory.items.append(old_item)
                
        # Re-calculate stats
        RPGEngine.sync_character_stats(char, len(rpg_state.party.active))
        
        # If character is player, update main profile
        if char.is_player_character:
            rpg_state.player_character = char
            
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "party": rpg_state.party.model_dump(),
            "inventory": rpg_state.inventory.model_dump(),
            "message": f"Đã trang bị {item.name} cho {char.name}."
        }

    async def unequip_item(self, session_id: str, character_id: str, slot: str, user_id: str) -> dict[str, Any]:
        """Unequips an item from a character slot back to inventory."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        char = next((c for c in rpg_state.party.active + rpg_state.party.reserve if c.character_id == character_id), None)
        if not char:
            raise ValueError("Không tìm thấy nhân vật.")
            
        item = getattr(char.equipment, slot.lower())
        if not item:
            raise ValueError(f"Không có trang bị nào ở ô {slot} để tháo.")
            
        # Remove from equipment
        setattr(char.equipment, slot.lower(), None)
        
        # Add back to inventory
        existing = next((i for i in rpg_state.inventory.items if i.name == item.name), None)
        if existing:
            existing.quantity += 1
        else:
            item.item_id = str(uuid.uuid4())[:8]
            item.quantity = 1
            rpg_state.inventory.items.append(item)
            
        RPGEngine.sync_character_stats(char, len(rpg_state.party.active))
        if char.is_player_character:
            rpg_state.player_character = char
            
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "party": rpg_state.party.model_dump(),
            "inventory": rpg_state.inventory.model_dump(),
            "message": f"Đã tháo trang bị {item.name} của {char.name}."
        }

    async def use_consume_item(self, session_id: str, character_id: str, item_id: str, user_id: str) -> dict[str, Any]:
        """Uses a consumable item (e.g. food/holy water/revives) from inventory on a character."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        # 1. Fetch item
        item = next((i for i in rpg_state.inventory.items if i.item_id == item_id), None)
        if not item or item.item_type not in ["Consume", "Consumable"]:
            raise ValueError("Không tìm thấy vật phẩm tiêu hao hợp lệ.")
            
        # Check special items (Fragments and Void Key)
        if item.name.startswith("Bản đồ cổ") or item.name == "Bản đồ khu vực":
            env = rpg_state.environment
            # Try to extract environment from name (e.g. "Bản đồ cổ Rừng rậm" -> "Rừng rậm")
            possible_env = item.name.replace("Bản đồ cổ", "").strip()
            if possible_env in REGION_CATALOG:
                env = possible_env
                
            catalog = REGION_CATALOG.get(env, {})
            major_loc = catalog.get("major")
            if not major_loc:
                raise ValueError(f"Không tìm thấy kiến trúc lớn ở môi trường {env}.")
                
            msg_unlocked = ""
            if major_loc not in rpg_state.unlocked_fast_travel:
                rpg_state.unlocked_fast_travel.append(major_loc)
                msg_unlocked += f" mở khóa dịch chuyển nhanh đến [{major_loc}]"
            if major_loc not in rpg_state.explored_regions:
                rpg_state.explored_regions.append(major_loc)
                
            if not msg_unlocked:
                msg = f"Bạn đã khám phá [{major_loc}] từ trước rồi, bản đồ này không giúp ích thêm."
            else:
                msg = f"🗺️ SỬ DỤNG BẢN ĐỒ CỔ: Bản đồ đã ghi nhận và{msg_unlocked}."
                
            # Consume item
            if item.quantity > 1:
                item.quantity -= 1
            else:
                rpg_state.inventory.items.remove(item)
                
            session.rpg_state = rpg_state.model_dump()
            await self.store.update_session(session)
            
            return {
                "session_id": session_id,
                "party": rpg_state.party.model_dump(),
                "inventory": rpg_state.inventory.model_dump(),
                "message": msg,
                "rpg_state": session.rpg_state
            }

        elif item.name.startswith("Mảnh vỡ chìa khoá vĩ đại ") or item.name == "Chìa khoá Hư Không vĩ đại":
            msg = ""
            if item.name.startswith("Mảnh vỡ chìa khoá vĩ đại "):
                # Check for all 7 key fragments
                fragments = [i for i in rpg_state.inventory.items if i.name.startswith("Mảnh vỡ chìa khoá vĩ đại ")]
                unique_envs = {f.name.replace("Mảnh vỡ chìa khoá vĩ đại ", "").strip() for f in fragments}
                ENVIRONMENTS = {"Đồng bằng", "Đồi núi", "Rừng rậm", "Núi lửa", "Hoang mạc", "Núi tuyết", "Thiên giới"}
                
                if len(unique_envs) >= 7:
                    # Combine and forge Void Key
                    for env in ENVIRONMENTS:
                        frag_name = f"Mảnh vỡ chìa khoá vĩ đại {env}"
                        item_to_rem = next((i for i in rpg_state.inventory.items if i.name == frag_name), None)
                        if item_to_rem:
                            if item_to_rem.quantity > 1:
                                item_to_rem.quantity -= 1
                            else:
                                rpg_state.inventory.items.remove(item_to_rem)
                                
                    # Create void key
                    void_key = RPGItem(
                        item_id=str(uuid.uuid4()),
                        name="Chìa khoá Hư Không vĩ đại",
                        rarity="Mythic",
                        item_type="Consumable",
                        description="Chiếc chìa khóa chứa đựng năng lượng hư không cực hạn. Sử dụng để kích hoạt Cánh Cổng Hư Không diện kiến trùm cuối Alpha.",
                        quantity=1
                    )
                    rpg_state.inventory.items.append(void_key)
                    msg = "🔮 RÈN THÀNH CÔNG! Bạn đã kết hợp 7 mảnh vỡ chìa khóa của 7 vùng đất lớn để rèn nên [Chìa khoá Hư Không vĩ đại]!"
                else:
                    missing = ENVIRONMENTS - unique_envs
                    raise ValueError(f"Chưa thu thập đủ 7 mảnh khóa! Bạn còn thiếu mảnh khóa ở: {', '.join(missing)}")
            else:
                # Use Void Key -> Start Alpha combat
                alpha = RPGCharacter(
                    character_id=str(uuid.uuid4()),
                    name="Alpha",
                    rarity="Mythic",
                    race="Bí ẩn",
                    char_class="Bí ẩn",
                    level=50,
                    gender="Male",
                    exp=0,
                    buffs=[],
                    debuffs=[]
                )
                alpha.stats.max_hp = 2000
                alpha.stats.hp = 2000
                alpha.stats.atk = 200
                alpha.stats.defense = 90
                alpha.stats.res = 160
                alpha.stats.res_def = 50
                alpha.stats.atk_spd = 120
                alpha.base_stats = alpha.stats.model_copy()
                
                rpg_state.combat = RPGCombatState(
                    cb_turn_count=0,
                    combat_party=[c.model_copy() for c in rpg_state.party.active],
                    enemy=alpha,
                    combat_log=[],
                    is_active=True
                )
                rpg_state.current_event = None
                rpg_state.current_region = "Cánh Cổng Hư Không"
                
                # Consume key
                if item.quantity > 1:
                    item.quantity -= 1
                else:
                    rpg_state.inventory.items.remove(item)
                    
                msg = "🌌 CÁNH CỔNG HƯ KHÔNG MỞ RA! Sức mạnh thần bí hút lấy toàn đội của bạn. Trùm cuối ALPHA xuất thế!"
                
            session.rpg_state = rpg_state.model_dump()
            await self.store.update_session(session)
            
            return {
                "session_id": session_id,
                "party": rpg_state.party.model_dump(),
                "inventory": rpg_state.inventory.model_dump(),
                "message": msg,
                "rpg_state": session.rpg_state
            }

        # 2. Fetch target
        char = next((c for c in rpg_state.party.active + rpg_state.party.reserve if c.character_id == character_id), None)
        if not char:
            raise ValueError("Không tìm thấy nhân vật mục tiêu.")
            
        msg = ""
        # 3. Apply item effect
        if item.name == "Hiệu triệu": # Revives with 100% HP
            if char.stats.hp > 0:
                raise ValueError(f"{char.name} vẫn còn sống, không cần hồi sinh.")
            char.stats.hp = char.stats.max_hp
            msg = f"Hồi sinh thần kỳ! {char.name} đã trở lại chiến đấu với 100% HP."
            
        elif item.name == "Thiết triệu": # Revives with 5% HP
            if char.stats.hp > 0:
                raise ValueError(f"{char.name} vẫn còn sống, không cần hồi sinh.")
            char.stats.hp = max(1, int(char.stats.max_hp * 0.05))
            msg = f"{char.name} đã được hồi sinh với 5% HP ({char.stats.hp}/{char.stats.max_hp})."
            
        else:
            # Healing/curing items require character to be alive
            if char.stats.hp <= 0:
                raise ValueError(f"Không thể sử dụng vật phẩm phục hồi lên nhân vật đã tử trận. Hãy dùng vật phẩm Hồi sinh.")
                
            if item.name == "Bình nước thánh": # 70% Max HP heal + clear debuffs
                char.stats.hp = min(char.stats.max_hp, char.stats.hp + int(char.stats.max_hp * 0.70))
                char.debuffs = []
                msg = f"Dùng Nước Thánh: {char.name} hồi 70% HP và xóa sạch hiệu ứng bất lợi!"
                
            elif item.name == "Băng gạt": # Removes Bleed + heals 30% Max HP
                char.stats.hp = min(char.stats.max_hp, char.stats.hp + int(char.stats.max_hp * 0.30))
                char.debuffs = [d for d in char.debuffs if d.name != "Chảy máu"]
                msg = f"Dùng Băng Gạt: {char.name} cầm máu thành công và hồi 30% HP."
                
            elif item.name == "Thịt thú nướng": # Heals 30% Max HP
                char.stats.hp = min(char.stats.max_hp, char.stats.hp + int(char.stats.max_hp * 0.30))
                msg = f"Dùng Thịt Nướng: {char.name} thưởng thức đồ ngon, hồi 30% HP."
                
            elif item.name == "Mẫu bánh mì": # Heals 20% Max HP
                char.stats.hp = min(char.stats.max_hp, char.stats.hp + int(char.stats.max_hp * 0.20))
                msg = f"Dùng Mẫu Bánh Mì: {char.name} hồi phục 20% HP."

        # Remove quantity
        if item.quantity > 1:
            item.quantity -= 1
        else:
            rpg_state.inventory.items.remove(item)
            
        RPGEngine.sync_character_stats(char, len(rpg_state.party.active))
        if char.is_player_character:
            rpg_state.player_character = char
            
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "party": rpg_state.party.model_dump(),
            "inventory": rpg_state.inventory.model_dump(),
            "message": msg,
            "rpg_state": session.rpg_state
        }

    async def get_game_state(self, session_id: str, user_id: str) -> dict[str, Any]:
        """Returns the full parsed state dict."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
        return session.rpg_state

    async def generate_world_image(self, session_id: str, user_id: str) -> dict[str, Any]:
        """Generates a landscape image of the current turn's world environment."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        # Get last story narrative to build prompt
        messages = await self.store.get_messages(session_id, limit=100)
        last_msg = next((m for m in reversed(messages) if m.role == "ai"), None)
        
        env = rpg_state.environment or ""
        reg = rpg_state.current_region or ""
        if not reg and rpg_state.offered_event:
            if rpg_state.offered_event.startswith("region:"):
                reg = rpg_state.offered_event.split(":", 1)[1]
            elif rpg_state.offered_event.startswith("dungeon:"):
                reg = rpg_state.offered_event.split(":", 1)[1]
                
        desc = last_msg.content if last_msg and last_msg.content else ""
        prompt = f"Fantasy world landscape. Environment terrain: {env}. Specific location: {reg if reg else 'Wildlands'}. Scenic details description: {desc}"
            
        settings = get_settings()
        url = f"{settings.kaggle_backend_url.rstrip('/')}/generate-world-theme"
        
        payload = {
            "prompt": prompt,
            "world_name": f"{session_id}_see_the_world",
            "summarize_model": "gemini-2.5-flash",
            "txt2img_model": "SDXL lightning",
            "step": 4
        }
        
        try:
            res = await call_kaggle_api(url, payload)
            if res.get("status") == "success" and "image_base64" in res:
                dest_filename = f"{session_id}_see_the_world.png"
                saved_path = save_base64_image(res["image_base64"], dest_filename)
                return {
                    "success": True,
                    "image_url": saved_path,
                    "en_prompt": res.get("en_prompt", "")
                }
            else:
                raise ValueError("Kaggle backend không trả về ảnh hợp lệ.")
        except Exception as e:
            raise ValueError(f"Không thể kết nối đến Kaggle server: {e}")

    async def refresh_character_image(self, session_id: str, character_id: str, user_id: str) -> dict[str, Any]:
        """Generates or regenerates an avatar image for a character."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        char = None
        filename = None
        prompt = None
        
        # 1. Check special IDs (Monk, Merchant) or lookup in state
        if character_id == "monk" or character_id.startswith("monk_"):
            if rpg_state.current_monk and rpg_state.current_monk.character_id == character_id:
                char = rpg_state.current_monk
            elif rpg_state.current_monk and character_id == "monk":
                char = rpg_state.current_monk
                
            if char:
                filename = f"{char.character_id}.png"
                prompt = f"A serene holy monk character in a fantasy RPG, gender: {char.gender}, race: {char.race}, sitting in a peaceful temple background, wearing humble golden and white robes, glowing aura, fantasy concept art, highly detailed"
            else:
                filename = "monk.png"
                prompt = "A serene holy monk character in a fantasy RPG, sitting in a peaceful temple background, wearing humble golden and white robes, glowing aura, fantasy concept art, highly detailed"
        elif character_id == "merchant" or character_id.startswith("merchant_"):
            if rpg_state.current_merchant and rpg_state.current_merchant.character_id == character_id:
                char = rpg_state.current_merchant
            elif rpg_state.current_merchant and character_id == "merchant":
                char = rpg_state.current_merchant
                
            if char:
                filename = f"{char.character_id}.png"
                prompt = f"A friendly merchant character in a fantasy RPG, gender: {char.gender}, race: {char.race}, holding bags of coins, traveling wooden cart in the background filled with potions and armor, fantasy concept art, highly detailed"
            else:
                filename = "merchant.png"
                prompt = "A friendly merchant character in a fantasy RPG, holding bags of coins, traveling wooden cart in the background filled with potions and armor, fantasy concept art, highly detailed"
        else:
            # Active party
            for c in rpg_state.party.active:
                if c.character_id == character_id:
                    char = c
                    break
            # Reserve party
            if not char:
                for c in rpg_state.party.reserve:
                    if c.character_id == character_id:
                        char = c
                        break
            # Stranger event
            if not char and rpg_state.current_event == "stranger" and rpg_state.current_stranger and rpg_state.current_stranger.character_id == character_id:
                char = rpg_state.current_stranger
            # Combat enemy
            if not char and rpg_state.combat and rpg_state.combat.is_active and rpg_state.combat.enemy and rpg_state.combat.enemy.character_id == character_id:
                char = rpg_state.combat.enemy
                
            if not char:
                raise ValueError("Không tìm thấy nhân vật tương ứng.")
                
            name_lower = char.name.lower()
            if "hoshiguma" in name_lower:
                filename = "Hoshiguma_the_breacher.png"
                prompt = "A Valkyrie Guard, Defender, long green hair, single prominent forehead horn, wearing white and black kimono/garb, carrying a katana and a massive triangular shield, fantasy concept art, anime style, highly detailed"
            elif "vinavictoria" in name_lower or "vina victoria" in name_lower or "vina_victoria" in name_lower:
                filename = "VinaVictoria.png"
                prompt = "A lioness, Feline imperial queen, golden mane hair, heavy dark knight armor, holding a long sword and a blue royal orb, fantasy concept art, anime style, highly detailed"
            elif "wang" in name_lower:
                filename = "Wang.png"
                prompt = "A dragon race man, black and white hair, dragon horns, long tail, black robe/kimono, holding a small pet, surrounded by a white spirit dragon, fantasy concept art, anime style, highly detailed"
            elif "lemuen" in name_lower or "lumuen" in name_lower:
                filename = "Lemuen.png"
                prompt = "An angel race girl, pink hair, halo above head, sitting in a white wheelchair, giant sniper rifle, black leather jacket, delicate features, fantasy concept art, anime style, highly detailed"
            elif "medusa" in name_lower:
                filename = "Medusa.png"
                prompt = "Medusa, seductive yet deadly gorgon queen, voluptuous dark fantasy beauty, luminous pale skin dusted with iridescent green scales, long flowing hair of living serpents with forked tongues and golden eyes, piercing cat-slit yellow eyes with a deadly petrifying glow, sheer dark silk draped over serpentine lower body, standing in a torchlit underground temple with stone statues of fallen warriors around her, dramatic chiaroscuro lighting, 8k fantasy concept art, oil painting style, highly detailed"
            elif "vua goblin" in name_lower or "goblin king" in name_lower:
                filename = "Goblin_King.png"
                prompt = "Goblin King, colossal grotesque goblin warlord towering over cowering goblin minions, massive warped body covered in battle scars and tribal tattoos, crowned with a crude iron crown adorned with stolen gems, wielding a colossal bone club wrapped in barbed chains, seated on a throne built from skulls and broken weapons in a vast torchlit cavern, menacing red glowing eyes, dramatic rim lighting, dark fantasy concept art, ultra detailed, 8k"
            elif "werewolf" in name_lower:
                filename = "Werewolf.png"
                prompt = "WereWolf, massive terrifying werewolf mid-transformation, enormous muscular humanoid wolf form, thick matted dark fur with glowing crimson eyes, razor-sharp claws dripping fresh blood, head tilted back in a thunderous howl at a full moon breaking through storm clouds, standing in a dense foggy forest with shattered trees around, moonlight casting long dramatic shadows, dark fantasy, ultra detailed fur texture, dynamic action pose, 8k concept art"
            elif "dracula" in name_lower:
                filename = "Dracula.png"
                prompt = "Count Dracula, ancient vampire lord with aristocratic elegance and supernatural menace, sharp refined features with chalk-white skin and prominent fangs, glowing crimson eyes with hypnotic intensity, dressed in a floor-length high-collared velvet cape of deep crimson and midnight black, one hand holding an ornate chalice of dark red blood, standing at the center of a grand gothic castle hall with moonlight streaming through stained glass windows, dramatic theatrical lighting, baroque dark fantasy concept art, highly detailed, 8k"
            elif "golem" in name_lower:
                filename = "Golem.png"
                prompt = "Stone Golem, colossal ancient construct assembled from massive granite boulders and obsidian plates, towering 10 meters tall, body covered in carved glowing blue arcane runes that pulse with magical energy, massive craggy fists raised in combat stance, cracks across its surface revealing molten energy core within, standing amidst crumbled ancient ruins with a destroyed stone floor around it, low dramatic lighting from rune glow, thick dust and debris in the air, dark fantasy concept art, ultra detailed, 8k"
            elif "poseidon" in name_lower:
                filename = "Poseidon.png"
                prompt = "Poseidon, god of the sea, colossal divine figure rising from a massive ocean storm, muscular body of deep blue-toned divine skin, long flowing white hair and beard swirling in supernatural winds, crowned with coral and pearl diadem, wielding an enormous golden trident crackling with blue-white lightning, massive ocean waves crashing around him, ship wreckage visible in the churning waters below, dramatic storm sky with bolts of lightning, epic divine fantasy concept art, ultra detailed, 8k"
            elif "diablo" in name_lower:
                filename = "Diablo.png"
                prompt = "Diablo, supreme demon lord, colossal red-skinned demonic titan standing 15 meters tall, enormous curved black horns sweeping back from a crowned skull-like head, muscular body covered in cracked obsidian skin with rivers of lava flowing through the cracks, wielding a massive flaming chain whip and a sword of pure hellfire, surrounded by volcanic eruptions and rivers of molten lava in a hellish underworld landscape, bodies of defeated warriors littering the ground, scorching hellfire atmosphere, dramatic bottom-lit infernal glow, epic dark fantasy concept art, ultra detailed, 8k"
            elif "thiên dực long vương" in name_lower or "dragon king" in name_lower:
                filename = "Dragon_King.png"
                prompt = "Heavenly Winged Dragon King, majestic celestial dragon deity in semi-humanoid form, long serpentine body with glistening silver and white scales that shimmer like starlight, six enormous feathered wings spanning vast distances, each feather tipped with golden light, noble dragon head with a crown of crystalline horns, radiating divine golden energy aura, soaring majestically above a sea of clouds with lightning arcing around it, sunrise light breaking through clouds behind, heavenly celestial atmosphere, ultra detailed fantasy concept art, 8k"
            elif "ma vương xương cốt" in name_lower or "bone king" in name_lower:
                filename = "Bone_King.png"
                prompt = "Bone Demon King, terrifying undead overlord skeleton warlord, towering skeletal frame clad in dark ornate battle armor engraved with death runes, pauldrons shaped like screaming skulls, glowing toxic green flames burning in eye sockets, wielding an enormous pitch-black greatsword wreathed in death energy, seated on a monumental throne constructed entirely from skulls and bones, surrounded by an army of undead soldiers, eerie green spectral mist filling the vast dark throne room, dramatic underlighting from the death flames, dark necromantic fantasy concept art, ultra detailed, 8k"
            elif "alpha" in name_lower:
                filename = "Alpha.png"
                prompt = "Alpha, transcendent god-like cosmic entity in Valkyrie Defender form, supremely powerful divine figure in gleaming futuristic celestial plate armor inscribed with glowing void runes, enormous wings made of swirling void energy and cosmic starlight unfurling behind, holding an immense luminous shield that radiates protective divine light, hovering in the center of a cosmic void surrounded by spiral galaxies and nebulae, stars and planets visible in the background, awe-inspiring divine presence, ultra detailed epic fantasy sci-fi concept art, 8k"
            elif char.character_id == "player":
                filename = "player_avatar.png"
                player_desc = char.description or "A brave human specialist hero"
                prompt = f"A fantasy RPG hero, gender: {char.gender}, race: Human, class: Specialist, appearance: {player_desc}, fantasy concept art, highly detailed"
            else:
                in_party = any(c.character_id == char.character_id for c in rpg_state.party.active + rpg_state.party.reserve)
                if in_party:
                    filename = f"{char.character_id}.png"
                else:
                    filename = f"{char.race}_{char.char_class}.png"
                class_descs = {
                    "Defender": "muscular, strong, sturdy warrior, heavy armor",
                    "Guard": "brave warrior, iron armor, sharp blade",
                    "Caster": "magical wizard/witch, holding a glowing staff, robes",
                    "Sniper": "stealthy hunter/archer, holding a recurve bow, leather outfit",
                    "Supporter": "holy priest/cleric, casting healing magic, gentle look"
                }
                class_desc = class_descs.get(char.char_class, "adventurer")
                prompt = f"A fantasy RPG character, gender: {char.gender}, race: {char.race}, class: {char.char_class} ({class_desc}), appearance: {char.description or 'brave and determined look'}, fantasy concept art, highly detailed"

        # Sanitize filename
        filename_sanitized = filename.replace(" ", "_")
        dest_filename = f"{session_id}_{filename_sanitized}"
        
        settings = get_settings()
        url = f"{settings.kaggle_backend_url.rstrip('/')}/generate-world-theme"
        
        payload = {
            "prompt": prompt,
            "world_name": dest_filename.replace(".png", ""),
            "summarize_model": "gemini-2.5-flash",
            "txt2img_model": "SDXL lightning",
            "step": 4
        }
        
        try:
            res = await call_kaggle_api(url, payload)
            if res.get("status") == "success" and "image_base64" in res:
                saved_path = save_base64_image(res["image_base64"], dest_filename)
                return {
                    "success": True,
                    "image_url": saved_path,
                    "en_prompt": res.get("en_prompt", "")
                }
            else:
                raise ValueError("Kaggle backend không trả về ảnh hợp lệ.")
        except Exception as e:
            raise ValueError(f"Không thể kết nối đến Kaggle server: {e}")

    async def refresh_quest(self, session_id: str, quest_id: str, user_id: str) -> dict[str, Any]:
        """Refreshes a single quest by paying 2 gold and rolling a new one in the same category."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        # Find quest index
        quest_idx = -1
        for idx, q in enumerate(rpg_state.active_quests):
            if q.get("quest_id") == quest_id:
                quest_idx = idx
                break
                
        if quest_idx == -1:
            raise ValueError("Không tìm thấy nhiệm vụ yêu cầu.")
            
        quest_to_refresh = rpg_state.active_quests[quest_idx]
        if quest_to_refresh.get("completed"):
            raise ValueError("Nhiệm vụ đã hoàn thành, không thể làm mới.")
            
        if rpg_state.inventory.gold < 2:
            raise ValueError("Không đủ vàng (Cần 2 vàng để làm mới nhiệm vụ).")
            
        # Deduct cost
        rpg_state.inventory.gold -= 2
        category = quest_to_refresh.get("category", 1)
        
        # Generate new quest
        new_quest = QuestEngine.generate_quest_for_category(category, rpg_state)
        rpg_state.active_quests[quest_idx] = new_quest
        
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "active_quests": rpg_state.active_quests,
            "inventory": rpg_state.inventory.model_dump(),
            "message": f"Đã tiêu 2 vàng để làm mới nhiệm vụ. Nhiệm vụ mới: {new_quest.get('description')}",
            "rpg_state": session.rpg_state
        }

    async def fast_travel(self, session_id: str, target_region: str, user_id: str, background_tasks: BackgroundTasks | None = None) -> dict[str, Any]:
        """Performs fast travel to an unlocked major location."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        # Check if combat is active
        if rpg_state.combat and rpg_state.combat.is_active:
            raise ValueError("Không thể dịch chuyển nhanh khi đang trong chiến đấu.")
            
        # Check if dungeon is active
        if rpg_state.dungeon_state and rpg_state.dungeon_state.get("active"):
            raise ValueError("Không thể dịch chuyển nhanh khi đang thám hiểm hầm ngục.")
            
        # Find which environment target_region belongs to
        new_env = None
        for env, data in REGION_CATALOG.items():
            if data.get("major") == target_region:
                new_env = env
                break
                
        if not new_env:
            raise ValueError(f"Không xác định được môi trường của [{target_region}].")

        # Adjacency list graph of environments to calculate distance
        MAP_GRAPH = {
            "Đồng bằng": ["Hoang mạc", "Rừng rậm", "Đồi núi"],
            "Hoang mạc": ["Đồng bằng", "Núi lửa", "Rừng rậm", "Núi tuyết"],
            "Núi lửa": ["Hoang mạc"],
            "Núi tuyết": ["Hoang mạc", "Đồi núi"],
            "Đồi núi": ["Đồng bằng", "Núi tuyết", "Thiên giới"],
            "Rừng rậm": ["Đồng bằng", "Hoang mạc", "Thiên giới"],
            "Thiên giới": ["Đồi núi", "Rừng rậm"]
        }

        # Calculate BFS shortest path distance
        start_env = rpg_state.environment
        for env_name, data in REGION_CATALOG.items():
            if data.get("major") == start_env:
                start_env = env_name
                break
        distance = 0
        if start_env != new_env:
            queue = [(start_env, 0)]
            visited = {start_env}
            found = False
            while queue:
                curr, dist = queue.pop(0)
                if curr == new_env:
                    distance = dist
                    found = True
                    break
                for neighbor in MAP_GRAPH.get(curr, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append((neighbor, dist + 1))
            if not found:
                distance = 1  # Fallback

        cost = 100 * distance
        if rpg_state.inventory.gold < cost:
            raise ValueError(f"Không đủ vàng để dịch chuyển nhanh! Dịch chuyển từ {start_env} đến {new_env} (Khoảng cách: {distance}) yêu cầu {cost} vàng, nhưng bạn chỉ có {rpg_state.inventory.gold} vàng.")

        # Deduct gold cost
        rpg_state.inventory.gold -= cost

        # Log player action as user message
        user_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=f"Dịch chuyển nhanh đến {target_region}"
        )
        await self.store.add_message(user_msg)
            
        # Perform movement
        old_env = rpg_state.environment
        rpg_state.environment = new_env
        rpg_state.current_region = target_region
        rpg_state.current_event = None
        rpg_state.offered_event = None
        rpg_state.past_turn_is_special = False
        
        # Generate narrative text
        prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả cảnh tổ đội sử dụng cổng dịch chuyển không gian, tiêu tốn {cost} vàng để dịch chuyển nhanh từ {old_env} đến vương đô lớn [{target_region}] của vùng đất {new_env}."
        story_text = await self._generate_text_logged(
            prompt, user_id=user_id, session_id=session_id, operation="fast_travel.narrative"
        )
        
        # Generate travel choices inside the major location
        choices = [
            f"Rời khỏi {target_region} để thám hiểm vùng đất {new_env}",
            f"Khảo sát tìm hiểu xung quanh {target_region}",
            "Nghỉ ngơi hồi phục thể lực"
        ]
        
        # Track travels achievement
        ach_notifs = AchievementEngine.update_progress(rpg_state, "travels", 1)
        
        session.rpg_state = rpg_state.model_dump()
        
        # Log AI response as ai message
        ai_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="ai",
            content=story_text,
            choices=choices
        )
        await self.store.add_message(ai_msg)
        await self.store.update_session(session)
        
        # Schedule see-world generation task in background
        if background_tasks:
            background_tasks.add_task(self.generate_world_image, session_id, user_id)
            
        return {
            "session_id": session_id,
            "story": story_text,
            "choices": choices,
            "rpg_state": session.rpg_state,
            "notifications": ach_notifs
        }

    async def leave_region(self, session_id: str, user_id: str) -> dict[str, Any]:
        """Leaves the current regular region and returns to the main environment."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        if not rpg_state.current_region:
            raise ValueError("Hiện tại không ở trong khu vực nào.")
        if rpg_state.dungeon_state and rpg_state.dungeon_state.get("active"):
            raise ValueError("Không thể dùng tính năng này trong hầm ngục.")
        if rpg_state.combat and rpg_state.combat.is_active:
            raise ValueError("Không thể rời khỏi khu vực khi đang chiến đấu.")

        # Log player action as user message
        user_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=f"Rời khỏi {rpg_state.current_region}"
        )
        await self.store.add_message(user_msg)

        rpg_state.current_region = None
        rpg_state.past_turn_is_special = True
        rpg_state.offered_event = None
        
        prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả cảnh tổ đội rời khỏi địa điểm khám phá và quay lại môi trường bản đồ thế giới {rpg_state.environment} rộng lớn."
        story_text = await self._generate_text_logged(
            prompt, user_id=user_id, session_id=session_id, operation="region.leave"
        )
        
        rpg_state.turn_count += 1
        
        choices = ["Khám phá vùng đất mới", "Khám phá ngóc ngách xung quanh", "Tiếp tục di chuyển"]
        
        session.rpg_state = rpg_state.model_dump()
        
        ai_msg = Message(
            message_id=str(uuid.uuid4()),
            session_id=session_id,
            role="ai",
            content=story_text,
            choices=choices
        )
        await self.store.add_message(ai_msg)
        await self.store.update_session(session)
        
        return {
            "session_id": session_id,
            "story": story_text,
            "choices": choices,
            "event_type": None,
            "rpg_state": session.rpg_state,
            "message_id": ai_msg.message_id
        }

    async def restore_rpg_game(self, session_id: str, game_state: dict, user_id: str) -> bool:
        """Restores a serialized RPG state for the user session."""
        session = await self.store.get_session(session_id)
        if session:
            if session.user_id != user_id:
                raise PermissionError("Không có quyền phục hồi session này.")
            session.rpg_state = game_state
            await self.store.update_session(session)
        else:
            session = SessionState(
                session_id=session_id,
                user_id=user_id,
                is_saved=False,
                title=f"Hành trình RPG phục hồi",
                mode="rpg",
                rpg_state=game_state
            )
            await self.store.create_session(session)
        return True

    async def execute_debug_command(self, session_id: str, command: str, user_id: str) -> dict[str, Any]:
        """Executes a testing/debugging command to alter the RPG game state."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        story_text = ""
        choices = []
        is_combat_over = False
        result_status = "continue"
        
        from app.services.rpg_engine import (
            ITEM_CATALOG, BUY_PRICES, SELL_PRICES,
            RACE_CLASSES, RARITY_RACE_MAP, MYTHIC_CHARACTERS,
            STRANGER_RARITY_PROBS
        )
        
        def is_rarity_allowed(location: str | None, environment: str, rarity: str) -> bool:
            if rarity == "Mythic":
                return location in [
                    "Vương đô Victoria", "Long kinh thành", "Tòa Thành Chúa Quỷ",
                    "Pháo Đài Mùa Đông", "Thánh Đường Tối Cao The Light Heavens"
                ]
            if location == "Hang tối":
                return rarity in ["Legendary", "Uncommon", "Common"]
            return rarity in ["Legendary", "Epic", "Rare", "Uncommon", "Common"]
            
        def generate_item_by_rarity_and_type(item_type: str, rarity: str, quantity: int = 1) -> RPGItem:
            rarity_data = ITEM_CATALOG.get(rarity, ITEM_CATALOG["Common"])
            item_data = rarity_data.get(item_type, rarity_data["Consume"])
            
            stats_bonus = item_data.get("stats_bonus", {})
            description = item_data.get("description", "")
            name = item_data.get("name", "Vật phẩm")
            
            b_price = BUY_PRICES.get(rarity, 30)
            s_price = SELL_PRICES.get(rarity, 10)
            
            return RPGItem(
                item_id=f"{item_type.lower()}_{str(uuid.uuid4())[:8]}",
                name=name,
                rarity=rarity,
                item_type=item_type,
                stats_bonus=stats_bonus,
                description=description,
                quantity=quantity,
                buy_price=b_price,
                sell_price=s_price
            )

        cmd = command.strip()
        
        # 1. game_over
        if cmd == "game_over":
            if rpg_state.player_character:
                rpg_state.player_character.stats.hp = 0
            for c in rpg_state.party.active + rpg_state.party.reserve:
                c.stats.hp = 0
            rpg_state.combat = None
            rpg_state.current_event = None
            rpg_state.offered_event = None
            
            story_text = "💀 Lệnh DEBUG: GAME OVER! Bạn đã tử trận lập tức."
            
        # 2. gain_gold_{n}
        elif cmd.startswith("gain_gold_"):
            match = re.match(r"^gain_gold_(\d+)$", cmd)
            if not match:
                raise ValueError("Sai cú pháp lệnh gain_gold_{n}")
            n = int(match.group(1))
            rpg_state.inventory.gold += n
            story_text = f"✨ Lệnh DEBUG: Nhận thành công +{n} Vàng! (Tổng vàng: {rpg_state.inventory.gold})"
            
        # 3. gain_exp_{n}
        elif cmd.startswith("gain_exp_"):
            match = re.match(r"^gain_exp_(\d+)$", cmd)
            if not match:
                raise ValueError("Sai cú pháp lệnh gain_exp_{n}")
            n = int(match.group(1))
            exp_logs = []
            for char in rpg_state.party.active:
                logs = RPGEngine.add_exp(char, n, len(rpg_state.party.active))
                exp_logs.extend(logs)
            if rpg_state.player_character:
                for char in rpg_state.party.active:
                    if char.is_player_character:
                        rpg_state.player_character = char
            story_text = f"✨ Lệnh DEBUG: Cộng thành công +{n} EXP cho toàn tổ đội."
            if exp_logs:
                story_text += "\n" + "\n".join(exp_logs)
                
        # 4. gain_maxlvl
        elif cmd == "gain_maxlvl":
            for char in rpg_state.party.active + rpg_state.party.reserve:
                char.level = char.max_level
                char.exp = 0
                RPGEngine.sync_character_stats(char, len(rpg_state.party.active))
                char.stats.hp = char.stats.max_hp
            if rpg_state.player_character:
                rpg_state.player_character.level = rpg_state.player_character.max_level
                rpg_state.player_character.exp = 0
                RPGEngine.sync_character_stats(rpg_state.player_character, len(rpg_state.party.active))
                rpg_state.player_character.stats.hp = rpg_state.player_character.stats.max_hp
            # Also update combat_party copies so in-progress combat reflects new stats
            if rpg_state.combat and rpg_state.combat.is_active:
                alive_count = sum(1 for c in rpg_state.combat.combat_party if c.stats.hp > 0)
                for cc in rpg_state.combat.combat_party:
                    # Find matching party member (to get updated level)
                    party_char = next(
                        (c for c in rpg_state.party.active if c.character_id == cc.character_id), None
                    )
                    if party_char:
                        cc.level = party_char.level
                        cc.exp = 0
                        RPGEngine.sync_character_stats(cc, alive_count)
                        cc.stats.hp = cc.stats.max_hp
            story_text = "✨ Lệnh DEBUG: Đưa toàn bộ thành viên trong tổ đội đạt Cấp Độ Tối Đa (Level Max) và hồi đầy HP!"
            
        # 5. revive
        elif cmd == "revive":
            for char in rpg_state.party.active + rpg_state.party.reserve:
                char.stats.hp = char.stats.max_hp
                char.debuffs = []
                char.condition = "Bình thường"
            if rpg_state.player_character:
                rpg_state.player_character.stats.hp = rpg_state.player_character.stats.max_hp
                rpg_state.player_character.debuffs = []
                rpg_state.player_character.condition = "Bình thường"
            if rpg_state.combat:
                for char in rpg_state.combat.combat_party:
                    char.stats.hp = char.stats.max_hp
                    char.debuffs = []
            story_text = "✨ Lệnh DEBUG: Hồi sinh toàn bộ thành viên, hồi đầy HP và hóa giải mọi debuff thành công!"
            
        # 6. gain_{type}_{rarity}_{n}
        elif cmd.startswith("gain_") and len(cmd.split("_")) >= 4 and cmd.split("_")[1] in ["weapon", "armor", "consume"]:
            parts = cmd.split("_")
            item_type_raw = parts[1]
            rarity_raw = parts[2]
            try:
                n = int(parts[3])
            except ValueError:
                raise ValueError("Số lượng vật phẩm n phải là số nguyên.")
                
            item_type = item_type_raw.capitalize()
            rarity = rarity_raw.capitalize()
            
            if rarity not in ITEM_CATALOG:
                raise ValueError(f"Độ hiếm không hợp lệ: {rarity_raw}")
                
            new_item = generate_item_by_rarity_and_type(item_type, rarity, n)
            existing = next((i for i in rpg_state.inventory.items if i.name == new_item.name), None)
            if existing:
                existing.quantity += new_item.quantity
            else:
                rpg_state.inventory.items.append(new_item)
            story_text = f"✨ Lệnh DEBUG: Thêm thành công {n}x [{rarity}] {new_item.name} vào kho đồ!"
            
        # 7. go_to_{direct}_{region}
        elif cmd.startswith("go_to_"):
            parts = cmd.split("_")
            if len(parts) < 4:
                raise ValueError("Sai cú pháp lệnh go_to_{direct}_{region}")
            direct = parts[2].upper()
            region = parts[3].lower()
            
            direct_map = {
                "M": "Đồng bằng", "W": "Đồi núi", "E": "Hoang mạc",
                "NE": "Rừng rậm", "SW": "Núi tuyết", "SE": "Núi lửa", "NW": "Thiên giới"
            }
            if direct not in direct_map:
                raise ValueError(f"Hướng không hợp lệ: {parts[2]}")
            if region not in ["main", "sub", "dungeon", "none"]:
                raise ValueError(f"Kiến trúc không hợp lệ: {parts[3]}")
                
            target_env = direct_map[direct]
            rpg_state.environment = target_env
            rpg_state.current_region = None
            rpg_state.current_event = None
            rpg_state.offered_event = None
            
            rpg_state.debug_cheats["next_region"] = region
            story_text = f"✨ Lệnh DEBUG: Dịch chuyển thành công đến [{target_env}]. Lượt kế tiếp sẽ bắt gặp kiến trúc: {region.upper()}."
            
        # 8. meet_{character}
        elif cmd.startswith("meet_"):
            character = cmd.replace("meet_", "").lower()
            if character in ["merchant", "monk", "npc"]:
                probs = REGION_EVENT_PROBS.get(rpg_state.current_region) if rpg_state.current_region else ENVIRONMENT_EVENT_PROBS.get(rpg_state.environment)
                if not probs:
                    probs = {"stranger": 10, "merchant": 5, "monk": 5, "item": 10, "normal": 70}
                
                event_key = "merchant" if character == "merchant" else ("monk" if character == "monk" else "stranger")
                if probs.get(event_key, 0) <= 0:
                    raise ValueError(f"Vị trí hiện tại ({rpg_state.current_region or rpg_state.environment}) không có xác suất gặp {character}.")
                    
                rpg_state.debug_cheats["next_event"] = event_key
                story_text = f"✨ Lệnh DEBUG: Ép lượt tiếp theo bắt gặp sự kiện: {character.upper()}!"
                
            elif character in ["mythic", "legendary", "epic", "rare", "uncommon", "common"]:
                rarity = character.capitalize()
                loc = rpg_state.current_region
                env = rpg_state.environment
                if not is_rarity_allowed(loc, env, rarity):
                    raise ValueError(f"Vị trí hiện tại ({loc or env}) không hỗ trợ độ hiếm {rarity}.")
                    
                rpg_state.debug_cheats["next_event"] = "stranger"
                rpg_state.debug_cheats["next_stranger_rarity"] = rarity
                story_text = f"✨ Lệnh DEBUG: Ép lượt tiếp theo bắt gặp Kẻ lạ mặt có độ hiếm: {rarity}!"
            else:
                raise ValueError(f"Nhân vật hoặc độ hiếm không được hỗ trợ: {character}")
                
        # 9. recruit_{race}_{class}_{gender}
        elif cmd.startswith("recruit_"):
            parts = cmd.split("_")
            if len(parts) < 4:
                raise ValueError("Sai cú pháp lệnh recruit_{race}_{class}_{gender}")
            race_raw = parts[1].lower()
            class_raw = parts[2].lower()
            gender_raw = parts[3].lower()
            
            race_map = {
                "valkyrie": "Valkyrie", "angel": "Angel", "devil": "Devil",
                "elf": "Elf", "royalty": "Royalty", "orc": "Orc",
                "goblin": "Goblin", "human": "Human"
            }
            class_map = {
                "defender": "Defender", "guard": "Guard", "caster": "Caster",
                "sniper": "Sniper", "supporter": "Supporter"
            }
            gender_map = {
                "male": "Male", "female": "Female"
            }
            
            if race_raw not in race_map:
                raise ValueError(f"Chủng tộc không hợp lệ: {parts[1]}")
            if class_raw not in class_map:
                raise ValueError(f"Lớp nhân vật không hợp lệ: {parts[2]}")
            if gender_raw not in gender_map:
                raise ValueError(f"Giới tính không hợp lệ: {parts[3]}")
                
            race = race_map[race_raw]
            char_class = class_map[class_raw]
            gender = gender_map[gender_raw]
            
            allowed_classes = RACE_CLASSES.get(race, [])
            if char_class not in allowed_classes:
                raise ValueError(f"Lớp nhân vật {char_class} không khả dụng cho tộc {race}.")
                
            total_party = len(rpg_state.party.active) + len(rpg_state.party.reserve)
            if total_party >= 9:
                raise ValueError("Đội hình đã đầy! (Tối đa 4 chính thức, 5 dự bị)")
                
            rarity = "Common"
            for r_key, r_list in RARITY_RACE_MAP.items():
                if race in r_list:
                    rarity = r_key
                    break
                    
            name = f"{gender} {race} {char_class}"
            if rarity == "Mythic":
                preset_list = MYTHIC_CHARACTERS.get(char_class, [])
                preset = next((p for p in preset_list if p.get("gender") == gender), None)
                if not preset and preset_list:
                    preset = preset_list[0]
                if preset:
                    name = preset["name"]
                    gender = preset["gender"]
                    
            lvl = rpg_state.player_character.level if rpg_state.player_character else 1
            new_char = RPGEngine.generate_random_character(lvl, {"Mythic": 0, "Legendary": 0, "Epic": 0, "Rare": 0, "Uncommon": 0, "Common": 100})
            new_char.name = name
            new_char.race = race
            new_char.char_class = char_class
            new_char.gender = gender
            new_char.rarity = rarity
            
            RPGEngine.init_character_skills(new_char)
            RPGEngine.sync_character_stats(new_char, len(rpg_state.party.active) + 1)
            new_char.stats.hp = new_char.stats.max_hp
            
            if len(rpg_state.party.active) < 4:
                rpg_state.party.active.append(new_char)
                for c in rpg_state.party.active:
                    RPGEngine.sync_character_stats(c, len(rpg_state.party.active))
                dest = "chính thức"
            else:
                rpg_state.party.reserve.append(new_char)
                dest = "dự bị"
                
            self.copy_character_avatar(session_id, new_char)
            story_text = f"✨ Lệnh DEBUG: Đã chiêu mộ [{rarity}] {name} ({race} {char_class}) thành công vào đội hình {dest}!"
            
        # 10. found_item
        elif cmd == "found_item":
            probs = REGION_EVENT_PROBS.get(rpg_state.current_region) if rpg_state.current_region else ENVIRONMENT_EVENT_PROBS.get(rpg_state.environment)
            if not probs:
                probs = {"stranger": 10, "merchant": 5, "monk": 5, "item": 10, "normal": 70}
            if probs.get("item", 0) <= 0:
                raise ValueError(f"Vị trí hiện tại ({rpg_state.current_region or rpg_state.environment}) không có xác suất tìm thấy vật phẩm.")
                
            rpg_state.debug_cheats["next_event"] = "item"
            story_text = "✨ Lệnh DEBUG: Ép lượt tiếp theo bắt gặp sự kiện: TÌM THẤY VẬT PHẨM!"
            
        # 11. gain_keys
        elif cmd == "gain_keys":
            environments_list = ["Đồng bằng", "Đồi núi", "Rừng rậm", "Núi lửa", "Hoang mạc", "Núi tuyết", "Thiên giới"]
            added = []
            for env in environments_list:
                frag_name = f"Mảnh vỡ chìa khoá vĩ đại {env}"
                existing = next((i for i in rpg_state.inventory.items if i.name == frag_name), None)
                if not existing:
                    key_frag = RPGItem(
                        item_id=f"key_{str(uuid.uuid4())[:8]}",
                        name=frag_name,
                        rarity="Epic",
                        item_type="Consume",
                        description=f"Một mảnh vỡ cổ đại chứa năng lượng bảo vệ của vùng đất {env}.",
                        quantity=1
                    )
                    rpg_state.inventory.items.append(key_frag)
                    added.append(env)
            if added:
                story_text = f"✨ Lệnh DEBUG: Nhận thành công các mảnh khóa còn thiếu của các vùng đất: {', '.join(added)}!"
            else:
                story_text = "✨ Lệnh DEBUG: Bạn đã sở hữu đầy đủ 7 mảnh khóa vĩ đại trong kho đồ!"
                
        # 12-14. good_ending, bad_ending, continue_ending
        elif cmd in ["good_ending", "bad_ending", "continue_ending"]:
            choice_idx = 0 if cmd == "good_ending" else (1 if cmd == "bad_ending" else 2)
            rpg_state.offered_event = "ending_choice"
            session.rpg_state = rpg_state.model_dump()
            await self.store.update_session(session)
            return await self.process_turn(session_id, choice_index=choice_idx, user_id=user_id)
            
        # 15. combat_{type}
        elif cmd.startswith("combat_"):
            ctype = cmd.replace("combat_", "").lower()
            if not rpg_state.combat or not rpg_state.combat.is_active:
                raise ValueError("Không ở trong trận đấu đang kích hoạt.")
                
            if ctype == "kill":
                rpg_state.combat.enemy.stats.hp = 0
                if rpg_state.dungeon_state and rpg_state.dungeon_state.get("active"):
                    session.rpg_state = rpg_state.model_dump()
                    await self.store.update_session(session)
                    return await self.process_combat_end_action(session_id, action="loot", user_id=user_id)
                else:
                    enemy = rpg_state.combat.enemy
                    combat_log = ["⚔️ Lệnh DEBUG: Tiêu diệt kẻ địch ngay lập tức!"]
                    
                    if enemy.name == "Alpha":
                        rpg_state.combat = None
                        rpg_state.current_event = None
                        AchievementEngine.update_progress(rpg_state, "final_boss_defeated", 1)
                        rpg_state.offered_event = "ending_choice"
                        
                        prompt = "Viết bằng tiếng Việt (dưới 120 từ) miêu tả cảnh trùm cuối Alpha bị đánh bại thảm hại, thân hình khổng lồ của hắn vỡ tan thành ngàn mảnh sáng hư không. Thế giới rung chuyển, một cánh cổng ánh sáng và năng lượng hư không cổ xưa hiện ra mở ra 3 ngả đường số phận."
                        ai_narrative = await self._generate_text_logged(
                            prompt, user_id=user_id, session_id=session_id, operation="combat.alpha_defeat"
                        )
                        
                        ai_msg = Message(
                            message_id=str(uuid.uuid4()),
                            session_id=session_id,
                            role="ai",
                            content=f"👑 ALPHA ĐÃ BẠI TRẬN!\n\n{ai_narrative}",
                            choices=[
                                "Good Ending - Trở về thế giới thực với vinh quang cứu thế",
                                "Bad Ending - Đồng hóa với Hư Không và trở thành Alpha tiếp theo",
                                "Continue Ending - Từ chối kết cục, tiếp tục hành trình vô tận"
                            ]
                        )
                        await self.store.add_message(ai_msg)
                        
                        session.rpg_state = rpg_state.model_dump()
                        await self.store.update_session(session)
                        
                        return {
                            "session_id": session_id,
                            "combat_log": combat_log,
                            "story": ai_msg.content,
                            "combat_state": None,
                            "is_combat_over": True,
                            "result": "win",
                            "choices": ai_msg.choices,
                            "rpg_state": session.rpg_state,
                            "message_id": ai_msg.message_id
                        }
                    elif enemy.name in ["Medusa", "Golem", "WereWolf", "Dracula", "Vua Goblin", "Poseidon", "Diablo", "Thiên Dực Long Vương", "Ma vương Xương Cốt"] or enemy.char_class == "Boss":
                        self._sync_combat_party_back(rpg_state)
                        rpg_state.combat = None
                        rpg_state.current_event = None
                        rpg_state.current_stranger = None
                        rpg_state.past_turn_is_special = True
                        
                        gold_gained, exp_gained, items = EventEngine.calculate_combat_drops(enemy)
                        rpg_state.inventory.gold += gold_gained
                        
                        exp_logs = []
                        for char in rpg_state.party.active:
                            if char.stats.hp > 0:
                                lvl_logs = RPGEngine.add_exp(char, exp_gained, len(rpg_state.party.active))
                                exp_logs.extend(lvl_logs)
                        
                        for char in rpg_state.party.active:
                            if char.is_player_character:
                                rpg_state.player_character = char
                                
                        item_names = []
                        for item in items:
                            existing = next((i for i in rpg_state.inventory.items if i.name == item.name), None)
                            if existing:
                                existing.quantity += 1
                            else:
                                rpg_state.inventory.items.append(item)
                            item_names.append(f"[{item.rarity}] {item.name}")
                            
                        prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả cảnh kết liễu Boss {enemy.name} và thu nhặt toàn bộ vật phẩm quý hiếm rơi ra. Phần thưởng: +{gold_gained} Vàng, +{exp_gained} EXP."
                        story_text = await self._generate_text_logged(
                            prompt, user_id=user_id, session_id=session_id, operation="combat.boss_loot"
                        )
                        
                        drop_summary = f"\n\n🏆 ĐÃ TIÊU DIỆT BOSS {enemy.name.upper()}!"
                        drop_summary += f"\n💰 Nhận {gold_gained} vàng. (Tổng vàng: {rpg_state.inventory.gold})"
                        drop_summary += f"\n📈 Toàn đội nhận +{exp_gained} EXP."
                        if exp_logs:
                            drop_summary += "\n" + "\n".join(exp_logs)
                        if item_names:
                            drop_summary += f"\n🎁 Vật phẩm nhặt được: {', '.join(item_names)}"
                        story_text += drop_summary
                        
                        messages = await self.store.get_messages(session_id, limit=100)
                        ai_choices_prompt = build_rpg_turn_prompt(
                            session=session,
                            recent_messages=messages,
                            relevant_memories=[],
                            player_input=f"Hạ gục Boss {enemy.name} (loot)",
                            rpg_state_dict=rpg_state.model_dump(),
                            event_type=None
                        )
                        raw = await self._generate_text_logged(
                            ai_choices_prompt, user_id=user_id, session_id=session_id, operation="combat.boss.transition"
                        )
                        parsed = parse_rpg_output(raw)
                        choices = parsed["choices"]
                        
                        session.rpg_state = rpg_state.model_dump()
                        ai_msg = Message(
                            message_id=str(uuid.uuid4()),
                            session_id=session_id,
                            role="ai",
                            content=story_text,
                            choices=choices
                        )
                        await self.store.add_message(ai_msg)
                        await self.store.update_session(session)
                        
                        return {
                            "session_id": session_id,
                            "combat_log": combat_log,
                            "story": story_text,
                            "combat_state": None,
                            "is_combat_over": True,
                            "result": "win",
                            "choices": choices,
                            "rpg_state": session.rpg_state,
                            "message_id": ai_msg.message_id
                        }
                    else:
                        self._sync_combat_party_back(rpg_state)
                        rpg_state.combat = None
                        rpg_state.current_event = None
                        rpg_state.current_stranger = None
                        rpg_state.past_turn_is_special = True
                        
                        gold_gained, exp_gained, items = EventEngine.calculate_combat_drops(enemy)
                        rpg_state.inventory.gold += gold_gained
                        
                        exp_logs = []
                        for char in rpg_state.party.active:
                            if char.stats.hp > 0:
                                lvl_logs = RPGEngine.add_exp(char, exp_gained, len(rpg_state.party.active))
                                exp_logs.extend(lvl_logs)
                                
                        for char in rpg_state.party.active:
                            if char.is_player_character:
                                rpg_state.player_character = char
                                
                        prompt = f"Viết bằng tiếng Việt (dưới 100 từ) miêu tả cảnh hạ gục quái vật {enemy.name} trong thế giới hoang dã. Phần thưởng: +{gold_gained} Vàng, +{exp_gained} EXP."
                        story_text = await self._generate_text_logged(
                            prompt, user_id=user_id, session_id=session_id, operation="combat.win_loot"
                        )
                        
                        drop_summary = f"\n\n🏆 ĐÃ TIÊU DIỆT {enemy.name.upper()}!"
                        drop_summary += f"\n💰 Nhận {gold_gained} vàng. (Tổng vàng: {rpg_state.inventory.gold})"
                        drop_summary += f"\n📈 Toàn đội nhận +{exp_gained} EXP."
                        if exp_logs:
                            drop_summary += "\n" + "\n".join(exp_logs)
                        story_text += drop_summary
                        
                        messages = await self.store.get_messages(session_id, limit=100)
                        ai_choices_prompt = build_rpg_turn_prompt(
                            session=session,
                            recent_messages=messages,
                            relevant_memories=[],
                            player_input=f"Đánh bại {enemy.name}",
                            rpg_state_dict=rpg_state.model_dump(),
                            event_type=None
                        )
                        raw = await self._generate_text_logged(
                            ai_choices_prompt, user_id=user_id, session_id=session_id, operation="combat.win.transition"
                        )
                        parsed = parse_rpg_output(raw)
                        choices = parsed["choices"]
                        
                        session.rpg_state = rpg_state.model_dump()
                        ai_msg = Message(
                            message_id=str(uuid.uuid4()),
                            session_id=session_id,
                            role="ai",
                            content=story_text,
                            choices=choices
                        )
                        await self.store.add_message(ai_msg)
                        await self.store.update_session(session)
                        
                        return {
                            "session_id": session_id,
                            "combat_log": combat_log,
                            "story": story_text,
                            "combat_state": None,
                            "is_combat_over": True,
                            "result": "win",
                            "choices": choices,
                            "rpg_state": session.rpg_state,
                            "message_id": ai_msg.message_id
                        }
            elif ctype == "recruit":
                if rpg_state.dungeon_state and rpg_state.dungeon_state.get("active"):
                    raise ValueError("Lệnh combat_recruit không áp dụng trong Hầm ngục.")
                return await self.process_combat_end_action(session_id, action="recruit", user_id=user_id)
            elif ctype == "forgive":
                if rpg_state.dungeon_state and rpg_state.dungeon_state.get("active"):
                    raise ValueError("Lệnh combat_forgive không áp dụng trong Hầm ngục.")
                return await self.process_combat_end_action(session_id, action="forgive", user_id=user_id)
            else:
                raise ValueError(f"Kiểu lệnh combat không hợp lệ: {ctype}")
                
        # 16. dummy_combat
        elif cmd == "dummy_combat":
            rpg_state.dummy_combat_backup = rpg_state.party.model_copy(deep=True)
            dummy = RPGCharacter(
                character_id="dummy",
                name="Dummy",
                race="Human",
                char_class="Defender",
                rarity="Common",
                gender="Male",
                level=1,
                stats=RPGCharacterStats(
                    max_hp=10000,
                    hp=10000,
                    atk=0,
                    res=0,
                    defense=50,
                    res_def=50,
                    atk_spd=0
                )
            )
            dummy.base_stats = dummy.stats.model_copy()
            rpg_state.combat = RPGCombatState(
                cb_turn_count=0,
                combat_party=[c.model_copy(deep=True) for c in rpg_state.party.active],
                enemy=dummy,
                combat_log=[],
                is_active=True
            )
            rpg_state.current_event = None
            rpg_state.offered_event = None
            story_text = "⚔️ Bắt đầu đấu tập với hình nộm Dummy (HP 10000)! Sát thương nhận từ đấu tập sẽ không ảnh hưởng tiến trình chính."
            
        # 16b. dummy_kill
        elif cmd == "dummy_kill":
            if not rpg_state.combat or not rpg_state.combat.is_active or rpg_state.combat.enemy.character_id != "dummy":
                raise ValueError("Không ở trong trận đấu tập với Dummy.")
            rpg_state.combat = None
            if rpg_state.dummy_combat_backup:
                rpg_state.party = rpg_state.dummy_combat_backup
                rpg_state.dummy_combat_backup = None
            story_text = "⚔️ Đã kết thúc đấu tập với Dummy. Trạng thái tổ đội đã được phục hồi nguyên vẹn như trước khi đấu tập."
            
        # 16c. dummy_reset
        elif cmd == "dummy_reset":
            if not rpg_state.combat or not rpg_state.combat.is_active or rpg_state.combat.enemy.character_id != "dummy":
                raise ValueError("Không ở trong trận đấu tập với Dummy.")
            rpg_state.combat.enemy.stats.hp = 10000
            rpg_state.combat.enemy.debuffs = []
            rpg_state.combat.enemy.buffs = []
            rpg_state.combat.combat_party = [c.model_copy(deep=True) for c in rpg_state.dummy_combat_backup.active]
            story_text = "⚔️ Lệnh DEBUG: Đã reset trận đấu tập Dummy về trạng thái ban đầu!"
            
        # 16d. dummy_recharge
        elif cmd == "dummy_recharge":
            if not rpg_state.combat or not rpg_state.combat.is_active or rpg_state.combat.enemy.character_id != "dummy":
                raise ValueError("Không ở trong trận đấu tập với Dummy.")
            for c in rpg_state.combat.combat_party:
                c.special_skills.skill_1_countdown = 0
                c.special_skills.skill_2_countdown = 0
                c.special_skills.skill_1_activated = False
                c.special_skills.skill_1_activating = False
                c.special_skills.passive_activated = False
            story_text = "⚔️ Lệnh DEBUG: Hồi phục toàn bộ thời gian hồi chiêu của tổ đội đấu tập!"
            
        # 16e. dummy_revive
        elif cmd == "dummy_revive":
            if not rpg_state.combat or not rpg_state.combat.is_active or rpg_state.combat.enemy.character_id != "dummy":
                raise ValueError("Không ở trong trận đấu tập với Dummy.")
            for c in rpg_state.combat.combat_party:
                c.stats.hp = c.stats.max_hp
                c.debuffs = []
            story_text = "⚔️ Lệnh DEBUG: Hồi sinh và hồi phục đầy HP cho tổ đội đấu tập!"
            
        # 16f. dummy_restore
        elif cmd == "dummy_restore":
            if not rpg_state.combat or not rpg_state.combat.is_active or rpg_state.combat.enemy.character_id != "dummy":
                raise ValueError("Không ở trong trận đấu tập với Dummy.")
            rpg_state.combat.enemy.stats.hp = 10000
            rpg_state.combat.enemy.debuffs = []
            rpg_state.combat.enemy.buffs = []
            story_text = "⚔️ Lệnh DEBUG: Hồi phục đầy máu cho hình nộm Dummy!"
            
        # 16g. dummy_drain_{n}
        elif cmd.startswith("dummy_drain_") and not cmd.startswith("dummy_drain_party_"):
            if not rpg_state.combat or not rpg_state.combat.is_active or rpg_state.combat.enemy.character_id != "dummy":
                raise ValueError("Không ở trong trận đấu tập với Dummy.")
            match = re.match(r"^dummy_drain_(\d+)$", cmd)
            if not match:
                raise ValueError("Sai cú pháp lệnh dummy_drain_{n}")
            n = int(match.group(1))
            if n < 1 or n >= 100:
                raise ValueError("Tỷ lệ n phải nằm trong khoảng từ 1 đến 99.")
            enemy = rpg_state.combat.enemy
            enemy.stats.hp = int(enemy.stats.hp * n / 100)
            story_text = f"⚔️ Lệnh DEBUG: Giảm HP của Dummy xuống còn {n}% ({enemy.stats.hp}/{enemy.stats.max_hp})."
            
        # 16h. dummy_drain_party_{n}
        elif cmd.startswith("dummy_drain_party_"):
            if not rpg_state.combat or not rpg_state.combat.is_active or rpg_state.combat.enemy.character_id != "dummy":
                raise ValueError("Không ở trong trận đấu tập với Dummy.")
            match = re.match(r"^dummy_drain_party_(\d+)$", cmd)
            if not match:
                raise ValueError("Sai cú pháp lệnh dummy_drain_party_{n}")
            n = int(match.group(1))
            if n < 1 or n >= 100:
                raise ValueError("Tỷ lệ n phải nằm trong khoảng từ 1 đến 99.")
            for c in rpg_state.combat.combat_party:
                if not c.is_player_character:
                    c.stats.hp = int(c.stats.hp * n / 100)
            story_text = f"⚔️ Lệnh DEBUG: Giảm HP của các đồng hành trong party xuống còn {n}%."
            
        # 17. boss_e1_{character}_combat
        elif cmd.startswith("boss_e1_") and cmd.endswith("_combat"):
            boss_key = cmd.replace("boss_e1_", "").replace("_combat", "").lower()
            boss_names = {
                "medusa": "Medusa", "goblin": "Vua Goblin", "werewolf": "WereWolf",
                "dracula": "Dracula", "golem": "Golem"
            }
            if boss_key not in boss_names:
                raise ValueError(f"Boss Elite 1 không hợp lệ: {boss_key}")
            boss_name = boss_names[boss_key]
            
            player_level = rpg_state.player_character.level if rpg_state.player_character else 1
            enemy = RPGEngine.generate_random_character(70, {"Mythic": 0, "Legendary": 0, "Epic": 100, "Rare": 0, "Uncommon": 0, "Common": 0})
            enemy.name = boss_name
            enemy.race = "Bí ẩn"
            enemy.char_class = "Bí ẩn"
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
            self._scale_boss_stats_by_level(enemy, player_level)
            enemy.base_stats = enemy.stats.model_copy()
            
            rpg_state.combat = RPGCombatState(
                cb_turn_count=0,
                combat_party=[c.model_copy(deep=True) for c in rpg_state.party.active],
                enemy=enemy,
                combat_log=[],
                is_active=True
            )
            rpg_state.current_event = None
            rpg_state.offered_event = None
            story_text = f"⚔️ Lệnh DEBUG: Bắt đầu COMBAT chống lại Boss Elite 1: {boss_name}!"
            
        # 18. boss_e2_{character}_combat
        elif cmd.startswith("boss_e2_") and cmd.endswith("_combat"):
            boss_key = cmd.replace("boss_e2_", "").replace("_combat", "").lower()
            boss_names = {
                "fishman": "Poseidon", "devil": "Diablo", "dragon": "Thiên Dực Long Vương", "undead": "Ma vương Xương Cốt"
            }
            if boss_key not in boss_names:
                raise ValueError(f"Boss Elite 2 không hợp lệ: {boss_key}")
            boss_name = boss_names[boss_key]
            
            player_level = rpg_state.player_character.level if rpg_state.player_character else 1
            enemy = RPGEngine.generate_random_character(80, {"Mythic": 0, "Legendary": 100, "Epic": 0, "Rare": 0, "Uncommon": 0, "Common": 0})
            enemy.name = boss_name
            enemy.race = "Bí ẩn"
            enemy.char_class = "Bí ẩn"
            if boss_name == "Poseidon":
                enemy.stats.max_hp = 1000
                enemy.stats.atk = 150
                enemy.stats.defense = 60
                enemy.stats.res = 80
                enemy.stats.res_def = 60
                enemy.stats.atk_spd = 80
            elif boss_name == "Diablo":
                enemy.stats.max_hp = 1000
                enemy.stats.atk = 100
                enemy.stats.defense = 70
                enemy.stats.res = 150
                enemy.stats.res_def = 40
                enemy.stats.atk_spd = 70
            elif boss_name == "Thiên Dực Long Vương":
                enemy.stats.max_hp = 1000
                enemy.stats.atk = 80
                enemy.stats.defense = 60
                enemy.stats.res = 160
                enemy.stats.res_def = 40
                enemy.stats.atk_spd = 60
            elif boss_name == "Ma vương Xương Cốt":
                enemy.stats.max_hp = 1000
                enemy.stats.atk = 100
                enemy.stats.defense = 90
                enemy.stats.res = 80
                enemy.stats.res_def = 60
                enemy.stats.atk_spd = 70
            enemy.stats.hp = enemy.stats.max_hp
            self._scale_boss_stats_by_level(enemy, player_level)
            enemy.base_stats = enemy.stats.model_copy()
            
            rpg_state.combat = RPGCombatState(
                cb_turn_count=0,
                combat_party=[c.model_copy(deep=True) for c in rpg_state.party.active],
                enemy=enemy,
                combat_log=[],
                is_active=True
            )
            rpg_state.current_event = None
            rpg_state.offered_event = None
            story_text = f"⚔️ Lệnh DEBUG: Bắt đầu COMBAT chống lại Boss Elite 2: {boss_name}!"
            
        # 19. final_boss_combat
        elif cmd == "final_boss_combat":
            alpha = RPGCharacter(
                character_id=str(uuid.uuid4()),
                name="Alpha",
                rarity="Mythic",
                race="Bí ẩn",
                char_class="Bí ẩn",
                level=90,
                gender="Male",
                exp=0,
                buffs=[],
                debuffs=[]
            )
            alpha.stats.max_hp = 2000
            alpha.stats.hp = 2000
            alpha.stats.atk = 200
            alpha.stats.defense = 90
            alpha.stats.res = 160
            alpha.stats.res_def = 50
            alpha.stats.atk_spd = 120
            alpha_player_level = rpg_state.player_character.level if rpg_state.player_character else 1
            self._scale_boss_stats_by_level(alpha, alpha_player_level)
            alpha.base_stats = alpha.stats.model_copy()
            
            rpg_state.combat = RPGCombatState(
                cb_turn_count=0,
                combat_party=[c.model_copy(deep=True) for c in rpg_state.party.active],
                enemy=alpha,
                combat_log=[],
                is_active=True
            )
            rpg_state.current_event = None
            rpg_state.offered_event = None
            story_text = "⚔️ Lệnh DEBUG: Bắt đầu COMBAT với TRÙM CUỐI ALPHA!"
            
        else:
            raise ValueError(f"Không nhận diện được lệnh debug: {command}")
            
        if story_text:
            ai_msg = Message(
                message_id=str(uuid.uuid4()),
                session_id=session_id,
                role="ai",
                content=story_text,
                choices=choices
            )
            await self.store.add_message(ai_msg)
            
        # If dummy combat was defeated naturally (combat is over, result is win, and enemy was dummy)
        if rpg_state.combat and not rpg_state.combat.is_active:
            if rpg_state.combat.enemy.character_id == "dummy" and rpg_state.combat.enemy.stats.hp <= 0:
                rpg_state.combat = None
                if rpg_state.dummy_combat_backup:
                    rpg_state.party = rpg_state.dummy_combat_backup
                    rpg_state.dummy_combat_backup = None
                story_text = "⚔️ Bia đỡ đạn Dummy đã bị tiêu diệt! Trận đấu tập kết thúc và trạng thái tổ đội của bạn đã được khôi phục."
                
                ai_msg = Message(
                    message_id=str(uuid.uuid4()),
                    session_id=session_id,
                    role="ai",
                    content=story_text,
                    choices=[]
                )
                await self.store.add_message(ai_msg)
                
        session.rpg_state = rpg_state.model_dump()
        await self.store.update_session(session)
        
        combat_state = None
        if rpg_state.combat:
            combat_state = rpg_state.combat.model_dump()
            is_combat_over = not rpg_state.combat.is_active
            result_status = "win" if (is_combat_over and rpg_state.combat.enemy.stats.hp <= 0) else "continue"
            
        return {
            "session_id": session_id,
            "story": story_text,
            "choices": choices,
            "rpg_state": session.rpg_state,
            "is_combat_over": is_combat_over,
            "combat_state": combat_state,
            "result": result_status
        }

