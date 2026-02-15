# Technical Design Document

## Overview

A web app where students photograph handwritten math solutions and receive AI feedback on their reasoning process. The goal is pedagogical — feedback should help students understand *where* their thinking went right or wrong, not just tell them the answer.

## Architecture

The system is intentionally simple: a FastAPI backend serves a vanilla HTML/JS frontend, with SQLite for storage. There are no build tools, no ORM, no authentication layer. This keeps the focus on the core feedback loop.

The interesting part is the AI pipeline. When a student submits a photo, the backend makes two Claude API calls in sequence:

1. **Vision call** — sends the image to Claude Vision, which both checks image quality and extracts the handwritten math. If the image is unreadable (blurry, dark, messy layout), it stops here and asks the student to retake the photo. This prevents garbage-in-garbage-out from reaching the evaluator.

2. **Evaluation call** — sends the extracted text (along with the problem and correct answer) to Claude for analysis. The prompt is designed to produce structured feedback: step-by-step analysis, identification of errors, suggestions, and encouragement.

Originally the spec called for Mathpix OCR, but during development we found that Claude Vision handles handwriting well enough on its own, and using a single API key for everything simplifies deployment. We also tried OCR.space (free tier was unreliable for handwriting, 1MB limit).

## Data Model

Three tables: `topics` → `problems` → `submissions`. Topics group problems by subject (fractions, linear equations, percentages). Each problem has a question and correct answer. Submissions store the image (truncated base64), extracted text, correctness, and the full feedback JSON.

Feedback is stored as a JSON string rather than normalized tables because the structure varies per evaluation and we only ever read it back as a whole — no need to query individual steps.

## API Design

The API follows a straightforward REST pattern. `GET /api/topics` and `/api/topics/{id}/problems` handle browsing. `POST /api/submissions` runs the full pipeline. `GET /api/submissions` provides history with pagination. A `/health` endpoint reports whether the AI services are configured.

The submission endpoint returns a `quality_failed` flag when the image is rejected, which the frontend uses to show an amber warning card with retake suggestions instead of the normal feedback display.

## LLM Strategy

The evaluation prompt frames Claude as a "supportive math tutor" and asks for JSON output with specific fields: summary, step-by-step analysis (each step marked correct/incorrect/unclear with a comment), improvement suggestions, and encouragement. This structure gives the frontend enough to render color-coded feedback.

The prompt emphasizes process over correctness — a student who gets the wrong answer but shows good reasoning should get different feedback than one who writes only the answer. Edge cases like minimal work, unconventional methods, and calculation errors in otherwise sound reasoning all get specific handling instructions in the prompt.

## Error Handling

The system degrades gracefully at each stage. If the Vision call detects a bad image, the student gets a friendly suggestion to retake the photo — no evaluation is attempted. If OCR succeeds but evaluation fails, the extracted text is still saved and the student sees their work plus the correct answer. API errors (auth, rate limit, server errors) all return appropriate messages rather than stack traces.

The image quality check is deliberately strict ("when in doubt, reject") because feeding a bad extraction to the evaluator produces confusing feedback. It's better to ask for a retake than to give feedback on misread text.

## Scope Decisions

- No authentication — single-user for simplicity
- SQLite over PostgreSQL — zero config, sufficient for this scale
- Base64 images in the database — simple but wouldn't scale; production would use file storage
- No rate limiting or input size validation — noted as future work
- Crossed-out content detection was explored but Sonnet's visual reasoning isn't reliable enough for it yet — documented in conversation logs as a known limitation
