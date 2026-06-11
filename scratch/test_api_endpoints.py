import requests
import sys

# Set output encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {
    "Authorization": "Bearer guest",
    "Content-Type": "application/json"
}

def test_api_flow():
    print("--- STARTING API INTEGRATION TESTS ---")
    
    # 1. Start game
    print("1. Starting RPG Game...")
    start_payload = {
        "player_name": "Antigravity Test Player",
        "gender": "Male"
    }
    r = requests.post(f"{BASE_URL}/game/rpg/start", json=start_payload, headers=HEADERS)
    assert r.status_code == 200, f"Failed to start game: {r.text}"
    start_data = r.json()
    session_id = start_data["session_id"]
    print(f"   Success! Session ID: {session_id}")
    
    # 2. Start story narrative
    print("2. Starting Adventure Story...")
    r = requests.post(f"{BASE_URL}/game/rpg/start-story?session_id={session_id}", headers=HEADERS)
    assert r.status_code == 200, f"Failed to start story: {r.text}"
    story_data = r.json()
    print("   Success! Story started.")
    
    # 3. Give gold to player using debug command
    print("3. Adding gold via debug command...")
    debug_payload = {
        "session_id": session_id,
        "command": "gain_gold_1000"
    }
    r = requests.post(f"{BASE_URL}/game/rpg/debug/command", json=debug_payload, headers=HEADERS)
    assert r.status_code == 200, f"Debug command failed: {r.text}"
    rpg_state = r.json()["rpg_state"]
    print(f"   Success! Player gold: {rpg_state['inventory']['gold']}")
    assert rpg_state['inventory']['gold'] >= 1000
    
    # 4. Test Fast Travel API
    # "Hoang mạc" has major: "Thành Phố Tự Do"
    print("4. Testing Fast Travel to 'Thành Phố Tự Do'...")
    travel_payload = {
        "session_id": session_id,
        "target_region": "Thành Phố Tự Do"
    }
    r = requests.post(f"{BASE_URL}/game/rpg/fast-travel", json=travel_payload, headers=HEADERS)
    assert r.status_code == 200, f"Fast travel failed: {r.text}"
    travel_data = r.json()
    rpg_state = travel_data["rpg_state"]
    print(f"   Success! Fast traveled. Env: {rpg_state['environment']}, Region: {rpg_state['current_region']}")
    assert rpg_state['environment'] == "Hoang mạc"
    assert rpg_state['current_region'] == "Thành Phố Tự Do"

    # 5. Test Leave Region API
    print("5. Testing Leave Region endpoint...")
    leave_payload = {
        "session_id": session_id
    }
    r = requests.post(f"{BASE_URL}/game/rpg/leave-region", json=leave_payload, headers=HEADERS)
    assert r.status_code == 200, f"Leave region endpoint failed: {r.text}"
    leave_data = r.json()
    rpg_state = leave_data["rpg_state"]
    print(f"   Success! Left region. Current Region: {rpg_state['current_region']} (Expected: None)")
    assert rpg_state['current_region'] is None
    
    # 6. Test Combat with Medusa (Elite 1 Boss) and HP preservation
    print("6. Testing Medusa Combat encounter...")
    debug_payload["command"] = "boss_e1_medusa_combat"
    r = requests.post(f"{BASE_URL}/game/rpg/debug/command", json=debug_payload, headers=HEADERS)
    assert r.status_code == 200, f"Failed to start Medusa combat: {r.text}"
    combat_data = r.json()
    rpg_state = combat_data["rpg_state"]
    combat_state = rpg_state["combat"]
    assert combat_state is not None
    assert combat_state["is_active"] is True
    enemy = combat_state["enemy"]
    print(f"   Enemy Name: {enemy['name']}, Race: {enemy['race']}, Class: {enemy['char_class']}")
    print(f"   Enemy Max HP: {enemy['stats']['max_hp']} (Expected: 500)")
    assert enemy["name"] == "Medusa"
    assert enemy["race"] == "Bí ẩn"
    assert enemy["char_class"] == "Bí ẩn"
    assert enemy["stats"]["max_hp"] == 500
    
    # 7. Defeat Medusa via combat_kill
    print("7. Defeating Medusa via combat_kill...")
    debug_payload["command"] = "combat_kill"
    r = requests.post(f"{BASE_URL}/game/rpg/debug/command", json=debug_payload, headers=HEADERS)
    assert r.status_code == 200, f"Failed to run combat_kill: {r.text}"
    kill_data = r.json()
    is_combat_over = kill_data.get("is_combat_over", False)
    result = kill_data.get("result")
    print(f"   Combat Over: {is_combat_over}, Result: {result}")
    assert is_combat_over is True
    assert result == "win"
    
    # 8. Test Combat with Alpha (Final Boss)
    print("8. Testing Alpha Combat encounter...")
    debug_payload["command"] = "final_boss_combat"
    r = requests.post(f"{BASE_URL}/game/rpg/debug/command", json=debug_payload, headers=HEADERS)
    assert r.status_code == 200, f"Failed to start Alpha combat: {r.text}"
    combat_data = r.json()
    rpg_state = combat_data["rpg_state"]
    combat_state = rpg_state["combat"]
    assert combat_state is not None
    assert combat_state["is_active"] is True
    enemy = combat_state["enemy"]
    print(f"   Enemy Name: {enemy['name']}, Race: {enemy['race']}, Class: {enemy['char_class']}")
    print(f"   Enemy Max HP: {enemy['stats']['max_hp']} (Expected: 2000)")
    assert enemy["name"] == "Alpha"
    assert enemy["race"] == "Bí ẩn"
    assert enemy["char_class"] == "Bí ẩn"
    # Alpha's HP is scaled by player level (starts at 2000, scaled upwards)
    assert enemy["stats"]["max_hp"] >= 2000
    
    # 9. Test combat_kill debug command on Alpha
    print("9. Defeating Alpha via combat_kill...")
    debug_payload["command"] = "combat_kill"
    r = requests.post(f"{BASE_URL}/game/rpg/debug/command", json=debug_payload, headers=HEADERS)
    assert r.status_code == 200, f"Failed to run combat_kill on Alpha: {r.text}"
    kill_data = r.json()
    print("   Combat Over: True")
    print(f"   Story contains Ending choices: {len(kill_data['choices']) > 0}")
    assert len(kill_data["choices"]) > 0
    print(f"   Choices offered: {kill_data['choices']}")
    
    print("\nAll API integration tests passed successfully!")

if __name__ == "__main__":
    test_api_flow()
