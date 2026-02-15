# Math Feedback App

A web application where students photograph their handwritten math solutions and receive AI-powered feedback on their reasoning process.

## Features

- Select from multiple math topics (fractions, linear equations, percentages)
- Upload photos of handwritten work
- Image quality detection — rejects blurry, poorly lit, or unreadable images with helpful tips
- AI-powered OCR extracts handwritten math via Claude Vision
- Detailed feedback on solution process, not just correctness
- Step-by-step analysis with encouragement and suggestions
- View history of previous submissions

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: HTML/CSS/JavaScript (vanilla)
- **Database**: SQLite
- **AI**: Claude Vision API (image quality check + OCR) and Claude API (evaluation)
- **Model**: `claude-sonnet-4-20250514`

## Architecture

The app uses a 2-step AI pipeline:

1. **Vision Call** (Claude Vision) — Checks image quality and extracts handwritten math text in a single call. Rejects blurry/unreadable images with helpful suggestions.
2. **Evaluation Call** (Claude Text) — Evaluates the extracted solution against the correct answer. Provides step-by-step analysis, identifies errors, and gives encouraging feedback.

## Setup Instructions

### Prerequisites

- Python 3.10+
- Anthropic API key with credits (https://console.anthropic.com/)

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Backend Setup

```bash
cd backend
pip install -r requirements.txt

# Copy the example env file and add your API key
cp .env.example .env
# Edit .env with your Anthropic API key

# Run the server (on Windows use: py -m uvicorn app.main:app --reload)
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
# Open index.html in browser, or use a local server:
python -m http.server 3000
```

The frontend will be available at `http://localhost:3000`

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/topics` | List all math topics |
| GET | `/api/topics/{id}/problems` | Get problems for a topic |
| GET | `/api/problems/{id}` | Get a specific problem |
| POST | `/api/submissions` | Submit solution for evaluation |
| GET | `/api/submissions` | View submission history |
| GET | `/api/submissions/{id}` | Get submission details |
| GET | `/health` | Check API and service status |

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Project Structure

```
/
├── README.md                  # This file
├── DESIGN.md                  # Technical design document
├── CONVERSATION_LOG.md        # Development log (session 1)
├── CONVERSATION_LOG_2.md      # Development log (session 2)
├── seed_data.json             # Initial math problems data
├── backend/
│   ├── .env.example           # API key template
│   ├── requirements.txt       # Python dependencies
│   └── app/
│       ├── main.py            # FastAPI application + health check
│       ├── models.py          # Pydantic models (Feedback, StepAnalysis, etc.)
│       ├── database.py        # SQLite setup, init, seed
│       ├── routers/
│       │   ├── topics.py      # Topic endpoints
│       │   ├── problems.py    # Problem endpoints
│       │   └── submissions.py # Submission pipeline (vision + evaluation)
│       └── services/
│           ├── ocr.py         # VisionService (quality check + OCR)
│           └── evaluator.py   # EvaluatorService (solution evaluation)
└── frontend/
    ├── index.html             # Single-page application
    └── src/
        ├── app.js             # Application logic
        └── styles.css         # Responsive styles
```

## Assumptions & Scope Decisions

- Single-user application (no authentication)
- SQLite for simplicity (could upgrade to PostgreSQL for production)
- Images stored as base64 in database (would use file storage for production)
- Frontend prioritizes functionality over visual design
- CORS configured for all origins (restrict in production)

## Testing

Use test images to verify the application:
- **Clear handwriting** — should extract text and provide evaluation feedback
- **Blurry/dark images** — should be rejected with helpful retake suggestions
- **Correct solutions** — should confirm correctness with positive feedback
- **Incorrect solutions** — should identify errors with step-by-step analysis

## Development History

See `CONVERSATION_LOG.md` and `CONVERSATION_LOG_2.md` for detailed development logs including design decisions, experiments tried (OCR.space, multi-step pipelines, crossed-out detection), and lessons learned.
