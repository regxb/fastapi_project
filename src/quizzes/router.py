import uuid
from typing import Optional, List

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.constants import part_of_speech_list
from src.models import Word, FavoriteWord, User
from src.quizzes.schemas import AnswerResponse, FavoriteWordBase
from src.schemas import WordInfo
from src.utils import get_random_words
from src.database import get_async_session

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)


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


@router.get("/random-word", response_model=AnswerResponse)
async def get_random_word(language: str, session: AsyncSession = Depends(get_async_session)):
    word_for_translate, random_words = await get_random_words(session)

    if language == "eng":
        response_data = AnswerResponse(
            word_for_translate=WordInfo(id=word_for_translate.id, name=word_for_translate.name),
            other_words=[WordInfo(id=word.translation.id, name=word.translation.name) for word in random_words]
        )

    elif language == "ru":
        response_data = AnswerResponse(
            word_for_translate=WordInfo(id=word_for_translate.id, name=word_for_translate.translation.name),
            other_words=[WordInfo(id=word.translation.id, name=word.name) for word in random_words]
        )
    else:
        raise HTTPException(status_code=404, detail="Язык не найден")

    return response_data


@router.get("/available-parts-of-speech", response_model=List[str])
async def get_available_parts_of_speech():
    return part_of_speech_list


@router.get("/{part_of_speech}", response_model=AnswerResponse)
async def get_word_from_part_of_speech(part_of_speech: str, session: AsyncSession = Depends(get_async_session)):
    if part_of_speech not in part_of_speech_list:
        raise HTTPException(status_code=404, detail="Часть речи не найдена")
    query = (select(Word)
             .options(joinedload(Word.translation))
             .where(Word.part_of_speech == part_of_speech).order_by(func.random())
             .limit(3))
    result = await session.execute(query)
    words = result.scalars().all()
    word_for_translate = words[0]

    response_data = AnswerResponse(
        word_for_translate=WordInfo(id=word_for_translate.id, name=word_for_translate.translation.name),
        other_words=[WordInfo(id=word.translation_id, name=word.name) for word in words]
    )

    return response_data


@router.post("/favorite-word")
async def add_favorite_word(data: FavoriteWordBase, session: AsyncSession = Depends(get_async_session)):
    query = select(User).where(User.telegram_id == data.telegram_id)
    result = await session.scalar(query)
    if result:
        user_id = result.id
    else:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    word = await session.scalar(select(Word).where(Word.id == data.word_id))
    if word is None:
        raise HTTPException(status_code=404, detail="Слово не найдено")
    query = (select(FavoriteWord).where(and_(FavoriteWord.word_id == data.word_id, FavoriteWord.user_id == user_id)))
    result = await session.execute(query)
    user_favorite_words = result.scalars().all()
    if user_favorite_words:
        raise HTTPException(status_code=201, detail="Данное слово уже добавлено пользователем")
    new_favorite_word = FavoriteWord(
        user_id=user_id,
        word_id=data.word_id
    )
    session.add(new_favorite_word)
    await session.commit()
    return {"message": "Слово успешно добавлено"}
