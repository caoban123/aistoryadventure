import re

def main():
    js = open('frontend/rpg_app.js', encoding='utf-8').read()
    html = open('frontend/index.html', encoding='utf-8').read()
    
    # Check document.getElementById
    ids = re.findall(r'document\.getElementById\(\s*["\']([^"\']+)["\']\s*\)', js)
    missing_ids = []
    for tag_id in sorted(set(ids)):
        # Skip dynamic string patterns like `rpgStep${i}`
        if '$' in tag_id or '{' in tag_id:
            continue
        if f'id="{tag_id}"' not in html and f"id='{tag_id}'" not in html and f'id={tag_id}' not in html:
            missing_ids.append(tag_id)
            
    print(f"Checked {len(set(ids))} unique IDs.")
    if missing_ids:
        print("[FAIL] Missing IDs in HTML:")
        for m in missing_ids:
            print(f"  - {m}")
    else:
        print("[SUCCESS] No missing IDs found!")

if __name__ == '__main__':
    main()
