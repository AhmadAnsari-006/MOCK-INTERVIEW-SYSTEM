from __future__ import annotations

from typing import Any, Dict, List, Optional

from evaluators.text_metrics import confidence_score, keyword_coverage, basic_counts


def evaluate_answer(
    answer: str,
    keywords: List[str],
    *,
    relevance_0_1: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Backwards-compatible evaluator (used by legacy `/answer` endpoint).
    Now enriched with:
      - confidence score (heuristic)
      - optional relevance score (embedding/RAG similarity when available)
    """

    ratio, matched, missing, counts = keyword_coverage(answer, keywords or [])
    score_10 = round(float(ratio) * 10.0, 2)
    score_10 = max(0.0, min(10.0, score_10))
    score_100 = int(round((score_10 / 10) * 100))

    conf_10 = confidence_score(answer or "")
    rel_10 = round(float(relevance_0_1) * 10.0, 2) if relevance_0_1 is not None else None

    feedback = _generate_feedback(score_10=score_10, matched=matched, missing=missing, conf_10=conf_10, rel_10=rel_10)
    c = basic_counts(answer or "")

    return {
        "score_10": score_10,
        "score_100": score_100,
        "answer_words": int(c["words"]),
        "keyword_hit_count": counts["hit"],
        "keyword_total": counts["total"],
        "matched_keywords": matched,
        "missing_keywords": missing,
        "confidence_10": conf_10,
        "relevance_10": rel_10,
        "feedback": feedback,
    }


def _generate_feedback(
    *,
    score_10: float,
    matched: List[str],
    missing: List[str],
    conf_10: float,
    rel_10: Optional[float],
) -> str:
    if score_10 >= 8:
        core = "Strong coverage of expected concepts."
    elif score_10 >= 5:
        core = "Some key points are present, but the coverage can be deeper and more structured."
    else:
        core = "Missing several core concepts—focus on fundamentals and specific details."

    extras: List[str] = []
    if conf_10 < 4.0:
        extras.append("Try answering with a clearer structure and fewer hedges.")
    if rel_10 is not None and rel_10 < 4.0:
        extras.append("Your answer seems off-topic—align directly with the question.")

    if missing:
        top = ", ".join(missing[:3])
        extras.append(f"Include: {top}.")
    elif matched:
        top = ", ".join(matched[:3])
        extras.append(f"Good mentions: {top}.")

    return (core + (" " + " ".join(extras) if extras else "")).strip()
