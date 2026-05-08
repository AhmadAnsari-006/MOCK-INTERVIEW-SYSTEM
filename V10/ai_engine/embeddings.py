from __future__ import annotations

from functools import lru_cache
from typing import List

try:
    import numpy as np  # type: ignore
    from sentence_transformers import SentenceTransformer  # type: ignore
except Exception:  # pragma: no cover
    np = None
    SentenceTransformer = None


@lru_cache(maxsize=2)
def _load_model(model_name: str) -> SentenceTransformer:
    if SentenceTransformer is None:
        raise RuntimeError("sentence-transformers is not installed")
    return SentenceTransformer(model_name)


def embed_texts(*, model_name: str, texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    # Preferred: sentence-transformers (quality embeddings)
    if SentenceTransformer is not None and np is not None:
        m = _load_model(model_name)
        vectors = m.encode(texts, normalize_embeddings=True, convert_to_numpy=True)
        if isinstance(vectors, np.ndarray):
            return vectors.astype("float32").tolist()
        return [list(map(float, v)) for v in vectors]

    # Fallback: deterministic hashed bag-of-words vector (keeps app running without heavy deps)
    def hashed_vec(t: str, dim: int = 256) -> List[float]:
        v = [0.0] * dim
        for tok in (t or "").lower().split():
            h = hash(tok) % dim
            v[h] += 1.0
        # L2 normalize
        norm = sum(x * x for x in v) ** 0.5
        if norm > 0:
            v = [x / norm for x in v]
        return v

    return [hashed_vec(t) for t in texts]

