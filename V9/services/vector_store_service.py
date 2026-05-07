from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import chromadb


class VectorStoreService:
    def __init__(self, *, persist_dir: Path):
        self._persist_dir = persist_dir
        self._persist_dir.mkdir(parents=True, exist_ok=True)
        self._client = chromadb.PersistentClient(path=str(self._persist_dir))

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

        col = self._client.get_or_create_collection(name=self._collection_name(resume_id))
        ids: List[str] = []
        docs: List[str] = []
        metas: List[Dict[str, Any]] = []

        for i, ch in enumerate(chunks):
            ids.append(str(ch.get("chunk_id") or f"{resume_id}:{i}"))
            docs.append(str(ch.get("text") or ""))
            metas.append({k: v for k, v in (ch.get("meta") or {}).items()})

        col.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)

    def query(
        self,
        *,
        resume_id: str,
        query_embedding: List[float],
        top_k: int = 5,
    ) -> List[Tuple[str, Dict[str, Any]]]:
        col = self._client.get_or_create_collection(name=self._collection_name(resume_id))
        res = col.query(query_embeddings=[query_embedding], n_results=max(1, int(top_k)))
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        out: List[Tuple[str, Dict[str, Any]]] = []
        for d, m in zip(docs, metas):
            out.append((d, m or {}))
        return out
