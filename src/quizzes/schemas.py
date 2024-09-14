from typing import List

from pydantic import BaseModel

from src.schemas import WordInfo


class AnswerResponse(BaseModel):
    word_for_translate: WordInfo
    other_words: List[WordInfo]
