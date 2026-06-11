import asyncio
import sys
from app.domain.rpg_models import RPGCharacter, RPGCharacterStats, RPGGameState
from app.services.rpg_engine import RPGEngine
from app.services.rpg_service import RPGService

# Set output encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

async def test_max_levels():
    print("--- TESTING DYNAMIC MAX LEVELS ---")
    
    # 1. Player Character
    player = RPGCharacter(
        character_id="player",
        name="User Player",
        race="Human",
        char_class="Guard",
        rarity="Common",
        is_player_character=True
    )
    print(f"Player Character (is_player_character=True) Max Level: {player.max_level} (Expected: 99)")
    assert player.max_level == 99
    
    player2 = RPGCharacter(
        character_id="player",
        name="User Player 2",
        race="Human",
        char_class="Guard",
        rarity="Common",
        is_player_character=False
    )
    print(f"Player Character (character_id='player') Max Level: {player2.max_level} (Expected: 99)")
    assert player2.max_level == 99

    # 2. Companion / Enemies Max Levels by Rarity
    rarities = {
        "Mythic": 90,
        "Legendary": 80,
        "Epic": 70,
        "Rare": 60,
        "Uncommon": 55,
        "Common": 50
    }
    for rarity, expected_lvl in rarities.items():
        comp = RPGCharacter(
            character_id="companion_123",
            name=f"Comp {rarity}",
            race="Elf",
            char_class="Caster",
            rarity=rarity
        )
        print(f"Companion Rarity {rarity} Max Level: {comp.max_level} (Expected: {expected_lvl})")
        assert comp.max_level == expected_lvl
        
    print("Dynamic max level checks passed!\n")

async def test_boss_stats_preservation():
    print("--- TESTING BOSS STATS PRESERVATION ---")
    
    # Create a boss with custom base stats (Medusa max_hp = 500)
    medusa = RPGCharacter(
        character_id="medusa_boss",
        name="Medusa",
        race="Bí ẩn",
        char_class="Bí ẩn",
        rarity="Epic"
    )
    medusa.stats.max_hp = 500
    medusa.stats.hp = 500
    medusa.stats.atk = 80
    medusa.stats.defense = 40
    medusa.stats.res = 100
    medusa.stats.res_def = 60
    medusa.stats.atk_spd = 90
    medusa.base_stats = medusa.stats.model_copy()
    
    # Recalculate stats using calculate_current_stats
    stats_after_calc = RPGEngine.calculate_current_stats(medusa)
    print(f"Medusa Max HP after recalculation: {stats_after_calc.max_hp} (Expected: 500)")
    assert stats_after_calc.max_hp == 500
    
    # Check sync_character_stats
    RPGEngine.sync_character_stats(medusa, 1)
    print(f"Medusa HP / Max HP after sync: {medusa.stats.hp} / {medusa.stats.max_hp} (Expected: 500 / 500)")
    assert medusa.stats.max_hp == 500
    assert medusa.stats.hp == 500
    
    print("Boss stats preservation check passed!\n")

async def main():
    try:
        await test_max_levels()
        await test_boss_stats_preservation()
        print("All automated tests completed successfully!")
    except AssertionError as e:
        print("TEST FAILED: Assertion Error", e)
    except Exception as e:
        print("TEST FAILED: Unexpected Error", e)

if __name__ == "__main__":
    asyncio.run(main())
