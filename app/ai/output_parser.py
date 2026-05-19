from __future__ import annotations

import json
import re
from typing import Any

def parse_story_output(raw_text: str) -> dict[str, Any]:
    text = (raw_text or "").strip()
    data = _try_parse_json(text)
    if not isinstance(data, dict):
        data = {}

    story = _clean_text(data.get("story")) or _fallback_story(text)
    foundation = _clean_text(data.get("foundation"))
    choices = _normalize_choices(data.get("choices"))
    survival_update = _normalize_survival_update(data.get("survival_update"))

    return {
        "foundation": foundation,
        "story": story,
        "choices": choices,
        "survival_update": survival_update,
    }

def _try_parse_json(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        pass

    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.S | re.I)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except Exception:
            pass

    obj = re.search(r"\{.*\}", text, flags=re.S)
    if obj:
        try:
            return json.loads(obj.group(0))
        except Exception:
            pass

    return None

def _clean_text(value: Any) -> str:
    return value.strip() if isinstance(value, str) else ""

def _normalize_choices(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    choices: list[str] = []
    for item in value:
        if not isinstance(item, str):
            continue
        text = re.sub(r"^\s*[-*\d.)]+\s*", "", item).strip()
        if 3 <= len(text) <= 220:
            choices.append(text)
    return list(dict.fromkeys(choices))[:4]

def _normalize_survival_update(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}

    allowed = {
        "danger",
        "supplies",
        "wounds",
        "time_pressure",
        "objective",
        "threat",
        "region",
        "loadout",
        "last_survival_note",
    }
    cleaned: dict[str, Any] = {}

    for key, item in value.items():
        if key not in allowed:
            continue

        if key in {"danger", "supplies", "wounds", "time_pressure"}:
            try:
                cleaned[key] = max(0, min(5, int(item)))
            except (TypeError, ValueError):
                continue
            continue

        if isinstance(item, str):
            text = item.strip()
            if text:
                cleaned[key] = text[:500]

    return cleaned

def _fallback_story(text: str) -> str:
    text = re.sub(r"```(?:json)?", "", text, flags=re.I).replace("```", "").strip()
    return text or "Không có phản hồi từ AI."
