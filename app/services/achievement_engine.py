from typing import List, Dict, Any
from app.domain.rpg_models import RPGGameState

ACHIEVEMENTS_CONFIG = {
    "billionaire": {
        "name": "Tỷ phú giàu nhất lục địa",
        "description": "Tích lũy đạt 10,000 vàng.",
        "target": 10000,
        "progress_field": "gold_accumulated",
    },
    "bounty_hunter": {
        "name": "Thợ săn tiền thưởng đỉnh cao",
        "description": "Hoàn thành 300 nhiệm vụ.",
        "target": 300,
        "progress_field": "quests_completed",
    },
    "butcher": {
        "name": "Kẻ đồ tể",
        "description": "Tiêu diệt (kết liễu) 500 Kẻ lạ mặt.",
        "target": 500,
        "progress_field": "strangers_killed",
    },
    "silver_warrior": {
        "name": "Dũng sĩ giáp bạc",
        "description": "Tiêu diệt 50 BOSS Elite 1.",
        "target": 50,
        "progress_field": "elite1_defeated",
    },
    "gold_knight": {
        "name": "Hiệp sĩ giáp vàng",
        "description": "Tiêu diệt 20 BOSS Elite 2.",
        "target": 20,
        "progress_field": "elite2_defeated",
    },
    "epic_hero": {
        "name": "Anh hùng sử thi",
        "description": "Tiêu diệt 1 Final BOSS Alpha.",
        "target": 1,
        "progress_field": "final_boss_defeated",
    },
    "chatterbox": {
        "name": "Kẻ nhiều chuyện",
        "description": "Nói chuyện 1000 lần với tu sĩ, thương nhân, kẻ lạ mặt.",
        "target": 1000,
        "progress_field": "conversations",
    },
    "nomad": {
        "name": "Kẻ du mục",
        "description": "Di chuyển giữa các khu vực địa hình 300 lần.",
        "target": 300,
        "progress_field": "travels",
    },
    "savior": {
        "name": "Thánh nhân cứu rỗi",
        "description": "Tha bổng cho Kẻ lạ mặt sau khi đánh bại 500 lần.",
        "target": 500,
        "progress_field": "strangers_spared",
    }
}

class AchievementEngine:
    @staticmethod
    def initialize_progress() -> Dict[str, Any]:
        """Initializes empty achievements progress dictionary."""
        return {
            "gold_accumulated": 0,
            "quests_completed": 0,
            "strangers_killed": 0,
            "elite1_defeated": 0,
            "elite2_defeated": 0,
            "final_boss_defeated": 0,
            "conversations": 0,
            "travels": 0,
            "strangers_spared": 0,
            "unlocked": []
        }

    @staticmethod
    def update_progress(rpg_state: RPGGameState, field: str, amount: int = 1) -> List[str]:
        """
        Increments achievement progress field and checks for unlocks.
        Returns list of notification strings for unlocked achievements.
        """
        progress = rpg_state.achievements_progress
        if not progress:
            progress = AchievementEngine.initialize_progress()
            rpg_state.achievements_progress = progress
            
        if "unlocked" not in progress:
            progress["unlocked"] = []
            
        if field in progress:
            progress[field] += amount
        else:
            progress[field] = amount
            
        # Also special case: billionaire can check current gold directly
        if field == "gold_accumulated" and rpg_state.inventory:
            # Keep gold_accumulated as cumulative gold OR maximum gold held
            progress["gold_accumulated"] = max(progress["gold_accumulated"], rpg_state.inventory.gold)

        notifications = []
        for key, config in ACHIEVEMENTS_CONFIG.items():
            if key in progress["unlocked"]:
                continue
                
            field_name = config["progress_field"]
            current_value = progress.get(field_name, 0)
            target = config["target"]
            
            if current_value >= target:
                progress["unlocked"].append(key)
                notifications.append(
                    f"🏆 ĐÃ MỞ KHÓA DANH HIỆU: \"{config['name']}\" ({config['description']})!"
                )
                
        return notifications

    @staticmethod
    def get_achievements_list(rpg_state: RPGGameState) -> List[Dict[str, Any]]:
        """Returns the list of achievements with their current progress and unlocked status."""
        progress = rpg_state.achievements_progress
        if not progress:
            progress = AchievementEngine.initialize_progress()
            
        unlocked = progress.get("unlocked", [])
        result = []
        for key, config in ACHIEVEMENTS_CONFIG.items():
            field_name = config["progress_field"]
            current_value = progress.get(field_name, 0)
            result.append({
                "id": key,
                "name": config["name"],
                "description": config["description"],
                "target": config["target"],
                "current": current_value,
                "unlocked": key in unlocked
            })
        return result
