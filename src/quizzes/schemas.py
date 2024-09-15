from typing import List

from pydantic import BaseModel, UUID4

from src.schemas import WordInfo


class AnswerResponse(BaseModel):
    word_for_translate: WordInfo
    other_words: List[WordInfo]


class FavoriteWordBase(BaseModel):
    telegram_id: int
    word_id: UUID4
