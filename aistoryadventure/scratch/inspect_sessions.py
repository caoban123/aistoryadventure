import asyncio
import sys
import json
from app.memory.firebase_store import FirebaseStore
from app.domain.rpg_models import RPGGameState

# Set output encoding to UTF-8
sys.stdout.reconfigure(encoding='utf-8')

async def main():
    store = FirebaseStore()
    if store.db:
        print("Connected to Firestore.")
        docs = store.db.collection("sessions").order_by("updated_at", direction="DESCENDING").limit(5).stream()
        for doc in docs:
            d = doc.to_dict()
            rpg_state = d.get("rpg_state", {})
            print(f"Session: {d.get('session_id')} - Title: {d.get('title')}")
            print(f"  Mode: {d.get('mode')}")
            print(f"  Gold: {rpg_state.get('inventory', {}).get('gold')}")
            print(f"  Items: {rpg_state.get('inventory', {}).get('items')}")
            print(f"  Combat Active: {bool(rpg_state.get('combat'))}")
    else:
        print("Firestore is not initialized. Checking local files.")
        path = store.local_dir
        for p in path.glob("*.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                session = data.get("session", {})
                rpg_state = session.get("rpg_state", {})
                print(f"File: {p.name} - Title: {session.get('title')}")
                print(f"  Gold: {rpg_state.get('inventory', {}).get('gold')}")
                print(f"  Items: {rpg_state.get('inventory', {}).get('items')}")
            except Exception as e:
                print(f"Error reading {p.name}: {e}")

if __name__ == "__main__":
    asyncio.run(main())
