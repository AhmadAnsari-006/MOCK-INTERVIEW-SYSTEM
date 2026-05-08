from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb

from rag.faiss_store import FaissStore


class VectorStoreService:
    def __init__(self, *, persist_dir: Path):
        self._persist_dir = persist_dir
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self._persist_dir))
        self._faiss = FaissStore(persist_dir=(self._persist_dir / "faiss"))

    @staticmethod
    def _collection_name(resume_id: str) -> str:
        rid = (resume_id or "").strip() or "unknown"
        safe = "resume_" + hashlib.sha1(rid.encode("utf-8")).hexdigest()[:16]
        return safe

    def upsert_resume_chunks(
        self,
        *,
        resume_id: str,
        chunks: List[Dict[str, Any]],
        embeddings: List[List[float]],
    ) -> None:
        if not chunks:
            return
        if len(chunks) != len(embeddings):
            raise ValueError("chunks and embeddings length mismatch")

        # 1) Always persist to Chroma (no extra deps beyond chromadb)
        col = self._client.get_or_create_collection(name=self._collection_name(resume_id))
        ids: List[str] = []
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []

        for i, ch in enumerate(chunks):
            ids.append(str(ch.get("chunk_id") or f"{resume_id}:{i}"))
            docs.append(str(ch.get("text") or ""))
            metas.append({k: v for k, v in (ch.get("meta") or {}).items()})

        col.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)

        # 2) Best-effort FAISS sidecar (faster retrieval if deps installed)
        try:
            self._faiss.upsert(resume_id=resume_id, chunks=chunks, embeddings=embeddings)
        except Exception:
            pass

    def query(
        self,
        *,
        resume_id: str,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        # Prefer FAISS if present, else fall back to Chroma.
        try:
            hits = self._faiss.query(resume_id=resume_id, query_embedding=query_embedding, top_k=top_k)
            if hits:
                return [(h.text, (h.meta or {}) | {"_score": h.score, "_store": "faiss"}) for h in hits]
        except Exception:
            pass

        col = self._client.get_or_create_collection(name=self._collection_name(resume_id))
        res = col.query(query_embeddings=[query_embedding], n_results=max(1, int(top_k)))
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        out: List[Tuple[str, Dict[str, Any]]] = []
        for d, m in zip(docs, metas):
            mm = (m or {})
            mm["_store"] = "chroma"
            out.append((d, mm))
        return out
