import json
import os

path = r"d:\hcmus\HK4\Tư duy tính toán cho TTNT\aistoryadventure\gen-img.ipynb"
with open(path, "r", encoding="utf-8") as f:
    notebook = json.load(f)

cells = notebook.get("cells", [])
for i, cell in enumerate(cells):
    source_lines = cell.get("source", [])
    if isinstance(source_lines, str):
        source = source_lines
    else:
        source = "".join(source_lines)
    
    if "@app.post(\"/generate-world-theme\")" in source:
        print(f"CELL_INDEX: {i}")
        print("--- SOURCE ---")
        print(source)
        print("--------------")
