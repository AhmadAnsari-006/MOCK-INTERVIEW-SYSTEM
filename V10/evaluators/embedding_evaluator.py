from __future__ import annotations

from typing import List, Optional, Tuple

import numpy as np


def cosine_similarity(a: List[float], b: List[float]) -> float:
    av = np.asarray(a, dtype="float32")
    bv = np.asarray(b, dtype="float32")
    if av.size == 0 or bv.size == 0:
        return 0.0
    denom = (np.linalg.norm(av) * np.linalg.norm(bv))
    if denom <= 0:
        return 0.0
    return float(np.dot(av, bv) / denom)


def best_context_similarity(
    *,
    answer_embedding: List[float],
    context_embeddings: List[List[float]],
) -> Tuple[float, Optional[int]]:
    if not answer_embedding or not context_embeddings:
        return 0.0, None
    best = -1.0
    best_i: Optional[int] = None
    for i, e in enumerate(context_embeddings):
        s = cosine_similarity(answer_embedding, e)
        if s > best:
            best = s
            best_i = i
    return max(0.0, min(1.0, float(best))), best_i

