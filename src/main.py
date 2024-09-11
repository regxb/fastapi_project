import random
import uuid

from fastapi import FastAPI, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from fastapi.middleware.cors import CORSMiddleware

from .models import Word, User
from .utils import get_random_words
from .database import get_async_session

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/user")
async def create_user(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    user = User(telegram_id=telegram_id)
    session.add(user)
    await session.commit()


@app.get("/user")
async def get_user_list(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User))
    users_list = result.scalars().all()

    return [{"user_id": user.id, "user_rating": user.rating, "created_at": user.created_at} for user in users_list]


@app.get("/get-word/eng")
async def get_word(session: AsyncSession = Depends(get_async_session)):
    word_for_translate, random_words = await get_random_words(session)

    return {
        "word_for_translate": {'id': word_for_translate.id,
                               'name': word_for_translate.name},
        "other_words": [
            {'id': word.translation.id, 'name': word.translation.name} for word in random_words
        ]
    }


@app.get("/get-word/rus")
async def get_word(session: AsyncSession = Depends(get_async_session)):
    word_for_translate, random_words = await get_random_words(session)

    return {
        "word_for_translate": {'id': word_for_translate.id,
                               'name': word_for_translate.translation.name},
        "other_words": [
            {'id': word.id, 'name': word.name} for word in random_words
        ]
    }


@app.get("/check_answer")
async def check_answer(
        word_for_translate_id: uuid.UUID,
        user_choice_word_id: uuid.UUID,
        session: AsyncSession = Depends(get_async_session),
):
    query = select(Word).where(Word.id == word_for_translate_id)
    word_for_translate = await session.scalar(query)
    if word_for_translate is None:
        return f"Слово с id {word_for_translate_id} не найдено"
    if word_for_translate.translation_id == user_choice_word_id:
        return True
    return False
