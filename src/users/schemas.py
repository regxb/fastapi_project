from datetime import datetime

from pydantic import BaseModel, field_validator, model_validator

from src.constants import AvailableLanguages


class UserCreate(BaseModel):
    telegram_id: int
    learning_language_from_id: int
    learning_language_to_id: int

    @field_validator("learning_language_to_id")
    def check_language_to_exists(cls, learning_language_to_id):
        if not AvailableLanguages.__contains__(learning_language_to_id):
            raise ValueError(f"Язык с id{learning_language_to_id} не найден")
        return learning_language_to_id

    @field_validator("learning_language_from_id")
    def check_language_from_exists(cls, learning_language_from_id):
        if not AvailableLanguages.__contains__(learning_language_from_id):
            raise ValueError(f"Язык с id{learning_language_from_id} не найден")
        return learning_language_from_id

    @model_validator(mode='before')
    def check_different_languages(cls, values):
        from_id = values.get("learning_language_from_id")
        to_id = values.get("learning_language_to_id")

        if from_id == to_id:
            raise ValueError("Языки обучения не могут быть одинаковыми.")
        return values


class UserInfo(BaseModel):
    id: int
    telegram_id: int
    rating: str
    learning_language_from_id: int
    learning_language_to_id: int
    created_at: datetime


class UserUpdate(UserCreate):
    ...
