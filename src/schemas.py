import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class UserCreate(BaseModel):
    telegram_id: int


class UsersList(BaseModel):
    id: int
    telegram_id: int
    rating: str
    created_at: datetime

    class Config:
        orm_mode = True


class Answer(BaseModel):
    word_for_translate_id: uuid.UUID
    user_choice_word_id: uuid.UUID
