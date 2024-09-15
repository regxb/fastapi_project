from typing import List

from pydantic import BaseModel

from src.schemas import WordInfo


class ExamData(BaseModel):
    telegram_id: int


class ExamAnswerResponse(BaseModel):
    word_for_translate: WordInfo
    other_words: List[WordInfo]
    exam_id: int
    exam_way: int
