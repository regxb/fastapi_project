import uuid
from typing import List

from pydantic import BaseModel

from src.quizzes.schemas import RandomWordResponse


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
    username: str
    user_photo_url: str
    success: bool


class UserStatsSchema(BaseModel):
    username: str
    user_photo_url: str
    points: int


class CompetitionsAnswersSchema(BaseModel):
    type: str
    answered_user: AnsweredUsersSchema
    selected_word_id: uuid.UUID
    correct_word_id: uuid.UUID
    users: List[UserStatsSchema]
    new_question: RandomWordResponse
