import json

extracted_path = r"d:\hcmus\HK4\Tư duy tính toán cho TTNT\final\aistoryadventure\scratch\extracted_steps.txt"
with open(extracted_path, 'r', encoding='utf-8') as f:
    steps = json.load(f)

for step in steps:
    idx = step["step_index"]
    for tc in step.get("tool_calls", []):
        args = tc.get("args", {})
        rep = args.get("ReplacementContent", "")
        if rep:
            out_file = f"d:/hcmus/HK4/Tư duy tính toán cho TTNT/final/aistoryadventure/scratch/rep_{idx}.txt"
            with open(out_file, 'w', encoding='utf-8') as out_f:
                out_f.write(rep)
