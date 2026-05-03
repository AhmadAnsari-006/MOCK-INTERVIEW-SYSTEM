import re
from typing import Any, Dict, List


_WORD_RE = re.compile(r"[a-zA-Z0-9_+#.-]+")


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text or "")]


def evaluate_answer(answer: str, keywords: List[str]) -> Dict[str, Any]:
    answer_lc = (answer or "").lower()
    tokens = set(_tokenize(answer_lc))

    weighted_total = 0.0
    weighted_hit = 0.0
    matched: List[str] = []
    missing: List[str] = []

    for kw in (keywords or []):
        kw_lc = (kw or "").strip().lower()
        if not kw_lc:
            continue

        weight = 1.0
        if " " in kw_lc:
            weight = 1.25
        if len(kw_lc) >= 10:
            weight += 0.25

        weighted_total += weight

        hit = False
        if " " in kw_lc:
            hit = kw_lc in answer_lc
        else:
            hit = kw_lc in tokens or kw_lc in answer_lc

        if hit:
            weighted_hit += weight
            matched.append(kw)
        else:
            missing.append(kw)

    ratio = (weighted_hit / weighted_total) if weighted_total > 0 else 0.0

    score_10 = round(ratio * 10, 2)
    score_10 = max(0.0, min(10.0, score_10))

    score_100 = int(round((score_10 / 10) * 100))

    feedback = _generate_feedback(score_10=score_10, matched=matched, missing=missing)

    return {
        "score_10": score_10,
        "score_100": score_100,
        "matched_keywords": matched,
        "missing_keywords": missing,
        "feedback": feedback,
    }


def _generate_feedback(score_10: float, matched: List[str], missing: List[str]) -> str:
    if score_10 >= 8:
        core = "Strong answer: you covered most expected concepts with good relevance."
    elif score_10 >= 5:
        core = "Decent answer: you mentioned some key points, but the coverage can be deeper and more structured."
    else:
        core = "Needs improvement: the answer misses several core concepts and should be more specific."

    if missing:
        top = ", ".join(missing[:3])
        return f"{core} Try to include: {top}."

    if matched:
        top = ", ".join(matched[:3])
        return f"{core} Good mentions: {top}."

    return core
