from pydantic import BaseModel
from typing import List, Optional


class Question(BaseModel):
    id: str
    topic: str
    difficulty: int  # 1-5
    text: str


class Answer(BaseModel):
    question_id: str
    text: str


class Evaluation(BaseModel):
    technical_accuracy: int
    depth: int
    communication: int
    problem_solving: int
    confidence: int
    overall: int
    decision: str  # "increase_difficulty" | "same" | "decrease_difficulty" | "follow_up"


class InterviewSession(BaseModel):
    id: str
    candidate_id: str
    current_difficulty: int = 3
    history: List[dict] = []
    status: str = "in_progress"  # in_progress | completed
