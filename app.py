import os
import logging
import sqlite3
import re

from typing import Optional
from datetime import datetime

from flask import Flask, render_template, request, session
from groq import Groq
from dotenv import load_dotenv
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# =========================================================
# LOAD ENV VARIABLES
# =========================================================
load_dotenv()

# =========================================================
# APP CONFIG
# =========================================================
app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "dev-secret-key"
)

API_KEY = os.getenv("GROQ_API_KEY")

MODEL_NAME = "llama-3.3-70b-versatile"

# =========================================================
# LOGGING CONFIG
# =========================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# =========================================================
# RATE LIMITER
# =========================================================
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["20 per minute"],
    storage_uri="memory://"
)

# =========================================================
# API KEY VALIDATION
# =========================================================
if not API_KEY:

    logger.critical("GROQ_API_KEY is missing.")

    raise EnvironmentError(
        "Please add GROQ_API_KEY in your .env file."
    )

# =========================================================
# GROQ CLIENT
# =========================================================
client = Groq(api_key=API_KEY)

logger.info("Groq client initialized successfully.")

# =========================================================
# DATABASE INITIALIZATION
# =========================================================
def init_db():
    """
    Creates SQLite database and table if not exists.
    """

    conn = sqlite3.connect("interviews.db")

    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interview_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_role TEXT NOT NULL,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        feedback TEXT NOT NULL,
        score INTEGER,
        created_at TEXT NOT NULL
    )
    """)

    conn.commit()
    conn.close()

    logger.info("Database initialized successfully.")

# =========================================================
# SAVE INTERVIEW RESULT
# =========================================================
def save_interview_result(
    job_role,
    question,
    answer,
    feedback,
    score
):
    """
    Saves interview result to database.
    """

    conn = sqlite3.connect("interviews.db")

    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO interview_results (
        job_role,
        question,
        answer,
        feedback,
        score,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        job_role,
        question,
        answer,
        feedback,
        score,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    logger.info("Interview result saved successfully.")

# =========================================================
# HELPER FUNCTIONS
# =========================================================
def clean_input(value: str) -> str:
    """
    Cleans user input safely.
    """

    return value.strip() if value else ""


def get_ai_response(prompt: str) -> Optional[str]:
    """
    Sends prompt to Groq API and returns response.
    """

    try:

        logger.info(
            f"Sending prompt to AI: {prompt[:80]}..."
        )

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        content = response.choices[0].message.content

        if not content:

            logger.warning(
                "Empty response received from AI."
            )

            return None

        return content.strip()

    except Exception:

        logger.exception(
            "Groq API request failed."
        )

        return None


def generate_questions(job_role: str) -> list:
    """
    Generates interview questions.
    """

    prompt = f"""
    Generate exactly 3 concise technical interview
    questions for a {job_role}.

    Rules:
    - One question per line
    - No numbering
    - No bullet points
    - No explanations
    """

    raw_questions = get_ai_response(prompt)

    if not raw_questions:

        return [
            "AI is temporarily unavailable.",
            "Please try again later.",
            "Check app.log for details."
        ]

    questions = [
        q.strip("-•1234567890. ")
        for q in raw_questions.split('\n')
        if q.strip()
    ]

    return questions[:3]


def evaluate_answer(
    job_role: str,
    question: str,
    answer: str
) -> str:
    """
    Evaluates candidate answer using AI.
    """

    if len(answer) > 2000:

        return (
            "Answer too long. "
            "Please limit responses to 2000 characters."
        )

    prompt = f"""
    You are a senior {job_role} interviewer.

    Interview Question:
    {question}

    Candidate Answer:
    {answer}

    Evaluate the answer professionally.

    Return in this format:

    Score: x/10

    Strengths:
    - Mention good points

    Improvements:
    - Mention missing concepts or corrections

    Keep response concise.
    """

    feedback = get_ai_response(prompt)

    return feedback or "Could not generate feedback."


def extract_score(feedback: str) -> int:
    """
    Extracts score from AI feedback.
    """

    match = re.search(r"(\\d+)/10", feedback)

    if match:
        return int(match.group(1))

    return 0

# =========================================================
# ROUTES
# =========================================================
@app.route('/')
def index():

    return render_template('index.html')


@app.route('/interview', methods=['POST'])
@limiter.limit("10 per minute")
def interview():

    job_role = clean_input(
        request.form.get('job_role')
    )

    if not job_role:

        return render_template(
            'index.html',
            error="Please enter a job role."
        ), 400

    logger.info(
        f"Generating interview for role: {job_role}"
    )

    questions = generate_questions(job_role)

    # SESSION MEMORY
    session["job_role"] = job_role
    session["questions"] = questions

    return render_template(
        'interview.html',
        role=job_role,
        questions=questions
    )


@app.route('/evaluate', methods=['POST'])
@limiter.limit("10 per minute")
def evaluate():

    job_role = clean_input(
        request.form.get('job_role')
    )

    results = []

    for i in range(1, 4):

        question = clean_input(
            request.form.get(f'question_{i}')
        )

        answer = clean_input(
            request.form.get(f'answer_{i}')
        )

        if not question or not answer:

            results.append({
                'question': question or "Question missing.",
                'answer': answer or "No answer provided.",
                'feedback': "Skipped due to incomplete input.",
                'score': 0
            })

            continue

        feedback = evaluate_answer(
            job_role,
            question,
            answer
        )

        score = extract_score(feedback)

        # SAVE TO DATABASE
        save_interview_result(
            job_role,
            question,
            answer,
            feedback,
            score
        )

        results.append({
            'question': question,
            'answer': answer,
            'feedback': feedback,
            'score': score
        })

    # SAVE SESSION MEMORY
    session["results"] = results

    logger.info(
        f"Interview evaluation completed for role: {job_role}"
    )

    return render_template(
        'results.html',
        role=job_role,
        results=results
    )


@app.route('/history')
def history():
    """
    Displays interview history page.
    """

    conn = sqlite3.connect("interviews.db")

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM interview_results
    ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    history_data = [
        dict(row)
        for row in rows
    ]

    return render_template(
        "history.html",
        history=history_data
    )


@app.route('/dashboard')
def dashboard():
    """
    Analytics dashboard.
    """

    conn = sqlite3.connect("interviews.db")

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
    SELECT *
    FROM interview_results
    """)

    rows = cursor.fetchall()

    conn.close()

    history = [
        dict(row)
        for row in rows
    ]

    total_interviews = len(history)

    average_score = 0

    if total_interviews > 0:

        average_score = round(
            sum(item["score"] for item in history)
            / total_interviews,
            2
        )

    return render_template(
        "dashboard.html",
        total_interviews=total_interviews,
        average_score=average_score,
        history=history
    )


@app.route('/memory')
def memory():

    return {
        "job_role": session.get("job_role"),
        "questions": session.get("questions"),
        "results": session.get("results")
    }


@app.route('/clear-memory')
def clear_memory():

    session.clear()

    logger.info("Session memory cleared.")

    return {
        "message": "Session memory cleared successfully."
    }


@app.route('/health')
def health():

    return {
        "status": "ok",
        "message": "App is running successfully."
    }, 200

# =========================================================
# ERROR HANDLERS
# =========================================================
@app.errorhandler(404)
def not_found(error):

    logger.warning(f"404 Error: {error}")

    return render_template(
        'index.html',
        error="Page not found."
    ), 404


@app.errorhandler(500)
def server_error(error):

    logger.exception(
        f"500 Internal Server Error: {error}"
    )

    return render_template(
        'index.html',
        error="Something went wrong."
    ), 500

# =========================================================
# INITIALIZE DATABASE
# =========================================================
init_db()

# =========================================================
# START APPLICATION
# =========================================================
if __name__ == '__main__':

    logger.info("Starting Flask application...")

    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000
    )
    '''
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    










































































































































































































































































































    
    
    
    

















































































































































































    
    '''