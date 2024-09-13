from datetime import datetime

from pydantic import BaseModel


class UserCreate(BaseModel):
    telegram_id: int


class UserInfo(BaseModel):
    id: int
    telegram_id: int
    rating: str
    created_at: datetime
