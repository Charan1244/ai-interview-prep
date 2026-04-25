
# 🤖 PrepAI — AI Interview Prep Tool

An AI-powered full-stack interview preparation platform. Enter any job role and instantly receive tailored interview questions with detailed answers — powered by Google Gemini, with full session history stored in SQLite.

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green?logo=fastapi)
![Gemini](https://img.shields.io/badge/Gemini_AI-1.5_Flash-orange?logo=google)
![SQLite](https://img.shields.io/badge/SQLite-Database-lightblue?logo=sqlite)

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────┐
│                 Frontend (HTML / CSS / JS)                │
│    Enter Role → Generate Questions → Review Answers      │
└─────────────────────────┬────────────────────────────────┘
                          │ REST API (HTTP/JSON)
┌─────────────────────────▼────────────────────────────────┐
│              FastAPI Backend Microservice                 │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │POST /generate│  │GET /sessions │  │GET /sessions  │  │
│  │(Gemini call) │  │(all history) │  │/:id (detail)  │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬───────┘  │
│         │                 │                   │          │
│  ┌──────▼─────────────────▼───────────────────▼───────┐  │
│  │         SQLite Database                            │  │
│  │   sessions table  +  questions table (FK)          │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────┬───────────────────────────────┘
                           │
            ┌──────────────▼──────────────┐
            │     Google Gemini API        │
            │  (gemini-1.5-flash model)    │
            └─────────────────────────────┘
```

---

## ✨ Features

- 🤖 **AI Question Generation** — Gemini generates role-specific technical, behavioral & system design questions
- 🎯 **Difficulty Levels** — Easy / Medium / Hard modes
- 💾 **Session Persistence** — Every session auto-saved to SQLite with full Q&A history
- 📚 **History Panel** — Browse and reload any past session instantly
- 🏷️ **Smart Categorization** — Questions auto-tagged as Technical / Behavioral / System Design
- 🔌 **REST API** — Clean microservice with interactive Swagger docs at `/docs`

---

## 🛠️ Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Frontend   | HTML5, CSS3, JavaScript |
| Backend    | Python 3.11, FastAPI    |
| AI Model   | Google Gemini 1.5 Flash |
| Database   | SQLite (relational)     |
| API Docs   | Swagger UI (auto-gen)   |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Google Gemini API key ([Get one free](https://makersuite.google.com/))

### Backend

```bash
# Clone repo
git clone https://github.com/yourusername/ai-interview-prep.git
cd ai-interview-prep/backend

# Install dependencies
pip install -r requirements.txt

# Set API key
export GEMINI_API_KEY=your_api_key_here

# Start server
uvicorn main:app --reload --port 8000
```

### Frontend

```bash
# Open directly in browser
open frontend/index.html
```

Visit **http://localhost:8000/docs** for the interactive Swagger API explorer.

---

## 📡 API Reference

| Method   | Endpoint                  | Description                              |
|----------|---------------------------|------------------------------------------|
| `GET`    | `/`                       | Health check                             |
| `POST`   | `/api/generate`           | Generate AI questions for a role         |
| `GET`    | `/api/sessions`           | List all past sessions with Q counts     |
| `GET`    | `/api/sessions/{id}`      | Retrieve full session with all Q&A       |
| `DELETE` | `/api/sessions/{id}`      | Delete a session and its questions       |

### Sample Request

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{"job_role": "Software Development Engineer", "difficulty": "hard", "num_questions": 5}'
```

### Sample Response

```json
{
  "session_id": 1,
  "job_role": "Software Development Engineer",
  "difficulty": "hard",
  "questions": [
    {
      "question": "Design a distributed rate limiter for a high-traffic API.",
      "answer": "Use a token bucket algorithm with Redis as the shared store...",
      "category": "system_design"
    }
  ],
  "created_at": "2024-11-15T10:30:00"
}
```

---

## 🗄️ Database Schema

```sql
-- Stores each prep session
CREATE TABLE sessions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    job_role   TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Stores Q&A pairs linked to sessions
CREATE TABLE questions (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id INTEGER NOT NULL,
    question   TEXT NOT NULL,
    answer     TEXT NOT NULL,
    category   TEXT NOT NULL,   -- technical | behavioral | system_design
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);
```

---

## 🔮 Future Roadmap

- [ ] Deploy on AWS EC2 + RDS (PostgreSQL)
- [ ] Add user auth with JWT tokens
- [ ] Voice mode — speak answers, get AI feedback
- [ ] Score tracking and performance analytics
- [ ] Export sessions as PDF

---

## 👨‍💻 Author

Built with Python, FastAPI & Google Gemini.
