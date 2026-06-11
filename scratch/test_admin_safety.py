import requests
import json

BASE_URL = "http://127.0.0.1:8002"
HEADERS = {
    "Authorization": "Bearer guest",
    "Content-Type": "application/json"
}

def test_safety_endpoints():
    print("--- TESTING SAFETY ENDPOINTS ---")
    
    # 1. GET /admin/safety/rules
    print("1. Fetching safety rules...")
    r = requests.get(f"{BASE_URL}/admin/safety/rules", headers=HEADERS)
    print("   Status Code:", r.status_code)
    assert r.status_code == 200, f"Failed: {r.text}"
    rules = r.json()
    print("   Categories in rules:", list(rules.keys()))
    print("   Vulgarity sample rule count:", len(rules.get("vulgarity", [])))
    
    # 2. POST /admin/safety/test (Safe text)
    print("\n2. Testing safe text...")
    payload_safe = {"text": "Xin chào thế giới! Đây là một câu chuyện phiêu lưu rất thú vị."}
    r = requests.post(f"{BASE_URL}/admin/safety/test", json=payload_safe, headers=HEADERS)
    print("   Status Code:", r.status_code)
    assert r.status_code == 200, f"Failed: {r.text}"
    res_safe = r.json()
    print("   Response:", json.dumps(res_safe, indent=2, ensure_ascii=False))
    assert res_safe["safe"] is True
    assert res_safe["was_censored"] is False
    
    # 3. POST /admin/safety/test (Banned / vulgar text)
    print("\n3. Testing vulgar text...")
    payload_vulgar = {"text": "Thằng đó đm thật là láo toét!"}
    r = requests.post(f"{BASE_URL}/admin/safety/test", json=payload_vulgar, headers=HEADERS)
    print("   Status Code:", r.status_code)
    assert r.status_code == 200, f"Failed: {r.text}"
    res_vulgar = r.json()
    print("   Response:", json.dumps(res_vulgar, indent=2, ensure_ascii=False))
    assert res_vulgar["safe"] is False
    assert "[Nội dung đã được lược bỏ để đảm bảo an toàn]" in res_vulgar["censored_result"]
    
    print("\nAll safety dashboard API endpoints tested successfully!")

if __name__ == "__main__":
    test_safety_endpoints()
