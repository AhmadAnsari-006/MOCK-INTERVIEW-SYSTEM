from __future__ import annotations

import math
import re
from typing import Dict, List, Tuple


_WORD_RE = re.compile(r"[a-zA-Z0-9_+#.-]+")
_SENT_END_RE = re.compile(r"[.!?]+")
_FILLER_RE = re.compile(r"\b(um|uh|like|basically|actually|sort of|kind of|i think|maybe|probably)\b", re.I)


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in _WORD_RE.findall(text or "")]


def basic_counts(text: str) -> Dict[str, float]:
    t = (text or "").strip()
    tokens = tokenize(t)
    words = len(tokens)
    chars = len(t)
    sentences = max(1, len(_SENT_END_RE.findall(t))) if t else 0
    filler = len(_FILLER_RE.findall(t))
    return {"words": float(words), "chars": float(chars), "sentences": float(sentences), "filler": float(filler)}


def confidence_score(text: str) -> float:
    """
    Heuristic 0..10:
    - penalize excessive filler/hedging
    - reward adequate length and structure
    """
    c = basic_counts(text)
    words = c["words"]
    if words <= 0:
        return 0.0

    filler_rate = c["filler"] / max(1.0, words)
    length_bonus = min(1.0, math.log10(1.0 + words) / 2.0)  # ~0..1
    structure_bonus = min(1.0, c["sentences"] / 4.0)

    score01 = 0.45 * length_bonus + 0.35 * structure_bonus + 0.20 * (1.0 - min(1.0, filler_rate * 8))
    return max(0.0, min(10.0, round(score01 * 10.0, 2)))


def keyword_coverage(answer: str, keywords: List[str]) -> Tuple[float, List[str], List[str], Dict[str, int]]:
    answer_lc = (answer or "").lower()
    tokens = set(tokenize(answer_lc))

    weighted_total = 0.0
    weighted_hit = 0.0
    matched: List[str] = []
    missing: List[str] = []
    hit_count = 0
    total_count = 0

    for kw in (keywords or []):
        kw_lc = (kw or "").strip().lower()
        if not kw_lc:
            continue

        total_count += 1

        weight = 1.0
        if " " in kw_lc:
            weight = 1.25
        if len(kw_lc) >= 10:
            weight += 0.25

        weighted_total += weight

        if (" " in kw_lc and kw_lc in answer_lc) or (" " not in kw_lc and (kw_lc in tokens or kw_lc in answer_lc)):
            weighted_hit += weight
            matched.append(kw)
            hit_count += 1
        else:
            missing.append(kw)

    ratio = (weighted_hit / weighted_total) if weighted_total > 0 else 0.0
    ratio = max(0.0, min(1.0, ratio))
    return ratio, matched, missing, {"hit": hit_count, "total": total_count}

