import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    with open('frontend/rpg_app.js', 'r', encoding='utf-8') as f:
        js = f.read()
        
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        html = f.read()
        
    # Matches document.querySelector(...) or document.querySelectorAll(...)
    queries = re.findall(r'document\.querySelector(All)?\(\s*["\']([^"\']+)["\']\s*\)', js)
    print(f"Total querySelector/querySelectorAll calls in JS: {len(queries)}")
    
    # Check each query selector
    for is_all, selector in queries:
        # Check if selector looks like ID or Class or tag
        # e.g., #rpgMapArea, .rpg-gender-btn, etc.
        print(f"Selector: {selector} (All: {bool(is_all)})")
        
        # Let's verify if there is at least one match in index.html for class/id
        if selector.startswith('#'):
            target_id = selector[1:]
            if target_id not in html:
                print(f"  ❌ ID '{target_id}' not found in HTML!")
        elif selector.startswith('.'):
            target_class = selector[1:]
            if target_class not in html:
                print(f"  ❌ Class '{target_class}' not found in HTML!")
        else:
            # tag name or complex selector, just print it
            pass

if __name__ == '__main__':
    main()
