import os
import json
import sys

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

transcript_path = r"C:\Users\Admin\.gemini\antigravity\brain\24a4b91c-8f3c-4270-a926-e0a5c32e5627\.system_generated\logs\transcript.jsonl"

if not os.path.exists(transcript_path):
    print("Transcript not found")
else:
    with open(transcript_path, "r", encoding="utf-8") as f:
        found_versions = []
        for line in f:
            try:
                data = json.loads(line)
                tool_calls = data.get("tool_calls", [])
                for call in tool_calls:
                    name = call.get("name")
                    args = call.get("args", {})
                    target = args.get("TargetFile") or args.get("Target") or ""
                    if "implementation_plan" in target:
                        c = args.get("CodeContent") or args.get("ReplacementContent") or str(args)
                        found_versions.append(c)
            except Exception as e:
                pass
        
        print(f"Total versions: {len(found_versions)}")
        # Print first 3 versions
        for idx in range(min(3, len(found_versions))):
            print(f"\n--- VERSION {idx} (length: {len(found_versions[idx])}) ---")
            print(found_versions[idx][:2500])
            print("----------------------")
