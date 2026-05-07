from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, jsonify, request, session

from services.ai_interview_service import AiInterviewService
from services.llm_service import LlmService
from services.resume_service import ResumeService
from services.vector_store_service import VectorStoreService


def create_ai_blueprint(*, data_dir: Path) -> Blueprint:
    bp = Blueprint("ai_api", __name__)

    resume_service = ResumeService(uploads_dir=data_dir / "uploads")

    def get_ai() -> AiInterviewService:
        llm = LlmService()
        vs = VectorStoreService(persist_dir=data_dir / "chroma")
        return AiInterviewService(llm_service=llm, vector_store_service=vs)

    @bp.post("/api/resume/upload")
    def upload_resume():
        if not session.get("user_id"):
            return jsonify({"error": "Not authenticated"}), 401

        f = request.files.get("resume")
        if not f:
            return jsonify({"error": "Missing file field 'resume'"}), 400

        content = f.read()
        if not content:
            return jsonify({"error": "Empty file"}), 400

        try:
            ai = get_ai()
            llm = ai._llm
            vs = ai._vs
            info = resume_service.save_upload(filename=f.filename or "resume", content=content)
            text = resume_service.extract_text(path=Path(info["path"]))
            chunks = resume_service.chunk_text(text=text)

            embeddings = llm.embed_texts([c["text"] for c in chunks]) if chunks else []
            if chunks and embeddings:
                vs.upsert_resume_chunks(resume_id=info["resume_id"], chunks=chunks, embeddings=embeddings)

            profile = ai.extract_resume_profile(resume_text=text)

            session["resume_id"] = info["resume_id"]
            session["resume_profile"] = profile

            return jsonify({"ok": True, "resume_id": info["resume_id"], "profile": profile})
        except Exception as e:
            msg = str(e)
            code = 400
            if "OPENAI_API_KEY" in msg:
                code = 503
                msg = "AI features are not configured. Set OPENAI_API_KEY and restart the server."
            return jsonify({"error": msg}), code

    @bp.post("/api/chat")
    def chat():
        if not session.get("user_id"):
            return jsonify({"error": "Not authenticated"}), 401

        payload: Dict[str, Any] = request.get_json(silent=True) or {}
        message = (payload.get("message") or "").strip()
        if not message:
            return jsonify({"error": "message is required"}), 400

        system = (
            "You are the platform assistant for an AI interview web app. "
            "Help users navigate features: resume upload, starting an interview, analytics, evaluation rubric, and settings. "
            "Be concise and action-oriented."
        )
        schema = '{"reply": "string"}'
        try:
            ai = get_ai()
            data = ai._llm.chat_json(system=system, user=message, schema_hint=schema, max_output_tokens=250)
            return jsonify({"reply": data.get("reply") or ""})
        except Exception as e:
            msg = str(e)
            code = 500
            if "OPENAI_API_KEY" in msg:
                code = 503
                msg = "AI features are not configured. Set OPENAI_API_KEY and restart the server."
            return jsonify({"error": msg}), code

    return bp
