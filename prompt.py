from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import mysql.connector

app = Flask(__name__)
CORS(app)  # Required when frontend & backend are on different domains


# ---------------------------
# Database Connection Function
# ---------------------------
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME"),
        port=int(os.environ.get("DB_PORT", 3306))
    )


# ---------------------------
# Home Route
# ---------------------------
@app.route('/')
def home():
    return render_template("hansik.html")


# ---------------------------
# Submit Test + Store Answers + Leaderboard
# ---------------------------
@app.route('/get_score', methods=['POST'])
def get_score():
    data = request.json

    name = data.get('name')
    jntu = data.get('jntu')
    branch = data.get('branch')
    answers = data.get('answers', [])

    score = sum(1 for a in answers if a.strip() != "")

    db = get_db_connection()
    cursor = db.cursor()

    # Check if participant exists
    cursor.execute("SELECT id FROM participants WHERE jntu=%s", (jntu,))
    existing = cursor.fetchone()

    if existing:
        participant_id = existing[0]

        cursor.execute(
            "UPDATE participants SET name=%s, branch=%s, score=%s WHERE id=%s",
            (name, branch, score, participant_id)
        )

        cursor.execute(
            "DELETE FROM answers WHERE participant_id=%s",
            (participant_id,)
        )

    else:
        cursor.execute(
            "INSERT INTO participants (name, jntu, branch, score) VALUES (%s, %s, %s, %s)",
            (name, jntu, branch, score)
        )
        participant_id = cursor.lastrowid

    # Insert answers
    for i, ans in enumerate(answers):
        cursor.execute(
            "INSERT INTO answers (participant_id, question_number, answer_text) VALUES (%s, %s, %s)",
            (participant_id, i + 1, ans)
        )

    db.commit()
    cursor.close()
    db.close()

    # Fetch leaderboard
    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute(
        "SELECT name, jntu, branch, score FROM participants ORDER BY score DESC"
    )
    leaderboard = cursor.fetchall()

    cursor.close()
    db.close()

    return jsonify({
        "score": score,
        "leaderboard": leaderboard
    })


# ---------------------------
# Local Development Run
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)