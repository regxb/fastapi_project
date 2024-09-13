from typing import Optional, Literal, List

from pydantic import BaseModel, UUID4


class WordInfo(BaseModel):
    id: UUID4
    name: str


class WordResponse(BaseModel):
    word_for_translate: WordInfo
    other_words: List[WordInfo]
