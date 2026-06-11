import os

scratch_dir = "d:/hcmus/HK4/Tư duy tính toán cho TTNT/final/aistoryadventure/scratch"
keywords = ["chủng tộc", "race", "tỷ lệ", "stranger", "người lạ", "dungeon", "hầm ngục", "victoria", "londinium", "long kinh thành", "chúa quỷ", "mùa đông", "light heavens", "tự do"]

out_file = os.path.join(scratch_dir, "matched_rules.txt")
with open(out_file, 'w', encoding='utf-8') as out_f:
    for filename in os.listdir(scratch_dir):
        if filename.endswith("_pdf.txt"):
            filepath = os.path.join(scratch_dir, filename)
            out_f.write(f"\n=================== {filename} ===================\n")
            with open(filepath, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            for i, line in enumerate(lines):
                # Check if any keyword matches
                if any(kw in line.lower() for kw in keywords):
                    # Write context: 3 lines before and 3 lines after
                    start = max(0, i - 3)
                    end = min(len(lines), i + 4)
                    out_f.write(f"--- Line {i+1} ---\n")
                    for j in range(start, end):
                        out_f.write(f"{j+1}: {lines[j]}")
                    out_f.write("\n")

print("Done searching rules!")
