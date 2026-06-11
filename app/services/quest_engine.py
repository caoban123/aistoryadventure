import random
import uuid
from typing import Any, List, Dict
from app.domain.rpg_models import RPGGameState, RPGCharacter

class QuestEngine:
    @staticmethod
    def generate_initial_quests(rpg_state: RPGGameState) -> List[Dict[str, Any]]:
        """Generates 6 active quests, one from each category."""
        quests = []
        for cat in range(1, 7):
            quests.append(QuestEngine.generate_quest_for_category(cat, rpg_state))
        return quests

    @staticmethod
    def generate_quest_for_category(category: int, rpg_state: RPGGameState) -> Dict[str, Any]:
        """Generates a random quest for a specific category (1-6)."""
        quest_id = str(uuid.uuid4())
        completed = False
        current = 0
        
        # Default fallback values
        quest_type = "unknown"
        description = "Nhiệm vụ kỳ bí"
        target = 1
        gold_reward = 10
        exp_reward = 5
        meta = {}

        if category == 1:
            # Level Quests: Player Level vs Party Level
            option = random.choice(["player_level", "party_level"])
            if option == "player_level" and rpg_state.player_character:
                current_level = rpg_state.player_character.level
                max_lvl = rpg_state.player_character.max_level
                x = min(5, max(1, max_lvl - current_level))
                target_level = current_level + x
                
                quest_type = "player_level"
                description = f"Tăng thêm {x} level cho nhân vật chính để đạt level {target_level}."
                target = target_level
                current = current_level
                gold_reward = target_level
                exp_reward = int(target_level / 2)
                meta = {"type": "player_level", "target_level": target_level}
            else:
                # Party Level: n members reach level L
                # L in [20, 30, 40, 50, 60, 80, 90]
                # n in [2, 3, 4]
                L_candidates = [20, 30, 40, 50, 60, 80, 90]
                n_candidates = [2, 3, 4]
                
                # Filter candidates that are not met yet
                valid_combinations = []
                party_members = rpg_state.party.active
                for L_val in L_candidates:
                    for n_val in n_candidates:
                        met_count = sum(1 for c in party_members if c.level >= L_val)
                        if met_count < n_val:
                            valid_combinations.append((L_val, n_val))
                
                if valid_combinations:
                    L, n = random.choice(valid_combinations)
                else:
                    L, n = 90, 4
                
                quest_type = "party_level"
                description = f"Có ít nhất {n} thành viên trong đội đạt level >= {L}."
                target = n
                current = sum(1 for c in party_members if c.level >= L)
                gold_reward = n * L
                exp_reward = int((n * L) / 2)
                meta = {"type": "party_level", "level_limit": L, "required_count": n}

        elif category == 2:
            # Defeat Quests
            sub_type = random.choice(["Goblin", "Orc", "Devil", "Elite1", "Elite2", "Alpha"])
            if sub_type == "Goblin":
                n = random.randint(5, 20)
                quest_type = "defeat_goblin"
                description = f"Tiêu diệt {n} Goblin trong chiến đấu."
                target = n
                gold_reward = n * 5
                exp_reward = int((n * 5) / 2)
                meta = {"type": "defeat", "race": "Goblin"}
            elif sub_type == "Orc":
                n = random.randint(3, 10)
                quest_type = "defeat_orc"
                description = f"Tiêu diệt {n} Orc trong chiến đấu."
                target = n
                gold_reward = n * 15
                exp_reward = int((n * 15) / 2)
                meta = {"type": "defeat", "race": "Orc"}
            elif sub_type == "Devil":
                n = random.randint(1, 5)
                quest_type = "defeat_devil"
                description = f"Tiêu diệt {n} Devil trong chiến đấu."
                target = n
                gold_reward = n * 60
                exp_reward = int((n * 60) / 2)
                meta = {"type": "defeat", "race": "Devil"}
            elif sub_type == "Elite1":
                quest_type = "defeat_elite1"
                description = "Tiêu diệt 1 BOSS Elite 1 bất kỳ (Medusa, Golem, Werewolf, Dracula, Vua Goblin)."
                target = 1
                gold_reward = 200
                exp_reward = 150
                meta = {"type": "defeat", "category": "Elite1"}
            elif sub_type == "Elite2":
                quest_type = "defeat_elite2"
                description = "Tiêu diệt 1 BOSS Elite 2 bất kỳ (Poseidon, Diablo, Thiên Dực Long Vương, Ma vương Xương Cốt)."
                target = 1
                gold_reward = 500
                exp_reward = 400
                meta = {"type": "defeat", "category": "Elite2"}
            elif sub_type == "Alpha":
                quest_type = "defeat_alpha"
                description = "Tiêu diệt Trùm Cuối Alpha để giải phóng lục địa."
                target = 1
                gold_reward = 1000
                exp_reward = 800
                meta = {"type": "defeat", "category": "Alpha"}

        elif category == 3:
            # Recruitment Quests
            race = random.choice(["Royalty", "Elf", "Devil", "Angel", "Valkyrie"])
            n = random.randint(1, 5)
            if race == "Royalty":
                gold_reward = n * 20
            elif race == "Elf":
                gold_reward = n * 30
            elif race == "Devil":
                gold_reward = n * 40
            elif race == "Angel":
                gold_reward = n * 40
            else: # Valkyrie
                gold_reward = n * 60
                
            quest_type = f"recruit_{race.lower()}"
            description = f"Chiêu mộ thành công {n} đồng minh tộc {race} vào đội."
            target = n
            exp_reward = int(gold_reward / 2)
            meta = {"type": "recruit", "race": race}

        elif category == 4:
            # Trade Quests
            option = random.choice(["sell", "buy"])
            if option == "sell":
                n = random.choice([100, 300, 500, 700, 1000])
                quest_type = "sell_items"
                description = f"Bán vật phẩm đạt tích lũy {n} vàng tại Thương nhân."
                target = n
                gold_reward = int(n * 0.3)
                exp_reward = int(gold_reward / 2)
                meta = {"type": "sell_gold"}
            else:
                rarity = random.choice(["Rare", "Epic", "Legendary", "Mythic"])
                n = random.randint(1, 5)
                if rarity == "Rare":
                    gold_reward = n * 20
                elif rarity == "Epic":
                    gold_reward = n * 30
                elif rarity == "Legendary":
                    gold_reward = n * 40
                else: # Mythic
                    gold_reward = n * 60
                
                quest_type = f"buy_{rarity.lower()}"
                description = f"Mua {n} vật phẩm độ hiếm {rarity} từ Thương nhân."
                target = n
                exp_reward = int(gold_reward / 2)
                meta = {"type": "buy_item", "rarity": rarity}

        elif category == 5:
            # Talk/Meeting Quests
            option = random.choice([
                ("talk_merchant", "Nói chuyện với thương nhân", "talk", "merchant", 10),
                ("talk_monk", "Nói chuyện với tu sĩ", "talk", "monk", 10),
                ("talk_stranger", "Nói chuyện với Kẻ lạ mặt bất kỳ", "talk", "stranger", 15),
                ("meet_merchant", "Chọn tiến tới gặp thương nhân", "meet", "merchant", 20),
                ("meet_monk", "Chọn tiến tới gặp tu sĩ", "meet", "monk", 20),
                ("meet_stranger", "Chọn tiến tới gặp Kẻ lạ mặt", "meet", "stranger", 15)
            ])
            
            n = random.randint(1, 5)
            q_type_name, q_desc_base, action, target_npc, gold_multiplier = option
            
            quest_type = q_type_name
            description = f"{q_desc_base} đủ {n} lần."
            target = n
            gold_reward = n * gold_multiplier
            exp_reward = int(gold_reward / 2)
            meta = {"type": action, "target": target_npc}

        elif category == 6:
            # Collect Items Quests
            rarity = random.choice(["Rare", "Epic", "Legendary", "Mythic"])
            if rarity == "Mythic":
                n = random.randint(1, 5)
                gold_reward = n * 60
            else:
                n = random.randint(1, 10)
                if rarity == "Rare":
                    gold_reward = n * 10
                elif rarity == "Epic":
                    gold_reward = n * 20
                else: # Legendary
                    gold_reward = n * 40
            
            quest_type = f"collect_{rarity.lower()}"
            description = f"Thu thập được {n} vật phẩm độ hiếm {rarity} từ bất cứ nguồn nào."
            target = n
            exp_reward = int(gold_reward / 2)
            meta = {"type": "collect", "rarity": rarity}

        return {
            "quest_id": quest_id,
            "category": category,
            "quest_type": quest_type,
            "description": description,
            "target": target,
            "current": current,
            "gold_reward": gold_reward,
            "exp_reward": exp_reward,
            "completed": completed,
            "meta": meta
        }

    @staticmethod
    def update_quest_progress(rpg_state: RPGGameState, event_type: str, data: Dict[str, Any]) -> List[str]:
        """
        Updates active quests progress based on game events.
        event_type can be:
        - "level_up" (data: {"char_id": str, "level": int})
        - "defeat" (data: {"race": str, "is_boss": bool, "boss_category": str}) (boss_category: Elite1, Elite2, Alpha)
        - "recruit" (data: {"race": str})
        - "sell_gold" (data: {"gold": int})
        - "buy_item" (data: {"rarity": str})
        - "talk" (data: {"target": str}) (merchant, monk, stranger)
        - "meet" (data: {"target": str})
        - "collect" (data: {"rarity": str})
        
        Returns a list of notification strings for completed quests.
        """
        notifications = []
        for quest in rpg_state.active_quests:
            if quest.get("completed"):
                continue
                
            meta = quest.get("meta", {})
            q_type = meta.get("type")
            target = quest.get("target", 1)
            
            if event_type == "level_up" and q_type == "player_level":
                # Check if it is the player character
                if data.get("char_id") == rpg_state.player_character.character_id:
                    quest["current"] = data.get("level", quest["current"])
                    
            elif event_type == "level_up" and q_type == "party_level":
                limit = meta.get("level_limit", 20)
                party_members = rpg_state.party.active
                quest["current"] = sum(1 for c in party_members if c.level >= limit)
                
            elif event_type == "defeat" and q_type == "defeat":
                # Check match by race
                if "race" in meta and data.get("race") == meta["race"]:
                    quest["current"] += 1
                # Check match by boss category
                elif "category" in meta and data.get("boss_category") == meta["category"]:
                    quest["current"] += 1
                    
            elif event_type == "recruit" and q_type == "recruit":
                if data.get("race") == meta.get("race"):
                    quest["current"] += 1
                    
            elif event_type == "sell_gold" and q_type == "sell_gold":
                quest["current"] += data.get("gold", 0)
                
            elif event_type == "buy_item" and q_type == "buy_item":
                if data.get("rarity") == meta.get("rarity"):
                    quest["current"] += 1
                    
            elif event_type == "talk" and q_type == "talk":
                if data.get("target") == meta.get("target"):
                    quest["current"] += 1
                    
            elif event_type == "meet" and q_type == "meet":
                if data.get("target") == meta.get("target"):
                    quest["current"] += 1
                    
            elif event_type == "collect" and q_type == "collect":
                if data.get("rarity") == meta.get("rarity"):
                    quest["current"] += 1
            
            # Check if quest completed
            if quest["current"] >= target:
                quest["current"] = target
                quest["completed"] = True
                
                # Give rewards
                g_reward = quest.get("gold_reward", 0)
                e_reward = quest.get("exp_reward", 0)
                rpg_state.inventory.gold += g_reward
                
                # Distribute EXP to all active party members
                party_members = rpg_state.party.active
                if party_members and e_reward > 0:
                    exp_per_member = max(1, int(e_reward / len(party_members)))
                    for char in party_members:
                        if char.level < char.max_level:
                            char.exp += exp_per_member
                            # Check level up
                            while char.exp >= char.level * 100 and char.level < char.max_level:
                                char.exp -= char.level * 100
                                char.level += 1
                                notifications.append(f"🎉 {char.name} đã thăng lên cấp {char.level}!")
                                # If player character levels up, trigger another check
                                if char.character_id == rpg_state.player_character.character_id:
                                    # We will handle recursive checking afterwards or trigger it now
                                    pass
                                    
                # Add quest completion count to achievements progress
                progress = rpg_state.achievements_progress
                progress["quests_completed"] = progress.get("quests_completed", 0) + 1
                
                notifications.append(
                    f"🏆 Đã hoàn thành nhiệm vụ: \"{quest.get('description')}\"! Nhận +{g_reward} vàng và +{e_reward} EXP!"
                )
                
        return notifications
