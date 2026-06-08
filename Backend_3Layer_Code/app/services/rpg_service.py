import json
import random
import re
import uuid
from time import perf_counter
from typing import Any
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
    RPGParty, RPGInventory, RPGShopState, RPGCombatState
)
from app.services.rpg_engine import RPGEngine, CombatEngine, EventEngine, ShopEngine
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
    if not os.path.exists(template_dir):
        os.makedirs(template_dir, exist_ok=True)
        # Copy the 4 Valkyries from root if they exist
        valkyries = {
            "Hoshiguma_the_Breacher.png": "Hoshiguma_the_breacher.png",
            "Lemuen.png": "Lemuen.png",
            "Vina_Victoria.png": "VinaVictoria.png",
            "Wang.png": "Wang.png"
        }
        for src_name, dest_name in valkyries.items():
            if os.path.exists(src_name):
                try:
                    shutil.copy(src_name, os.path.join(template_dir, dest_name))
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

class RPGService:
    def __init__(self) -> None:
        self.provider = get_text_provider()
        self.store = FirebaseStore()
        self.admin_control = AdminControlService()
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

    async def start_rpg_game(self, request: Any, user_id: str) -> dict[str, Any]:
        """Creates the initial SessionState and game models for RPG mode."""
        self.safety_filter.validate_input(request.player_name, "Tên người chơi")
        
        # 1. Create Specialist player character
        player_char = RPGEngine.generate_player_character(request.player_name, request.gender)
        if hasattr(request, "appearance_desc") and request.appearance_desc:
            player_char.description = request.appearance_desc
        
        # 2. Build initial empty RPG Game State
        rpg_state = RPGGameState(
            turn_count=0,
            past_turn_is_special=False,
            party=RPGParty(active=[player_char], reserve=[]),
            inventory=RPGInventory(items=[], gold=0),
            shop=RPGShopState(level=1, items_for_sale=[], mercenaries_for_sale=[]),
            player_character=player_char,
            current_event=None,
            region=request.region or "",
            objective=request.objective or ""
        )
        
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

    async def process_turn(self, session_id: str, choice_index: int, user_id: str) -> dict[str, Any]:
        """Executes a standard turn choice, processing event triggers or normal narrative flow."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
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
            else:
                # Player bypassed the event (Choice 2 or 3) -> proceed with normal story
                rpg_state.offered_event = None
                event_rolled = None
        else:
            # Check if past turn was special. If so, reset flag, no event rolled.
            if rpg_state.past_turn_is_special:
                rpg_state.past_turn_is_special = False
            else:
                # Only choice_index == 0 can trigger random events (Adventure choice)
                if choice_index == 0:
                    event_rolled = EventEngine.roll_event()
                    if event_rolled and event_rolled != "normal":
                        # We rolled a special event! But we only OFFER it.
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
                event_ctx = "Tu sĩ hiền triết vẫy tay chào bạn."
            elif event_rolled == "merchant":
                choices = ["Trò chuyện", "Xem cửa hàng", "Tạm biệt"]
                event_ctx = "Thương nhân chào mời bạn ghé xem hàng."
                items, mercs = ShopEngine.generate_shop_stock(rpg_state.shop.level, rpg_state.player_character.level)
                rpg_state.shop.items_for_sale = items
                rpg_state.shop.mercenaries_for_sale = mercs
            elif event_rolled == "stranger":
                choices = ["Trò chuyện", "Tấn công", "Tránh xung đột"]
                stranger = RPGEngine.generate_random_character(rpg_state.player_character.level)
                desc_prompt = build_rpg_npc_description_prompt(stranger)
                stranger.description = await self._generate_text_logged(
                    desc_prompt, user_id=user_id, session_id=session_id, operation="stranger.description"
                )
                rpg_state.current_stranger = stranger
                rpg_state.sympathy = 0
                event_ctx = f"Gặp người lạ mặt tên: {stranger.name} ({stranger.race} {stranger.char_class})."
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
            choices = parsed["choices"]

        rpg_state.turn_count += 1
        session.rpg_state = rpg_state.model_dump()
        
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

    async def process_turn_prompt(self, session_id: str, player_input: str, user_id: str) -> dict[str, Any]:
        """Handles custom text prompt entry instead of clicking preset choices."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
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
                        # Sync VinaVictoria/other stats
                        for c in rpg_state.party.active:
                            RPGEngine.sync_character_stats(c, len(rpg_state.party.active))
                        joined_msg = "đội hình chính thức"
                    else:
                        rpg_state.party.reserve.append(stranger)
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
        
        # Handle player death immediately if result is "lose"
        if result == "lose":
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

    async def process_combat_end_action(self, session_id: str, action: str, user_id: str) -> dict[str, Any]:
        """Resolves the victory rewards choice after winning combat against a stranger."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
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

    async def process_shop_buy_merc(self, session_id: str, merc_index: int, user_id: str) -> dict[str, Any]:
        """Hires a shop mercenary."""
        session = await self.store.get_session(session_id)
        if not session:
            raise ValueError("Không tìm thấy session.")
        if session.user_id != user_id:
            raise PermissionError("Không có quyền.")
            
        rpg_state = RPGGameState.model_validate(session.rpg_state)
        
        success, msg, shop, party, inv = ShopEngine.buy_mercenary(
            rpg_state.shop, rpg_state.party, rpg_state.inventory, merc_index
        )
        if not success:
            raise ValueError(msg)
            
        rpg_state.shop = shop
        rpg_state.party = party
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
        if not item or item.item_type != "Consume":
            raise ValueError("Không tìm thấy vật phẩm tiêu hao hợp lệ.")
            
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
            "message": msg
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
        
        if last_msg and last_msg.content:
            prompt = last_msg.content
        else:
            prompt = f"A beautiful fantasy landscape in the region of {rpg_state.region or 'mysterious land'} with the objective of {rpg_state.objective or 'adventure'}."
            
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
        if character_id == "monk":
            filename = "monk.png"
            prompt = "A serene holy monk character in a fantasy RPG, sitting in a peaceful temple background, wearing humble golden and white robes, glowing aura, fantasy concept art, highly detailed"
        elif character_id == "merchant":
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
            elif char.character_id == "player":
                filename = "player_avatar.png"
                player_desc = char.description or "A brave human specialist hero"
                prompt = f"A fantasy RPG hero, gender: {char.gender}, race: Human, class: Specialist, appearance: {player_desc}, fantasy concept art, highly detailed"
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
