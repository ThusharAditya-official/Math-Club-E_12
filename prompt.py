from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import os
import psycopg2

app = Flask(__name__)
CORS(app)


def get_db_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT")
    )


@app.route('/')
def home():
    return render_template("hansik.html")


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
    cursor.execute("SELECT id FROM participants WHERE jntu=%s;", (jntu,))
    existing = cursor.fetchone()

    if existing:
        participant_id = existing[0]

        cursor.execute(
            "UPDATE participants SET name=%s, branch=%s, score=%s WHERE id=%s;",
            (name, branch, score, participant_id)
        )

        cursor.execute(
            "DELETE FROM answers WHERE participant_id=%s;",
            (participant_id,)
        )

    else:
        cursor.execute(
            "INSERT INTO participants (name, jntu, branch, score) VALUES (%s, %s, %s, %s) RETURNING id;",
            (name, jntu, branch, score)
        )
        participant_id = cursor.fetchone()[0]

    for i, ans in enumerate(answers):
        cursor.execute(
            "INSERT INTO answers (participant_id, question_number, answer_text) VALUES (%s, %s, %s);",
            (participant_id, i + 1, ans)
        )

    db.commit()
    cursor.close()
    db.close()

    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute(
        "SELECT name, jntu, branch, score FROM participants ORDER BY score DESC;"
    )

    rows = cursor.fetchall()

    leaderboard = []
    for row in rows:
        leaderboard.append({
            "name": row[0],
            "jntu": row[1],
            "branch": row[2],
            "score": row[3]
        })

    cursor.close()
    db.close()

    return jsonify({
        "score": score,
        "leaderboard": leaderboard
    })


if __name__ == '__main__':
    app.run(debug=True)