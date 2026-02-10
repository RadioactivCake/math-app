# Technical Design Document

## Overview

This document outlines the technical design for the Math Feedback Application - a web app where students upload photos of handwritten math solutions and receive AI-powered feedback on their reasoning process.

---

## 1. Architecture

### System Components

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│    Frontend     │────▶│    Backend      │────▶│    Database     │
│   (HTML/JS)     │     │   (FastAPI)     │     │    (SQLite)     │
│                 │     │                 │     │                 │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
           ┌─────────────────┐      ┌─────────────────┐
           │   Mathpix API   │      │   Claude API    │
           │   (OCR)         │      │   (Evaluation)  │
           └─────────────────┘      └─────────────────┘
```

### Technology Choices

| Component | Choice | Rationale |
|-----------|--------|-----------|
| Frontend | Vanilla HTML/CSS/JS | Simple, no build step, fast to develop |
| Backend | Python + FastAPI | Async support, automatic OpenAPI docs, easy API design |
| Database | SQLite | Zero config, file-based, sufficient for this scope |
| OCR | Claude Vision API | Native handwriting reading, same API key as evaluation |
| LLM | Claude API | Strong reasoning capabilities for pedagogical feedback |

### Request Flow

1. User selects topic → Frontend fetches problems from backend
2. User uploads image → Backend receives base64-encoded image
3. Backend sends image to Mathpix → Receives extracted LaTeX/text
4. Backend constructs prompt with problem + extracted work + correct answer
5. Backend sends to Claude → Receives structured feedback
6. Backend stores submission and returns feedback to frontend
7. Frontend displays feedback to user

---

## 2. Data Model

### Entity Relationship

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│   Topic     │──1:N──│   Problem   │──1:N──│ Submission  │
└─────────────┘       └─────────────┘       └─────────────┘
```

### Tables

#### topics
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT (PK) | Unique identifier (e.g., "fractions-addition") |
| name | TEXT | Display name |
| description | TEXT | Topic description |
| grade_level | INTEGER | Target grade level |

#### problems
| Column | Type | Description |
|--------|------|-------------|
| id | TEXT (PK) | Unique identifier (e.g., "frac-add-001") |
| topic_id | TEXT (FK) | Reference to topic |
| question | TEXT | The math problem text |
| correct_answer | TEXT | Expected correct answer |

#### submissions
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER (PK) | Auto-increment ID |
| problem_id | TEXT (FK) | Reference to problem |
| image_data | TEXT | Base64-encoded image (or file path) |
| extracted_text | TEXT | OCR result from Mathpix |
| extracted_latex | TEXT | LaTeX representation from Mathpix |
| is_correct | BOOLEAN | Whether final answer was correct |
| feedback | TEXT | LLM-generated feedback |
| created_at | TIMESTAMP | Submission time |

---

## 3. API Design

### Endpoints

#### GET /api/topics
Returns list of available math topics.

**Response:**
```json
{
  "topics": [
    {
      "id": "fractions-addition",
      "name": "Adding Fractions",
      "description": "Adding fractions with like and unlike denominators",
      "grade_level": 5,
      "problem_count": 3
    }
  ]
}
```

#### GET /api/topics/{topic_id}/problems
Returns problems for a specific topic.

**Response:**
```json
{
  "topic": {
    "id": "fractions-addition",
    "name": "Adding Fractions"
  },
  "problems": [
    {
      "id": "frac-add-001",
      "question": "What is 1/4 + 1/2?"
    }
  ]
}
```

#### GET /api/problems/{problem_id}
Returns a specific problem (without the answer).

**Response:**
```json
{
  "id": "frac-add-001",
  "topic_id": "fractions-addition",
  "question": "What is 1/4 + 1/2?"
}
```

#### POST /api/submissions
Submit a solution image for evaluation.

**Request:**
```json
{
  "problem_id": "frac-add-001",
  "image_data": "base64-encoded-image-string"
}
```

**Response:**
```json
{
  "id": 1,
  "is_correct": true,
  "extracted_work": "1/4 + 1/2 = 1/4 + 2/4 = 3/4",
  "feedback": {
    "summary": "Correct! Great work.",
    "steps_analysis": [
      {
        "step": "Found common denominator of 4",
        "evaluation": "correct",
        "comment": "Good recognition that 4 is the LCD"
      },
      {
        "step": "Converted 1/2 to 2/4",
        "evaluation": "correct",
        "comment": "Correct conversion"
      },
      {
        "step": "Added numerators: 1 + 2 = 3",
        "evaluation": "correct",
        "comment": "Correct addition"
      }
    ],
    "suggestions": []
  }
}
```

#### GET /api/submissions
Returns submission history.

**Query params:** `?limit=10&offset=0`

**Response:**
```json
{
  "submissions": [
    {
      "id": 1,
      "problem_id": "frac-add-001",
      "question": "What is 1/4 + 1/2?",
      "is_correct": true,
      "feedback_summary": "Correct! Great work.",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 5
}
```

#### GET /api/submissions/{submission_id}
Returns full details of a specific submission.

---

## 4. LLM Strategy

### Prompt Design

The evaluation prompt will be structured to elicit pedagogically useful feedback:

