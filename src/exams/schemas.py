from pydantic import BaseModel


class ExamAnswerResponseSchema(BaseModel):
    success: bool
    message: str | None = None


class ExamSchema(BaseModel):
    type: str
    exercise: dict
    user_progress: int
    total_progress: int
    attempts: int
