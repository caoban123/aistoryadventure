import json

log_path = r"C:\Users\Admin\.gemini\antigravity\brain\ad58124c-a7df-432e-bd9c-d8434358287d\.system_generated\logs\transcript.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    for line in f:
        try:
            step = json.loads(line)
            if "tool_calls" in step and step["tool_calls"]:
                for tc in step["tool_calls"]:
                    name = tc.get("name")
                    args = tc.get("args") or {}
                    target = args.get("TargetFile", "")
                    if "rpg_service.py" in target:
                        print(f"Step: {step.get('step_index')}, Tool: {name}")
                        desc = args.get("Description") or args.get("Instruction") or ""
                        print(f"  Info: {desc[:150]}")
        except Exception as e:
            pass