```
You are a supportive math tutor evaluating a student's work.

PROBLEM: {question}
CORRECT ANSWER: {correct_answer}
STUDENT'S WORK (extracted from handwriting):
{extracted_text}

Analyze the student's solution and provide feedback. Focus on:
1. Whether their final answer is correct
2. The reasoning shown in their work
3. Any errors in their process (even if the answer is correct)
4. What they did well

Respond in JSON format:
{
  "is_correct": boolean,
  "summary": "Brief 1-2 sentence summary",
  "steps_analysis": [
    {
      "step": "What the student did",
      "evaluation": "correct|incorrect|unclear",
      "comment": "Specific feedback on this step"
    }
  ],
  "suggestions": ["Things to improve or remember"],
  "encouragement": "Positive closing note"
}

Be encouraging but honest. If work is minimal, note that showing steps helps catch errors.
```

### Pedagogical Principles

1. **Process over answer**: Emphasize reasoning, not just correctness
2. **Specific feedback**: Point to exact steps, not vague comments
3. **Growth mindset**: Frame errors as learning opportunities
4. **Scaffolding**: Suggest next steps without giving away answers
5. **Encouragement**: Always acknowledge effort and correct elements

### Handling Edge Cases

| Scenario | LLM Instruction |
|----------|-----------------|
| Correct answer, no work shown | Acknowledge correctness, encourage showing steps |
| Wrong answer, correct process | Highlight good reasoning, point to calculation error |
| Unreadable/unclear work | Ask for clarification, provide general guidance |
| Unconventional but valid method | Validate the approach, compare to standard method |

---

## 5. Error Handling

### OCR Failures (Mathpix)

| Error Type | Detection | User Message | Backend Action |
|------------|-----------|--------------|----------------|
| Low confidence | Mathpix confidence < 0.5 | "We had trouble reading your work. Try a clearer photo." | Log, still attempt evaluation |
| Empty result | No text extracted | "No mathematical content detected. Please upload a photo of your work." | Return early, don't call LLM |
| API error | HTTP 4xx/5xx | "Image processing temporarily unavailable. Please try again." | Log error, return 503 |
| Invalid image | Format not supported | "Please upload a JPEG or PNG image." | Return 400 |

### LLM Failures (Claude)

| Error Type | Detection | User Message | Backend Action |
|------------|-----------|--------------|----------------|
| Rate limit | HTTP 429 | "High demand. Please try again in a moment." | Implement retry with backoff |
| Invalid response | JSON parse fails | "Unable to generate feedback. Please try again." | Log, return generic feedback |
| API error | HTTP 5xx | "Feedback service temporarily unavailable." | Log, return 503 |

### Input Validation

- Maximum image size: 10MB
- Allowed formats: JPEG, PNG
- Problem ID must exist in database
- Rate limiting: 10 submissions per minute per session

### Graceful Degradation

If Mathpix fails but we have partial text:
1. Attempt evaluation with available text
2. Include disclaimer in feedback: "Note: Some of your work may not have been captured clearly."

If LLM fails:
1. Still store submission with OCR result
2. Return: "We couldn't generate detailed feedback, but your work has been saved. The correct answer is {answer}."

---

## 6. Future Considerations

Items explicitly out of scope for initial implementation, but worth noting:

- **User authentication**: Currently session-based only
- **Multiple attempts per problem**: Could track improvement over time
- **Hint system**: Progressive hints before showing answer
- **Teacher dashboard**: View class-wide analytics
- **Mobile optimization**: Camera integration for direct capture

---

## 7. Implementation Status

| Step | Task | Status |
|------|------|--------|
| 1 | Database setup and seeding | ✅ Complete |
| 2 | Basic API endpoints (topics, problems) | ✅ Complete |
| 3 | OCR integration (Claude Vision - Handwriting) | ✅ Complete |
| 4 | Claude integration with evaluation prompt | ✅ Complete |
| 5 | Submission endpoint (full flow) | ✅ Complete |
| 6 | Frontend: topic selection and problem display | ✅ Complete |
| 7 | Frontend: image upload with preview | ✅ Complete |
| 8 | Frontend: feedback display | ✅ Complete |
| 9 | Frontend: submission history | ✅ Complete |
| 10 | Error handling and edge cases | ✅ Complete |
| 11 | Testing with provided images | ⏳ Pending |

### Backend Files

```
backend/
├── .env.example           # Environment variables template
├── requirements.txt       # Python dependencies
└── app/
    ├── __init__.py
    ├── main.py            # FastAPI application entry point
    ├── database.py        # SQLite setup and operations
    ├── models.py          # Pydantic models for API
    ├── routers/
    │   ├── __init__.py
    │   ├── topics.py      # Topics endpoints
    │   ├── problems.py    # Problems endpoints
    │   └── submissions.py # Submissions endpoints
    └── services/
        ├── __init__.py
        ├── ocr.py         # Claude Vision OCR (handwriting extraction)
        └── evaluator.py   # Claude evaluation service
```

### Frontend Files

```
frontend/
├── index.html             # Main HTML page (single-page app)
└── src/
    ├── app.js             # Application logic (API calls, UI management)
    └── styles.css         # Responsive styling
```
