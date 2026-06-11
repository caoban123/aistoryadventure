import os
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from pypdf import PdfReader
except ImportError:
    print("pypdf is not installed yet")
    sys.exit(1)

pdf_files = {
    "Cơ chế bản đồ World map.pdf": "world_map_pdf.txt",
    "Cơ chế nhiệm vụ Quest và Achievements.pdf": "quests_achievements_pdf.txt",
    "Dungeon.pdf": "dungeon_pdf.txt",
    "Update 1-1.pdf": "update_1_1_pdf.txt",
    "WORLD LORE.pdf": "world_lore_pdf.txt"
}

update_dir = "update"
scratch_dir = "scratch"
os.makedirs(scratch_dir, exist_ok=True)

for pdf_name, txt_name in pdf_files.items():
    pdf_path = os.path.join(update_dir, pdf_name)
    txt_path = os.path.join(scratch_dir, txt_name)
    
    if not os.path.exists(pdf_path):
        print(f"File not found: {pdf_path}")
        continue
        
    print(f"Extracting {pdf_name} -> {txt_name}...")
    try:
        reader = PdfReader(pdf_path)
        text_content = []
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            text_content.append(f"--- PAGE {i+1} ---")
            text_content.append(text)
            
        full_text = "\n".join(text_content)
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        print(f"Successfully extracted {len(reader.pages)} pages to {txt_path}")
    except Exception as e:
        print(f"Error extracting {pdf_name}: {e}")
