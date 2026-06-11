import json

log_path = r"C:\Users\Admin\.gemini\antigravity\brain\ad58124c-a7df-432e-bd9c-d8434358287d\.system_generated\logs\transcript.jsonl"
out_path = r"d:\hcmus\HK4\Tư duy tính toán cho TTNT\final\aistoryadventure\scratch\extracted_steps.txt"

target_steps = [1996, 2002]

results = []
with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            step = json.loads(line)
            idx = step.get("step_index")
            if idx in target_steps:
                results.append(step)
        except Exception as e:
            pass

with open(out_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(results)} steps to {out_path}")
