from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Topic models
class Topic(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    grade_level: Optional[int] = None


class TopicWithCount(Topic):
    problem_count: int


class TopicListResponse(BaseModel):
    topics: list[TopicWithCount]


# Problem models
class Problem(BaseModel):
    id: str
    topic_id: str
    question: str


class ProblemWithAnswer(Problem):
    correct_answer: str


class TopicProblemsResponse(BaseModel):
    topic: Topic
    problems: list[Problem]


# Feedback models
class StepAnalysis(BaseModel):
    step: str
    evaluation: str  # "correct", "incorrect", "unclear"
    comment: str


class Feedback(BaseModel):
    summary: str
    steps_analysis: list[StepAnalysis]
    suggestions: list[str]
    encouragement: Optional[str] = None


# Submission models
class SubmissionCreate(BaseModel):
    problem_id: str
    image_data: str  # base64 encoded image


class SubmissionResponse(BaseModel):
    id: int
    is_correct: bool
    extracted_work: Optional[str] = None
    feedback: Feedback
    quality_failed: bool = False


class SubmissionHistoryItem(BaseModel):
    id: int
    problem_id: str
    question: str
    is_correct: bool
    feedback_summary: str
    created_at: str


class SubmissionHistoryResponse(BaseModel):
    submissions: list[SubmissionHistoryItem]
    total: int


class SubmissionDetail(BaseModel):
    id: int
    problem_id: str
    question: str
    correct_answer: str
    image_data: Optional[str] = None
    extracted_text: Optional[str] = None
    is_correct: bool
    feedback: Feedback
    created_at: str


# Error models
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
