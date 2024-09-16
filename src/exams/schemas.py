from typing import List, Dict

from pydantic import BaseModel, ConfigDict

from src.schemas import WordInfo


class ExamData(BaseModel):
    telegram_id: int


class ExamAnswerResponse(BaseModel):
    word_for_translate: WordInfo
    other_words: List[WordInfo]
    exam_id: int
    exam_way: int
    in_favorites: bool


class ExamStatistic(BaseModel):
    exams_qty: int
    questions_qty: int
    fail_words: List
