from __future__ import annotations

from typing import Any, Dict, List


def build_analytics_report(*, per_question: List[Dict[str, Any]]) -> Dict[str, Any]:
    strengths: List[str] = []
    weaknesses: List[str] = []

    rubric_totals: Dict[str, float] = {}
    rubric_counts: Dict[str, int] = {}

    for pq in per_question or []:
        strengths.extend(pq.get("matched_keywords") or [])
        weaknesses.extend(pq.get("missing_keywords") or [])
        rubric = pq.get("rubric") or {}
        if isinstance(rubric, dict):
            for k, v in rubric.items():
                try:
                    fv = float(v)
                except Exception:
                    continue
                rubric_totals[k] = rubric_totals.get(k, 0.0) + fv
                rubric_counts[k] = rubric_counts.get(k, 0) + 1

    def dedupe(xs: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for x in xs:
            key = (x or "").strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            out.append(x)
        return out

    strengths = dedupe(strengths)[:15]
    weaknesses = dedupe(weaknesses)[:15]

    rubric_avgs = {
        k: round((rubric_totals[k] / max(1, rubric_counts.get(k, 0))), 2) for k in rubric_totals.keys()
    }

    suggestions: List[str] = []
    for kw in weaknesses[:6]:
        suggestions.append(f"Practice: {kw} (explain definition, use-case, trade-offs, and a quick example).")

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "rubric_averages": rubric_avgs,
        "suggestions": suggestions,
    }

