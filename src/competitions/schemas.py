import uuid
from typing import List

from pydantic import BaseModel


class CompetitionRoomSchema(BaseModel):
    telegram_id: int
    room_id: int


class CompetitionAnswerSchema(BaseModel):
    word_for_translate_id: uuid.UUID
    user_word_id: uuid.UUID
    telegram_id: int
    room_id: int


class CompetitionsSchema(BaseModel):
    telegram_id: int
    language_from_id: int
    language_to_id: int


class AnsweredUsersSchema(BaseModel):
    telegram_id: int
    success: bool


class UserStatsSchema(BaseModel):
    telegram_id: int
    points: int


class CompetitionsAnswersSchema(BaseModel):
    answered_user: AnsweredUsersSchema
    selected_word_id: uuid.UUID
    correct_word_id: uuid.UUID
    users: List[UserStatsSchema]
