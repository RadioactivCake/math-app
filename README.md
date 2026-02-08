# Math Feedback App

A web application where students photograph their handwritten math solutions and receive AI-powered feedback on their reasoning process.

## Features

- Select from multiple math topics (fractions, linear equations, percentages)
- Upload photos of handwritten work
- Receive detailed feedback on solution process, not just correctness
- View history of previous submissions

## Tech Stack

- **Backend**: Python + FastAPI
- **Frontend**: HTML/CSS/JavaScript
- **Database**: SQLite
- **APIs**: Mathpix (OCR), Claude (Evaluation)

## Setup Instructions

### Prerequisites

- Python 3.10+
- Node.js (optional, for frontend dev server)

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
MATHPIX_APP_ID=your_mathpix_app_id
MATHPIX_APP_KEY=your_mathpix_app_key
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

The API will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
# Open index.html in browser, or use a local server:
python -m http.server 3000
```

The frontend will be available at `http://localhost:3000`

## API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## Project Structure

```
/
├── README.md              # This file
├── DESIGN.md              # Technical design document
├── seed_data.json         # Initial math problems data
├── backend/
│   ├── app/
│   │   ├── main.py        # FastAPI application
│   │   ├── models.py      # Database models
│   │   ├── database.py    # Database connection
│   │   ├── routers/       # API route handlers
│   │   └── services/      # Mathpix, Claude integrations
│   └── requirements.txt
└── frontend/
    ├── index.html
    ├── src/
    │   ├── app.js
    │   └── styles.css
    └── public/
```

## Assumptions & Scope Decisions

- Single-user application (no authentication)
- SQLite for simplicity (could upgrade to PostgreSQL for production)
- Images stored as base64 in database (would use file storage for production)
- Frontend prioritizes functionality over visual design

## Testing

Use the provided test images from the Google Drive folder to test the application:
- `correct_clean.png` - Clean handwriting, correct solution
- `correct_messy.png` - Messy handwriting, correct solution
- `wrong_common_error.png` - Common error example
- `minimal_work.png` - Minimal steps shown
- `blurry.png` - Low quality image (tests error handling)
