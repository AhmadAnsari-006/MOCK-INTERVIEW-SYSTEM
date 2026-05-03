from flask import Flask, request, jsonify, session, send_from_directory
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from routes.interview_routes import create_interview_blueprint
from services.evaluation_service import evaluate_answer
from services.feedback_service import build_final_feedback, summarize_score
from services.history_service import HistoryService
from services.question_service import QuestionService
from services.session_service import SessionService

# -----------------------------
# App Setup
# -----------------------------
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
)

app.secret_key = "dev-secret-key"

question_service = QuestionService(data_dir=BASE_DIR / "data")
session_service = SessionService(data_dir=BASE_DIR / "data")
history_service = HistoryService(data_dir=BASE_DIR / "data")

app.register_blueprint(create_interview_blueprint(question_service, session_service))

def _get_session_id():
    return session.get("session_id")


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return send_from_directory(str(BASE_DIR / "static" / "pages"), "index.html")


@app.route("/interview")
def interview_page():
    return send_from_directory(str(BASE_DIR / "static" / "pages"), "interview.html")


@app.route("/result")
def result_page():
    return send_from_directory(str(BASE_DIR / "static" / "pages"), "result.html")


# -----------------------------
# GET ROLES
# -----------------------------
@app.route("/get_roles")
def get_roles_route():
    return jsonify({"roles": question_service.get_roles()})


# -----------------------------
# GET FIELDS (IMPORTANT ADD)
# -----------------------------
@app.route("/get_fields")
def get_fields_route():
    role = request.args.get("role")
    fields = question_service.get_fields(role)
    return jsonify({"fields": fields})


# -----------------------------
# Start Interview
# -----------------------------
@app.route("/start", methods=["POST"])
def start():

    user_name = request.form.get("name")
    role = request.form.get("role")
    field = request.form.get("field")
    difficulty = request.form.get("difficulty")
    num_questions = int(request.form.get("num_questions", 5))

    picked = question_service.pick_questions(role, field, difficulty, num_questions)
    if not picked:
        return "❌ No questions found. Check dropdown mapping."

    sess = session_service.create_session(
        name=user_name,
        role=role,
        field=field,
        difficulty=difficulty,
        questions=picked,
    )
    session["session_id"] = sess["session_id"]

    return jsonify({"redirect": "/interview", "session_id": sess["session_id"], "total": len(picked)})


# -----------------------------
# Submit Answer
# -----------------------------
@app.route("/answer", methods=["POST"])
def answer():
    data = request.get_json(silent=True) or {}
    answer_text = data.get("answer", "")

    session_id = _get_session_id()
    sess = session_service.get_session(session_id)
    if not sess:
        return jsonify({"redirect": "/"})

    idx = int(sess.get("current_index") or 0)
    questions = sess.get("questions") or []
    if idx >= len(questions):
        return jsonify({"redirect": "/result"})

    q = questions[idx]
    eval_result = evaluate_answer(answer=answer_text, keywords=q.get("keywords") or [])

    sess.setdefault("answers", []).append(answer_text)
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

    if sess["current_index"] < len(questions):
        session_service.save_session(sess)
        return jsonify({
            "next_question": questions[sess["current_index"]]["question_text"],
            "index": sess["current_index"],
        })

    session_service.mark_completed(sess)
    return jsonify({"redirect": "/result"})


# -----------------------------
def _feedback_statement(score_10: float) -> str:
    if score_10 >= 9.0:
        return "Outstanding. You explained the key ideas confidently and with great coverage."
    if score_10 >= 7.5:
        return "Strong performance. Your answer coverage is solid—add more depth and trade-offs."
    if score_10 >= 6.0:
        return "Good progress. You have the basics—now focus on clarity, examples, and precision."
    if score_10 >= 4.0:
        return "Fair attempt. You’re on track, but you’re missing several expected concepts."
    return "Needs improvement. Focus on fundamentals, key terms, and structured explanation."


def _creative_improvement_tips(score_10: float, report) -> list:
    weaknesses = (report or {}).get("weaknesses") or []
    top_missing = weaknesses[:5]

    if score_10 >= 8.0:
        tips = [
            "Level-up challenge: add 1 real-world example and 1 trade-off in every answer.",
            "Give a 15-second summary first, then expand (interviewer-friendly structure).",
        ]
    elif score_10 >= 5.0:
        tips = [
            "Use a simple blueprint: Definition → How it works → Example → Edge case.",
            "After answering, ask yourself: “Did I explain the *why* and not only the *what*?”",
        ]
    else:
        tips = [
            "Start with fundamentals: define the term in one sentence before anything else.",
            "Practice a 3-step flow: Problem → Solution → Result (keep it concrete).",
        ]

    if top_missing:
        tips.append("Focus keywords for next attempt: " + ", ".join(top_missing) + ".")

    return tips


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=True)