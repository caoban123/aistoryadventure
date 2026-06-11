import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    # Read HTML file
    with open('frontend/index.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
        
    # Read JS file
    with open('frontend/rpg_app.js', 'r', encoding='utf-8') as f:
        js_content = f.read()
        
    # Find all IDs in HTML
    # Matches id="something" or id='something'
    html_ids = set(re.findall(r'\bid=["\']([^"\']+)["\']', html_content))
    print(f"Total IDs found in index.html: {len(html_ids)}")
    
    # Find all document.getElementById("something") in JS
    js_get_element_ids = set(re.findall(r'document\.getElementById\(\s*["\']([^"\']+)["\']\s*\)', js_content))
    print(f"Total document.getElementById IDs in rpg_app.js: {len(js_get_element_ids)}")
    
    missing_ids = []
    for jid in js_get_element_ids:
        # Ignore dynamically generated IDs or patterns (none should be in literal getElementById though)
        if jid not in html_ids:
            # Let's see if this ID is accessed without check
            # Find lines in JS containing getElementById("jid")
            pattern = r'document\.getElementById\(\s*["\']' + re.escape(jid) + r'["\']\s*\)'
            for i, line in enumerate(js_content.splitlines(), 1):
                if re.search(pattern, line):
                    # Check if there is an safety guard, e.g., if (el) or if (el === null) etc.
                    # We will print it for manual inspection
                    missing_ids.append((jid, i, line.strip()))
                    
    if missing_ids:
        print("\n❌ Found document.getElementById for IDs that do not exist in index.html:")
        for jid, line_num, line in sorted(missing_ids, key=lambda x: x[1]):
            print(f"  Line {line_num}: ID '{jid}' -> `{line}`")
    else:
        print("\n✅ All document.getElementById targets exist in index.html.")

if __name__ == '__main__':
    main()
