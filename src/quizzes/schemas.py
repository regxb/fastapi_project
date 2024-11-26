from typing import List

from pydantic import BaseModel, UUID4

from src.schemas import WordInfo, SentenceInfo


class UserFavoriteWord(BaseModel):
    telegram_id: int
    word_id: UUID4


class RandomWordResponse(BaseModel):
    type: str
    word_for_translate: WordInfo
    other_words: List[WordInfo]
    in_favorite: bool


class RandomSentenceResponse(BaseModel):
    type: str
    sentence_for_translate: SentenceInfo
    words_for_sentence: List[str]
