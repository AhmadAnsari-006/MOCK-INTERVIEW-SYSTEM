from typing import Any, Dict, List


def build_final_feedback(per_question: List[Dict[str, Any]]) -> Dict[str, Any]:
    strengths: List[str] = []
    weaknesses: List[str] = []

    for pq in per_question:
        strengths.extend(pq.get("matched_keywords") or [])
        weaknesses.extend(pq.get("missing_keywords") or [])

    strengths = _dedupe_preserve_order(strengths)[:10]
    weaknesses = _dedupe_preserve_order(weaknesses)[:10]

    suggestions: List[str] = []
    for kw in weaknesses[:5]:
        suggestions.append(f"Revise and practice explaining: {kw}")

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "suggestions": suggestions,
    }


def summarize_score(average_score_10: float) -> str:
    if average_score_10 >= 8:
        return "🔥 Excellent! Strong understanding and clarity."
    if average_score_10 >= 5:
        return "👍 Decent performance. Improve depth and structure."
    return "⚠️ Weak fundamentals. Focus on core concepts."


def _dedupe_preserve_order(items: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for it in items:
        key = (it or "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
    return out
