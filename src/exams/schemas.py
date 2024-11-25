from typing import List, Dict, Optional

from pydantic import BaseModel, ConfigDict

from src.schemas import WordInfo


class ExamAnswerResponse(BaseModel):
    success: bool
    message: Optional[str]
