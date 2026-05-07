from flask import Flask, request, jsonify, session, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

from routes.interview_routes import create_interview_blueprint
from routes.ai_routes import create_ai_blueprint
from services.evaluation_service import evaluate_answer
from services.feedback_service import build_final_feedback, summarize_score
from services.history_service import HistoryService
from services.db_service import DbService
from services.question_service import QuestionService
from services.session_service import SessionService
from services.ai_interview_service import AiInterviewService
from services.llm_service import LlmService
from services.vector_store_service import VectorStoreService

# -----------------------------
# App Setup
# -----------------------------
app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
)

app.secret_key = "dev-secret-key"

db_service = DbService(db_path=BASE_DIR / "data" / "app.db")
db_service.init_db()

question_service = QuestionService(data_dir=BASE_DIR / "data")
session_service = SessionService(data_dir=BASE_DIR / "data")
history_service = HistoryService(data_dir=BASE_DIR / "data")

ai_service = None
try:
    llm_service = LlmService()
    vector_store_service = VectorStoreService(persist_dir=BASE_DIR / "data" / "chroma")
    ai_service = AiInterviewService(llm_service=llm_service, vector_store_service=vector_store_service)
except Exception:
    ai_service = None

app.register_blueprint(create_interview_blueprint(question_service, session_service, ai_service=ai_service))
app.register_blueprint(create_ai_blueprint(data_dir=BASE_DIR / "data"))

def _get_session_id():
    return session.get("session_id")


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    if session.get("user_id"):
        return send_from_directory(str(BASE_DIR / "static" / "pages"), "index.html")
    return send_from_directory(str(BASE_DIR / "static" / "pages"), "login.html")


@app.route("/signup")
def signup_page():
    return send_from_directory(str(BASE_DIR / "static" / "pages"), "signup.html")


@app.route("/logout")
def logout():
    session.clear()
    return jsonify({"redirect": "/"})


@app.get("/api/me")
def api_me():
    if not session.get("user_id"):
        return jsonify({"authenticated": False}), 200
    return jsonify(
        {
            "authenticated": True,
            "user_id": session.get("user_id"),
            "name": session.get("user_name"),
            "email": session.get("user_email"),
        }
    )


@app.post("/api/signup")
def api_signup():
    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not name or not email or not password:
        return jsonify({"error": "name, email and password are required"}), 400

    if db_service.get_user_by_email(email=email):
        return jsonify({"error": "Email already registered"}), 409

    user_id = db_service.create_user(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        created_at=int(time.time()),
    )
    session["user_id"] = user_id
    session["user_name"] = name
    session["user_email"] = email
    return jsonify({"ok": True, "redirect": "/"})


@app.post("/api/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    email = (payload.get("email") or "").strip().lower()
    password = payload.get("password") or ""

    if not email or not password:
        return jsonify({"error": "email and password are required"}), 400

    user = db_service.get_user_by_email(email=email)
    if not user or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Invalid email or password"}), 401

    session["user_id"] = int(user["id"])
    session["user_name"] = user["name"]
    session["user_email"] = user["email"]
    return jsonify({"ok": True, "redirect": "/"})


@app.post("/api/change-password")
def api_change_password():
    if not session.get("user_id"):
        return jsonify({"error": "Not authenticated"}), 401

    payload = request.get_json(silent=True) or {}
    current_password = payload.get("current_password") or ""
    new_password = payload.get("new_password") or ""

    if not current_password or not new_password:
        return jsonify({"error": "current_password and new_password are required"}), 400

    user = db_service.get_user_by_id(user_id=int(session["user_id"]))
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not check_password_hash(user["password_hash"], current_password):
        return jsonify({"error": "Current password is incorrect"}), 401

    db_service.update_user_password_hash(
        user_id=int(user["id"]),
        password_hash=generate_password_hash(new_password),
    )
    return jsonify({"ok": True})


@app.route("/assets/img/<path:filename>")
def serve_img(filename: str):
    img_dir = (BASE_DIR.parent / "img").resolve()
    return send_from_directory(str(img_dir), filename)


@app.route("/interview")
def interview_page():
    if not session.get("user_id"):
        return send_from_directory(str(BASE_DIR / "static" / "pages"), "login.html")
    return send_from_directory(str(BASE_DIR / "static" / "pages"), "interview.html")


@app.route("/result")
def result_page():
    if not session.get("user_id"):
        return send_from_directory(str(BASE_DIR / "static" / "pages"), "login.html")
    return send_from_directory(str(BASE_DIR / "static" / "pages"), "result.html")


@app.route("/settings")
def settings_page():
    if not session.get("user_id"):
        return send_from_directory(str(BASE_DIR / "static" / "pages"), "login.html")
    return send_from_directory(str(BASE_DIR / "static" / "pages"), "settings.html")


@app.route("/tips")
def tips_page():
    if not session.get("user_id"):
        return send_from_directory(str(BASE_DIR / "static" / "pages"), "login.html")
    return send_from_directory(str(BASE_DIR / "static" / "pages"), "tips.html")


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