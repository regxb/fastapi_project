from typing import List, Dict, Optional

from pydantic import BaseModel, ConfigDict

from src.schemas import WordInfo


class ExamAnswerResponse(BaseModel):
    success: bool
    message: str | None = None


class ExamSchema(BaseModel):
    exercise: dict
    user_progress: int
    total_progress: int
    attempts: int
