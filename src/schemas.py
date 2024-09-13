import uuid
from datetime import datetime
from typing import Optional, Literal, List

from pydantic import BaseModel, UUID4


class UserCreate(BaseModel):
    telegram_id: int


class UserInfo(BaseModel):
    id: int
    telegram_id: int
    rating: str
    created_at: datetime
