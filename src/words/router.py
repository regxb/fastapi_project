import uuid
from typing import Optional

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Word
from src.words.schemas import WordResponse, WordInfo
from src.utils import get_random_words
from src.database import get_async_session

router = APIRouter(
    prefix="/word",
    tags=["word"]
)


@router.get("/quiz", response_model=WordResponse)
async def get_random_word(language: str, session: AsyncSession = Depends(get_async_session)):
    word_for_translate, random_words = await get_random_words(session)

    if language == "eng":
        response_data = WordResponse(
            word_for_translate=WordInfo(id=word_for_translate.id, name=word_for_translate.name),
            other_words=[WordInfo(id=word.translation.id, name=word.translation.name) for word in random_words]
        )

    elif language == "ru":
        response_data = WordResponse(
            word_for_translate=WordInfo(id=word_for_translate.id, name=word_for_translate.translation.name),
            other_words=[WordInfo(id=word.translation.id, name=word.name) for word in random_words]
        )
    else:
        raise HTTPException(status_code=404, detail="Язык не найден")

    return response_data


@router.get("/check-answer", response_model=Optional[bool])
async def check_answer(
        word_for_translate_id: uuid.UUID,
        user_choice_word_id: uuid.UUID,
        session: AsyncSession = Depends(get_async_session),
):
    query = select(Word).where(Word.id == word_for_translate_id)
    word_for_translate = await session.scalar(query)
    if word_for_translate is None:
        raise HTTPException(status_code=404, detail=f"Слово с id {word_for_translate_id} не найдено")
    if word_for_translate.translation_id == user_choice_word_id:
        return True
    return False
