import uuid

from pydantic import BaseModel


class CompetitionRoomSchema(BaseModel):
    telegram_id: int
    room_id: int


class CompetitionAnswerSchema(BaseModel):
    word_for_translate_id: uuid.UUID
    user_word_id: uuid.UUID
    telegram_id: int
    room_id: int
