from pydantic import BaseModel


class ExamData(BaseModel):
    telegram_id: int
