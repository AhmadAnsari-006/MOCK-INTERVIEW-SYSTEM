from flask import Flask, render_template, request, jsonify

# Added support for field and difficulty selection

# Explicitly define template and static folders
app = Flask(__name__, template_folder="templates", static_folder="static")

# -----------------------------
# Temporary in-memory storage
# (Later this will come from JSON)
# -----------------------------

questions = [
    "What is Object-Oriented Programming?",
    "Explain inheritance.",
    "What is polymorphism?"
]

current_question_index = 0
user_answers = []


# -----------------------------
# Route: Home Page
# -----------------------------

@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


# -----------------------------
# Route: Start Interview
# -----------------------------

@app.route("/start", methods=["POST"])
def start_interview():

    global current_question_index
    global user_answers

    # Reset session data
    current_question_index = 0
    user_answers = []

    # Debug log (helps during hackathon)
    print("Interview started")

    return render_template(
        "interview.html",
        question=questions[current_question_index]
    )


# -----------------------------
# Route: Submit Answer (AJAX)
# -----------------------------

@app.route("/answer", methods=["POST"])
def submit_answer():

    global current_question_index
    global user_answers

    data = request.get_json()

    answer = data.get("answer")

    # Save answer
    user_answers.append(answer)

    print("Answer received:", answer)

    # Move to next question
    current_question_index += 1

    # Check if more questions exist
    if current_question_index < len(questions):

        next_question = questions[current_question_index]

        return jsonify({
            "next_question": next_question
        })

    else:

        # Interview finished
        return jsonify({
            "redirect": "/result"
        })


# -----------------------------
# Route: Result Page
# -----------------------------

@app.route("/result", methods=["GET"])
def result():

    # Basic scoring logic
    score = len(user_answers) * 2

    feedback = "Good attempt. Keep practicing."

    print("Interview finished. Score:", score)

    return render_template(
        "result.html",
        score=score,
        feedback=feedback
    )


# -----------------------------
# Run Server
# -----------------------------

if __name__ == "__main__":

    print("Server starting on http://127.0.0.1:5000")

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
