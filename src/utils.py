import random
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .constants import part_of_speech_list
from .models import Word, FavoriteWord


async def get_random_words(session: AsyncSession):
    random_part_of_speech = random.choice(list(part_of_speech_list.keys()))
    query = select(Word).where(Word.part_of_speech == random_part_of_speech, Word.rating == "A1"
                               ).options(joinedload(Word.translation)).order_by(func.random()).limit(3)
    result = await session.execute(query)
    random_words = [random_word for random_word in result.scalars().all()]
    word_for_translate = random_words[0]
    random.shuffle(random_words)
    return word_for_translate, random_words


async def check_favorite_words(user_id: int, word_id: uuid4, session: AsyncSession):
    query = select(FavoriteWord).where(and_(FavoriteWord.user_id == user_id, FavoriteWord.word_id == word_id))
    result = await session.scalar(query)
    if result:
        return True
    else:
        return False


async def commit_changes(session: AsyncSession, message: str):
    try:
        await session.commit()
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"{message}")
