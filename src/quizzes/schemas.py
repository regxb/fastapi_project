from typing import List

from pydantic import BaseModel, UUID4

from src.schemas import WordInfo


# class AnswerResponse(BaseModel):
#     word_for_translate: WordInfo
#     other_words: List[WordInfo]
#     in_favorites: bool
#
#
# class SentenceInfo(BaseModel):
#     name: str
#     id: UUID4
#
#
# class SentenceAnswerResponse(BaseModel):
#     sentence_for_translate: SentenceInfo
#     other_words: List[str]
#
#
# class FavoriteAnswerResponse(BaseModel):
#     word_for_translate: WordInfo
#     other_words: List[WordInfo]
#
#
# class FavoriteWordBase(BaseModel):
#     telegram_id: int
#     word_id: UUID4


class RandomWordResponse(BaseModel):
    word_for_translate: WordInfo
    other_words: List[WordInfo]
