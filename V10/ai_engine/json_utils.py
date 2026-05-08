from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional


_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json_candidate(text: str) -> str:
    t = (text or "").strip()
    if not t:
        return ""

    m = _FENCE_RE.search(t)
    if m:
        return (m.group(1) or "").strip()

    # best-effort: find first {...} block
    start = t.find("{")
    end = t.rfind("}")
    if start != -1 and end != -1 and end > start:
        return t[start : end + 1].strip()

    return t


def parse_json_strict(text: str) -> Dict[str, Any]:
    candidate = _extract_json_candidate(text)
    try:
        obj = json.loads(candidate)
    except Exception as e:
        raise RuntimeError(f"LLM did not return valid JSON. Raw: {text[:500]}") from e
    if not isinstance(obj, dict):
        raise RuntimeError(f"LLM JSON is not an object. Raw: {text[:500]}")
    return obj


def build_json_instruction(schema_hint: Optional[str]) -> str:
    if not schema_hint:
        return "Return ONLY valid JSON."
    return f"Return ONLY valid JSON. Schema: {schema_hint}"

