from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..models import Problem

router = APIRouter(prefix="/api/problems", tags=["problems"])


@router.get("/{problem_id}", response_model=Problem)
async def get_problem(problem_id: str):
    """Get a specific problem (without the answer)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, topic_id, question FROM problems WHERE id = ?",
            (problem_id,)
        )
        row = cursor.fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="Problem not found")

    return Problem(
        id=row["id"],
        topic_id=row["topic_id"],
        question=row["question"]
    )
