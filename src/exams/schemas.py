from typing import List

from pydantic import BaseModel

from src.schemas import WordInfo


class ExamData(BaseModel):
    telegram_id: int


class CheckExamAnswerResponse(BaseModel):
    word_for_translate: WordInfo
    other_words: List[WordInfo]
    exam_way: int
