from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from src.constants import AvailableLanguages


class UserCreate(BaseModel):
    telegram_id: int
    learning_language_from_id: AvailableLanguages
    learning_language_to_id: AvailableLanguages
    photo_url: str
    username: str
    first_name: str

    @model_validator(mode="before")
    def check_different_languages(cls, values):
        if values['learning_language_from_id'] == values['learning_language_to_id']:
            raise ValueError("Языки обучения не могут быть одинаковыми.")
        return values


class UserInfo(BaseModel):
    id: int
    telegram_id: int
    photo_url: str
    username: str
    first_name: str
    rating: str
    learning_language_from_id: AvailableLanguages
    learning_language_to_id: AvailableLanguages
    created_at: datetime


class UserUpdate(BaseModel):
    telegram_id: int
    learning_language_from_id: AvailableLanguages
    learning_language_to_id: AvailableLanguages

    @model_validator(mode="before")
    def check_different_languages(cls, values):
        if values['learning_language_from_id'] == values['learning_language_to_id']:
            raise ValueError("Языки обучения не могут быть одинаковыми.")
        return values


class UsersSchema(BaseModel):
    users_count: int
    users: list[UserInfo]
