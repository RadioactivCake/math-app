from fastapi import APIRouter, HTTPException

from ..database import get_db
from ..models import TopicListResponse, TopicWithCount, TopicProblemsResponse, Topic, Problem

router = APIRouter(prefix="/api/topics", tags=["topics"])


@router.get("", response_model=TopicListResponse)
async def list_topics():
    """Get all available math topics with problem counts."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT t.id, t.name, t.description, t.grade_level,
                   COUNT(p.id) as problem_count
            FROM topics t
            LEFT JOIN problems p ON t.id = p.topic_id
            GROUP BY t.id
            ORDER BY t.grade_level, t.name
        """)
        rows = cursor.fetchall()

    topics = [
        TopicWithCount(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            grade_level=row["grade_level"],
            problem_count=row["problem_count"]
        )
        for row in rows
    ]

    return TopicListResponse(topics=topics)


@router.get("/{topic_id}/problems", response_model=TopicProblemsResponse)
async def get_topic_problems(topic_id: str):
    """Get all problems for a specific topic."""
    with get_db() as conn:
        cursor = conn.cursor()

        # Get topic
        cursor.execute(
            "SELECT id, name, description, grade_level FROM topics WHERE id = ?",
            (topic_id,)
        )
        topic_row = cursor.fetchone()

        if not topic_row:
            raise HTTPException(status_code=404, detail="Topic not found")

        # Get problems (without answers)
        cursor.execute(
            "SELECT id, topic_id, question FROM problems WHERE topic_id = ?",
            (topic_id,)
        )
        problem_rows = cursor.fetchall()

    topic = Topic(
        id=topic_row["id"],
        name=topic_row["name"],
        description=topic_row["description"],
        grade_level=topic_row["grade_level"]
    )

    problems = [
        Problem(
            id=row["id"],
            topic_id=row["topic_id"],
            question=row["question"]
        )
        for row in problem_rows
    ]

    return TopicProblemsResponse(topic=topic, problems=problems)
