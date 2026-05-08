from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class FaissHit:
    text: str
    meta: Dict[str, Any]
    score: float  # cosine similarity approx when vectors normalized


class FaissStore:
    """
    Minimal FAISS-based store for resume chunks.
    Stores: index + sidecar JSONL docs.

    Works only if `faiss` + `numpy` are installed. Callers should catch RuntimeError and fall back.
    """

    def __init__(self, *, persist_dir: Path):
        self._dir = persist_dir
        self._dir.mkdir(parents=True, exist_ok=True)

    def _paths(self, resume_id: str) -> Tuple[Path, Path]:
        safe = (resume_id or "unknown").strip().replace("/", "_")
        idx_path = self._dir / f"{safe}.faiss"
        docs_path = self._dir / f"{safe}.jsonl"
        return idx_path, docs_path

    def upsert(
        self,
        *,
        resume_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> None:
        try:
            import faiss  # type: ignore
            import numpy as np  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("FAISS store requires faiss-cpu and numpy") from e

        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")

        idx_path, docs_path = self._paths(resume_id)

        X = np.asarray(embeddings, dtype="float32")
        if X.ndim != 2:
            raise ValueError("embeddings must be 2D")
        dim = int(X.shape[1])

        # cosine sim if vectors are normalized (we normalize in embeddings module when available)
        index = faiss.IndexFlatIP(dim)
        index.add(X)
        faiss.write_index(index, str(idx_path))

        with docs_path.open("w", encoding="utf-8") as f:
            for ch in chunks:
                f.write(
                    json.dumps(
                        {"text": str(ch.get("text") or ""), "meta": ch.get("meta") or {}, "chunk_id": ch.get("chunk_id")},
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    def query(
        self,
        *,
        resume_id: str,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[FaissHit]:
        try:
            import faiss  # type: ignore
            import numpy as np  # type: ignore
        except Exception as e:  # pragma: no cover
            raise RuntimeError("FAISS store requires faiss-cpu and numpy") from e

        idx_path, docs_path = self._paths(resume_id)
        if not idx_path.exists() or not docs_path.exists():
            return []

        index = faiss.read_index(str(idx_path))
        q = np.asarray([query_embedding], dtype="float32")
        D, I = index.search(q, max(1, int(top_k)))
        ids = [int(i) for i in I[0].tolist() if int(i) >= 0]

        docs: List[Dict[str, Any]] = []
        with docs_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    docs.append(json.loads(line))
                except Exception:
                    continue

        out: List[FaissHit] = []
        for rank, doc_i in enumerate(ids):
            if doc_i >= len(docs):
                continue
            d = docs[doc_i]
            score = float(D[0][rank])
            out.append(FaissHit(text=str(d.get("text") or ""), meta=d.get("meta") or {}, score=score))
        return out

