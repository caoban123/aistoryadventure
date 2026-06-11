import os

filepath = "d:/hcmus/HK4/Tư duy tính toán cho TTNT/final/aistoryadventure/scratch/world_map_pdf.txt"
out_path = "d:/hcmus/HK4/Tư duy tính toán cho TTNT/final/aistoryadventure/scratch/all_distributions.txt"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Write lines 1900 to 3200 to out_path
with open(out_path, 'w', encoding='utf-8') as out_f:
    for i in range(1900, 3200):
        if i < len(lines):
            out_f.write(f"{i+1}: {lines[i]}")

print("Done extracting distributions text!")
