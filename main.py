from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import google.generativeai as genai
import sqlite3
import json
import os
from datetime import datetime

# ── App Init ───────────────────────────────────────────────────────────────────
app = FastAPI(title="AI Interview Prep API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your-api-key-here")
genai.configure(api_key=GEMINI_API_KEY)

# ── Database Setup ─────────────────────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect("interview_prep.db")
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_role    TEXT NOT NULL,
            difficulty  TEXT NOT NULL,
            created_at  TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS questions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id  INTEGER NOT NULL,
            question    TEXT NOT NULL,
            answer      TEXT NOT NULL,
            category    TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ── Models ─────────────────────────────────────────────────────────────────────
class GenerateRequest(BaseModel):
    job_role: str
    difficulty: Optional[str] = "medium"   # easy | medium | hard
    num_questions: Optional[int] = 5

class QAPair(BaseModel):
    question: str
    answer: str
    category: str                           # technical | behavioral | system_design

class GenerateResponse(BaseModel):
    session_id: int
    job_role: str
    difficulty: str
    questions: List[QAPair]
    created_at: str

class SessionSummary(BaseModel):
    session_id: int
    job_role: str
    difficulty: str
    question_count: int
    created_at: str

# ── DB Helper ──────────────────────────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect("interview_prep.db")
    conn.row_factory = sqlite3.Row
    return conn

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "AI Interview Prep API"}


@app.post("/api/generate", response_model=GenerateResponse)
def generate_questions(req: GenerateRequest):
    """
    Use Gemini to generate interview Q&A for a given job role.
    Saves the session + questions to SQLite.
    """
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
        Generate {req.num_questions} interview questions with detailed answers for a {req.job_role} role.
        Difficulty level: {req.difficulty}.
        Mix of technical, behavioral, and system design questions.

        Return ONLY a valid JSON array, no markdown, no explanation:
        [
          {{
            "question": "...",
            "answer": "...",
            "category": "technical" | "behavioral" | "system_design"
          }}
        ]
        """
        response = model.generate_content(prompt)
        text = response.text.strip().strip("```json").strip("```").strip()
        qa_list = json.loads(text)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini error: {str(e)}")

    # Persist session + questions
    conn = get_db()
    try:
        created_at = datetime.utcnow().isoformat()
        cursor = conn.execute(
            "INSERT INTO sessions (job_role, difficulty, created_at) VALUES (?, ?, ?)",
            (req.job_role, req.difficulty, created_at)
        )
        session_id = cursor.lastrowid

        for qa in qa_list:
            conn.execute(
                "INSERT INTO questions (session_id, question, answer, category) VALUES (?, ?, ?, ?)",
                (session_id, qa["question"], qa["answer"], qa.get("category", "technical"))
            )

        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")
    finally:
        conn.close()

    return GenerateResponse(
        session_id=session_id,
        job_role=req.job_role,
        difficulty=req.difficulty,
        questions=[QAPair(**q) for q in qa_list],
        created_at=created_at
    )


@app.get("/api/sessions", response_model=List[SessionSummary])
def get_all_sessions():
    """Retrieve all past prep sessions with question counts."""
    conn = get_db()
    rows = conn.execute("""
        SELECT s.id, s.job_role, s.difficulty, s.created_at,
               COUNT(q.id) as question_count
        FROM sessions s
        LEFT JOIN questions q ON q.session_id = s.id
        GROUP BY s.id
        ORDER BY s.created_at DESC
    """).fetchall()
    conn.close()

    return [
        SessionSummary(
            session_id=r["id"],
            job_role=r["job_role"],
            difficulty=r["difficulty"],
            question_count=r["question_count"],
            created_at=r["created_at"]
        ) for r in rows
    ]


@app.get("/api/sessions/{session_id}", response_model=GenerateResponse)
def get_session(session_id: int):
    """Retrieve a specific session with all its Q&A pairs."""
    conn = get_db()
    session = conn.execute(
        "SELECT * FROM sessions WHERE id = ?", (session_id,)
    ).fetchone()

    if not session:
        conn.close()
        raise HTTPException(status_code=404, detail="Session not found")

    questions = conn.execute(
        "SELECT * FROM questions WHERE session_id = ?", (session_id,)
    ).fetchall()
    conn.close()

    return GenerateResponse(
        session_id=session["id"],
        job_role=session["job_role"],
        difficulty=session["difficulty"],
        questions=[QAPair(
            question=q["question"],
            answer=q["answer"],
            category=q["category"]
        ) for q in questions],
        created_at=session["created_at"]
    )


@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: int):
    """Delete a session and all its questions."""
    conn = get_db()
    conn.execute("DELETE FROM questions WHERE session_id = ?", (session_id,))
    conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
    conn.commit()
    conn.close()
    return {"message": f"Session {session_id} deleted successfully"}
