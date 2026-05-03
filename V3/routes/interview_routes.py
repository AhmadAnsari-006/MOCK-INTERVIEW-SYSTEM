import time

from flask import Blueprint, jsonify, request, session

from services.evaluation_service import evaluate_answer
from services.feedback_service import build_final_feedback, summarize_score


def create_interview_blueprint(question_service, session_service):
    bp = Blueprint("interview_api", __name__)

    @bp.get("/start-interview")
    def start_interview():
        name = request.args.get("name", "")
        role = request.args.get("role", "")
        field = request.args.get("field", "")
        difficulty = request.args.get("difficulty", "medium")
        num_questions = int(request.args.get("num_questions", 5))

        picked = question_service.pick_questions(role, field, difficulty, num_questions)
        if not picked:
            return jsonify({"error": "No questions found for given role/field/difficulty"}), 404

        sess = session_service.create_session(
            name=name,
            role=role,
            field=field,
            difficulty=difficulty,
            questions=picked,
        )

        session["session_id"] = sess["session_id"]

        return jsonify(
            {
                "session_id": sess["session_id"],
                "total_questions": len(picked),
                "current_index": 0,
            }
        )

    @bp.get("/get-question")
    def get_question():
        session_id = request.args.get("session_id") or session.get("session_id")
        sess = session_service.get_session(session_id)
        if not sess:
            return jsonify({"error": "Invalid session"}), 400

        idx = int(sess.get("current_index") or 0)
        questions = sess.get("questions") or []

        if idx >= len(questions):
            return jsonify({"done": True}), 200

        q = questions[idx]
        return jsonify(
            {
                "done": False,
                "question_id": q.get("question_id"),
                "question_text": q.get("question_text"),
                "keywords": q.get("keywords"),
                "index": idx,
                "total": len(questions),
            }
        )

    @bp.post("/submit-answer")
    def submit_answer():
        payload = request.get_json(silent=True) or {}
        session_id = payload.get("session_id") or request.args.get("session_id") or session.get("session_id")
        sess = session_service.get_session(session_id)
        if not sess:
            return jsonify({"error": "Invalid session"}), 400

        idx = int(sess.get("current_index") or 0)
        questions = sess.get("questions") or []
        if idx >= len(questions):
            return jsonify({"error": "Interview already completed"}), 400

        answer = payload.get("answer", "")
        q = questions[idx]

        eval_result = evaluate_answer(answer=answer, keywords=q.get("keywords") or [])

        sess.setdefault("answers", []).append(
            {
                "question_id": q.get("question_id"),
                "answer": answer,
                "submitted_at": int(time.time()),
            }
        )
        sess.setdefault("per_question", []).append(
            {
                "question_id": q.get("question_id"),
                "score_10": eval_result["score_10"],
                "matched_keywords": eval_result["matched_keywords"],
                "missing_keywords": eval_result["missing_keywords"],
                "feedback": eval_result["feedback"],
            }
        )

        sess["current_index"] = idx + 1

        done = sess["current_index"] >= len(questions)
        if done:
            session_service.mark_completed(sess)
        else:
            session_service.save_session(sess)

        return jsonify(
            {
                "done": done,
                "index": idx,
                "score_10": eval_result["score_10"],
                "matched_keywords": eval_result["matched_keywords"],
                "missing_keywords": eval_result["missing_keywords"],
                "feedback": eval_result["feedback"],
                "next_index": sess["current_index"],
                "total": len(questions),
            }
        )

    @bp.get("/get-feedback")
    def get_feedback():
        session_id = request.args.get("session_id") or session.get("session_id")
        sess = session_service.get_session(session_id)
        if not sess:
            return jsonify({"error": "Invalid session"}), 400

        per_question = sess.get("per_question") or []
        n = len(per_question)
        avg = round(sum((x.get("score_10") or 0) for x in per_question) / n, 2) if n else 0.0
        score_display = round(avg, 1)

        report = build_final_feedback(per_question)
        time_taken = session_service.get_time_taken(sess)

        return jsonify(
            {
                "session_id": session_id,
                "name": sess.get("name"),
                "total_questions": len(sess.get("questions") or []),
                "answered_questions": n,
                "average_score_10": score_display,
                "per_question": per_question,
                "final_feedback": report,
                "summary": summarize_score(score_display),
                "time_taken": time_taken,
                "ui": {
                    "score": score_display,
                    "feedback": summarize_score(score_display),
                    "name": sess.get("name"),
                    "time_taken": time_taken,
                    "per_question": [x.get("score_10") for x in per_question],
                },
            }
        )

    return bp
