from flask import Flask, render_template, request, jsonify
import json
import random
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# -----------------------------
# Load JSON
# -----------------------------
def load_questions():
    path = BASE_DIR / "data" / "questions.json"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

questions_data = load_questions()

# -----------------------------
# App Setup
# -----------------------------
app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

# -----------------------------
# Global State (Hackathon Level)
# -----------------------------
current_question_index = 0
user_answers = []
selected_questions = []
user_name = ""
start_time = 0

# -----------------------------
# Helpers
# -----------------------------

# ✅ FIXED: Return all roles (no field confusion)
def get_roles():
    return list(questions_data.keys())


# ✅ NEW: Get fields based on role
def get_fields(role):
    if role in questions_data:
        return list(questions_data[role].keys())
    return []


# ✅ FIXED: Removed role_map (frontend must send exact key)
def get_questions(role, field, difficulty):
    try:
        return questions_data[role][field][difficulty.capitalize()]
    except KeyError:
        print(f"[ERROR] Invalid path → Role: {role}, Field: {field}, Difficulty: {difficulty}")
        return []


# -----------------------------
# Routes
# -----------------------------
@app.route("/")
def home():
    return render_template("index.html")


# -----------------------------
# GET ROLES
# -----------------------------
@app.route("/get_roles")
def get_roles_route():
    return jsonify({"roles": get_roles()})


# -----------------------------
# GET FIELDS (IMPORTANT ADD)
# -----------------------------
@app.route("/get_fields")
def get_fields_route():
    role = request.args.get("role")
    fields = get_fields(role)
    return jsonify({"fields": fields})


# -----------------------------
# Start Interview
# -----------------------------
@app.route("/start", methods=["POST"])
def start():

    global current_question_index, user_answers, selected_questions, user_name, start_time

    current_question_index = 0
    user_answers = []

    user_name = request.form.get("name")
    role = request.form.get("role")
    field = request.form.get("field")
    difficulty = request.form.get("difficulty")
    num_questions = int(request.form.get("num_questions", 5))

    print(f"[START] User={user_name}, Role={role}, Field={field}, Difficulty={difficulty}")

    all_questions = get_questions(role, field, difficulty)

    if not all_questions:
        return "❌ No questions found. Check dropdown mapping."

    selected_questions = random.sample(
        all_questions,
        min(num_questions, len(all_questions))
    )

    start_time = time.time()

    return render_template(
        "interview.html",
        question=selected_questions[0]["question"],
        total=len(selected_questions)
    )


# -----------------------------
# Submit Answer
# -----------------------------
@app.route("/answer", methods=["POST"])
def answer():

    global current_question_index, user_answers

    data = request.get_json(silent=True) or {}
    answer = data.get("answer", "")

    print(f"[ANSWER] Q{current_question_index}: {answer}")

    user_answers.append(answer)

    current_question_index += 1

    if current_question_index < len(selected_questions):

        return jsonify({
            "next_question": selected_questions[current_question_index]["question"],
            "index": current_question_index
        })

    else:
        return jsonify({
            "redirect": "/result"
        })


# -----------------------------
# Result
# -----------------------------
@app.route("/result")
def result():

    total_score = 0
    max_score = 0
    detailed_scores = []

    for i, ans in enumerate(user_answers):

        keywords = selected_questions[i]["keywords"]
        match_count = 0

        for kw in keywords:
            if kw.lower() in ans.lower():
                match_count += 1

        question_score = match_count / len(keywords) if keywords else 0

        detailed_scores.append(round(question_score * 10, 2))

        total_score += match_count
        max_score += len(keywords)

    final_score = int((total_score / max_score) * 10) if max_score else 0

    time_taken = int(time.time() - start_time)

    # Feedback
    if final_score > 7:
        feedback = "🔥 Excellent! Strong understanding and clarity."
    elif final_score > 4:
        feedback = "👍 Decent performance. Improve depth and structure."
    else:
        feedback = "⚠️ Weak fundamentals. Focus on core concepts."

    print(f"[RESULT] Score={final_score}/10 Time={time_taken}s")

    return render_template(
        "result.html",
        score=final_score,
        feedback=feedback,
        name=user_name,
        time_taken=time_taken,
        per_question=detailed_scores
    )


# -----------------------------
# Run
# -----------------------------
if __name__ == "__main__":
    print("Server running at http://127.0.0.1:5000")
    app.run(debug=True)