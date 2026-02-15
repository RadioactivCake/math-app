import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..database import get_db
from ..models import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionHistoryResponse,
    SubmissionHistoryItem,
    SubmissionDetail,
    Feedback,
    StepAnalysis,
    ErrorResponse,
)
from ..services.ocr import vision_service
from ..services.evaluator import evaluator_service

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionResponse)
async def create_submission(submission: SubmissionCreate):
    """
    Submit a solution image for evaluation.

    1. Validates the problem exists
    2. Claude Vision: checks image quality + extracts math (single call)
    3. Claude: evaluates the extracted solution
    4. Stores and returns the result
    """
    # Get problem with answer
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, question, correct_answer FROM problems WHERE id = ?",
            (submission.problem_id,)
        )
        problem = cursor.fetchone()

    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    # Step 1: Claude Vision — quality check + OCR in one call
    vision_result = await vision_service.analyze(submission.image_data)

    # Handle API/system errors
    if vision_result.error:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO submissions (problem_id, image_data, extracted_text, is_correct, feedback)
                VALUES (?, ?, ?, ?, ?)
            """, (
                submission.problem_id,
                submission.image_data[:100] + "...",
                None,
                False,
                json.dumps({
                    "summary": f"Could not process your image: {vision_result.error}",
                    "steps_analysis": [],
                    "suggestions": ["Please try again in a moment"],
                    "encouragement": "Don't give up! This is a temporary issue."
                })
            ))
            submission_id = cursor.lastrowid

        return SubmissionResponse(
            id=submission_id,
            is_correct=False,
            extracted_work=None,
            feedback=Feedback(
                summary=f"Could not process your image: {vision_result.error}",
                steps_analysis=[],
                suggestions=["Please try again in a moment"],
                encouragement="Don't give up! This is a temporary issue."
            ),
        )

    # Handle quality check failure
    if not vision_result.readable:
        issues_text = ", ".join(vision_result.issues) if vision_result.issues else "Image quality too low"
        return SubmissionResponse(
            id=0,
            is_correct=False,
            extracted_work=None,
            feedback=Feedback(
                summary=f"Image quality check failed: {issues_text}",
                steps_analysis=[],
                suggestions=[vision_result.suggestion] if vision_result.suggestion else [
                    "Try taking the photo in better lighting",
                    "Make sure your work is clearly visible and in focus",
                    "Write your steps in a clear, top-to-bottom order"
                ],
                encouragement="No worries! Just retake the photo and try again."
            ),
            quality_failed=True
        )

    # Step 2: Claude — evaluate the extracted text
    eval_result = await evaluator_service.evaluate(
        question=problem["question"],
        correct_answer=problem["correct_answer"],
        extracted_text=vision_result.extracted_text
    )

    if not eval_result.success:
        feedback = Feedback(
            summary=f"We extracted your work but couldn't fully evaluate it: {eval_result.error}",
            steps_analysis=[
                StepAnalysis(
                    step="Your work",
                    evaluation="unclear",
                    comment=vision_result.extracted_text or "Work extracted but evaluation unavailable"
                )
            ],
            suggestions=["Please try again in a moment"],
            encouragement=f"The correct answer is: {problem['correct_answer']}"
        )

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO submissions (problem_id, image_data, extracted_text, is_correct, feedback)
                VALUES (?, ?, ?, ?, ?)
            """, (
                submission.problem_id,
                submission.image_data[:100] + "...",
                vision_result.extracted_text,
                False,
                json.dumps(feedback.model_dump())
            ))
            submission_id = cursor.lastrowid

        return SubmissionResponse(
            id=submission_id,
            is_correct=False,
            extracted_work=vision_result.extracted_text,
            feedback=feedback,
        )

    # Success — store complete result
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO submissions (problem_id, image_data, extracted_text, is_correct, feedback)
            VALUES (?, ?, ?, ?, ?)
        """, (
            submission.problem_id,
            submission.image_data[:100] + "...",
            vision_result.extracted_text,
            eval_result.is_correct,
            json.dumps(eval_result.feedback.model_dump())
        ))
        submission_id = cursor.lastrowid

    return SubmissionResponse(
        id=submission_id,
        is_correct=eval_result.is_correct,
        extracted_work=vision_result.extracted_text,
        feedback=eval_result.feedback,
    )


@router.get("", response_model=SubmissionHistoryResponse)
async def list_submissions(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0)
):
    """Get submission history with pagination."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get total count
        cursor.execute("SELECT COUNT(*) as count FROM submissions")
        total = cursor.fetchone()["count"]

        # Get submissions with problem info
        cursor.execute("""
            SELECT s.id, s.problem_id, p.question, s.is_correct, s.feedback, s.created_at
            FROM submissions s
            JOIN problems p ON s.problem_id = p.id
            ORDER BY s.created_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        rows = cursor.fetchall()

    submissions = []
    for row in rows:
        feedback_data = json.loads(row["feedback"]) if row["feedback"] else {}
        submissions.append(
            SubmissionHistoryItem(
                id=row["id"],
                problem_id=row["problem_id"],
                question=row["question"],
                is_correct=row["is_correct"],
                feedback_summary=feedback_data.get("summary", ""),
                created_at=row["created_at"]
            )
        )

    return SubmissionHistoryResponse(submissions=submissions, total=total)


@router.get("/{submission_id}", response_model=SubmissionDetail)
async def get_submission(submission_id: int):
    """Get full details of a specific submission."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, p.question, p.correct_answer
            FROM submissions s
            JOIN problems p ON s.problem_id = p.id
            WHERE s.id = ?
        """, (submission_id,))
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Submission not found")

    feedback_data = json.loads(row["feedback"]) if row["feedback"] else {
        "summary": "",
        "steps_analysis": [],
        "suggestions": []
    }

    # Reconstruct feedback object
    steps = [
        StepAnalysis(**step)
        for step in feedback_data.get("steps_analysis", [])
    ]

    feedback = Feedback(
        summary=feedback_data.get("summary", ""),
        steps_analysis=steps,
        suggestions=feedback_data.get("suggestions", []),
        encouragement=feedback_data.get("encouragement")
    )

    return SubmissionDetail(
        id=row["id"],
        problem_id=row["problem_id"],
        question=row["question"],
        correct_answer=row["correct_answer"],
        image_data=row["image_data"],
        extracted_text=row["extracted_text"],
        is_correct=row["is_correct"],
        feedback=feedback,
        created_at=row["created_at"]
    )
