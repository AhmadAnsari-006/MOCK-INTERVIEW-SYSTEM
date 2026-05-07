from __future__ import annotations

import re
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import docx2txt
from pypdf import PdfReader


class ResumeService:
    def __init__(self, *, uploads_dir: Path):
        self._uploads_dir = uploads_dir
        self._uploads_dir.mkdir(parents=True, exist_ok=True)

    def save_upload(self, *, filename: str, content: bytes) -> Dict[str, Any]:
        resume_id = uuid.uuid4().hex
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", filename or "resume")
        ext = (Path(safe_name).suffix or "").lower()
        if ext not in {".pdf", ".docx"}:
            raise ValueError("Only PDF and DOCX are supported")

        path = self._uploads_dir / f"{resume_id}{ext}"
        path.write_bytes(content)
        return {"resume_id": resume_id, "path": str(path), "ext": ext, "filename": safe_name}

    def extract_text(self, *, path: Path) -> str:
        ext = (path.suffix or "").lower()
        if ext == ".pdf":
            reader = PdfReader(str(path))
            parts: List[str] = []
            for p in reader.pages:
                parts.append(p.extract_text() or "")
            return "\n".join(parts)
        if ext == ".docx":
            return docx2txt.process(str(path)) or ""
        raise ValueError("Unsupported file type")

    def chunk_text(self, *, text: str, chunk_chars: int = 1200, overlap: int = 150) -> List[Dict[str, Any]]:
        t = (text or "").strip()
        if not t:
            return []

        cleaned = re.sub(r"\n{3,}", "\n\n", t)

        chunks: List[Dict[str, Any]] = []
        i = 0
        chunk_idx = 0
        while i < len(cleaned):
            j = min(len(cleaned), i + max(200, int(chunk_chars)))
            chunk = cleaned[i:j].strip()
            if chunk:
                chunks.append(
                    {
                        "chunk_id": f"c{chunk_idx}",
                        "text": chunk,
                        "meta": {"start": i, "end": j},
                    }
                )
                chunk_idx += 1
            if j >= len(cleaned):
                break
            i = max(0, j - max(0, int(overlap)))
        return chunks
