import uuid
import random
from typing import Optional, List, Dict

from fastapi import Depends, HTTPException, APIRouter, Query
from sqlalchemy import select, func, and_, or_, union, alias
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.constants import part_of_speech_list
from src.models import Word, TranslationWord, User, FavoriteWord
from src.quizzes.query import get_random_word_for_translate, get_random_words, get_random_user_favorite_word, \
    check_word_in_favorite
from src.quizzes.schemas import RandomWordResponse, UserFavoriteWord
from src.schemas import WordInfo
# from src.utils import get_random_words, check_favorite_words
from src.database import get_async_session
from src.users.query import get_user

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)

languages = {"ru": 1, "en": 2}


@router.get("/check-answer", response_model=bool)
async def check_answer(
        word_for_translate_id: uuid.UUID,
        user_word_id: uuid.UUID,
        session: AsyncSession = Depends(get_async_session)
):
    word = await session.get(TranslationWord, user_word_id)
    return word_for_translate_id == word.word_id


@router.get("/random-word", response_model=RandomWordResponse)
async def get_random_word(
        telegram_id: int,
        language_from: str,
        language_to: str,
        session: AsyncSession = Depends(get_async_session)):
    language_from_id = languages.get(language_from)
    language_to_id = languages.get(language_to)

    if language_from_id and language_to_id:
        word_for_translate = await get_random_word_for_translate(session, language_from_id)
        other_words = await get_random_words(session, language_to_id, word_for_translate.id)
        other_words.append(word_for_translate.translation)
        random.shuffle(other_words)

        user = await get_user(session, telegram_id)
        in_favorite = await check_word_in_favorite(session, word_for_translate.id, user.id)

        response = RandomWordResponse(
            word_for_translate=WordInfo(name=word_for_translate.name, id=word_for_translate.id),
            other_words=[WordInfo(name=w.name, id=w.id) for w in other_words],
            in_favorite=in_favorite
        )
        return response
    raise HTTPException(status_code=404, detail="Язык не найден")


@router.post("/favorite-word")
async def add_favorite_word(data: UserFavoriteWord, session: AsyncSession = Depends(get_async_session)):
    user = await get_user(session, data.telegram_id)
    word = await session.get(Word, data.word_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if word is None:
        raise HTTPException(status_code=404, detail="Слово не найдено")
    query = (select(FavoriteWord).where(and_(FavoriteWord.word_id == data.word_id, FavoriteWord.user_id == user.id)))
    user_favorite_words = await session.scalar(query)
    if user_favorite_words:
        raise HTTPException(status_code=201, detail="Данное слово уже добавлено пользователем")
    new_favorite_word = FavoriteWord(
        user_id=user.id,
        word_id=word.id
    )
    session.add(new_favorite_word)
    try:
        await session.commit()
        return {"message": "Слово успешно добавлено"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Ошибка при добавлении слова в избранное")


@router.delete("/favorite-word")
async def delete_favorite_word(data: UserFavoriteWord, session: AsyncSession = Depends(get_async_session)):
    query = (select(FavoriteWord)
             .join(FavoriteWord.user)
             .where(and_(User.telegram_id == data.telegram_id, FavoriteWord.word_id == data.word_id)))
    user_favorite_word = await session.scalar(query)

    if user_favorite_word is None:
        raise HTTPException(status_code=404, detail="У пользователя нет такого слова в избранном")
    await session.delete(user_favorite_word)
    await session.commit()
    return {"message": "Слово было удалено"}


@router.get("/favorite-word", response_model=RandomWordResponse)
async def get_random_favorite_word(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    user = await get_user(session, telegram_id)
    random_user_favorite_word = await get_random_user_favorite_word(session, user.id)
    translate_to_language_id = random_user_favorite_word.word.translation.to_language_id
    other_words = await get_random_words(session, translate_to_language_id, random_user_favorite_word.word.id)
    other_words.append(random_user_favorite_word.word.translation)
    random.shuffle(other_words)

    response = RandomWordResponse(
        word_for_translate=WordInfo(name=random_user_favorite_word.word.name, id=random_user_favorite_word.word_id),
        other_words=[WordInfo(name=w.name, id=w.id) for w in other_words],
        in_favorite=True
    )
    return response


#
#
# @router.get("/part_of_speech", response_model=AnswerResponse)
# async def get_word_from_part_of_speech(
#         part_of_speech: str,
#         telegram_id: int,
#         session: AsyncSession = Depends(get_async_session)):
#     if part_of_speech not in part_of_speech_list:
#         raise HTTPException(status_code=404, detail="Часть речи не найдена")
#
#     query = (select(Word)
#              .options(joinedload(Word.translation))
#              .where(Word.part_of_speech == part_of_speech).order_by(func.random())
#              .limit(3))
#     result = await session.execute(query)
#     words = result.scalars().all()
#     word_for_translate = words[0]
#     user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
#     in_favorites = await check_favorite_words(user_id=user.id, word_id=word_for_translate.id, session=session)
#
#     response_data = AnswerResponse(
#         word_for_translate=WordInfo(id=word_for_translate.id, name=word_for_translate.translation.name),
#         other_words=[WordInfo(id=word.translation_id, name=word.name) for word in words],
#         in_favorites=in_favorites
#     )
#
#     return response_data
#
#
# @router.post("/add-word")
# async def add_word(
#         word_ru: str,
#         word_eng: str,
#         part_of_speech: str,
#         rating: str,
#         session: AsyncSession = Depends(get_async_session)):
#     new_translation_word = TranslationWord(name=word_ru)
#     session.add(new_translation_word)
#     await session.flush()
#
#     new_word = Word(name=word_eng, part_of_speech=part_of_speech, translation_id=new_translation_word.id, rating=rating)
#     session.add(new_word)
#     await session.commit()
#
#
# @router.post("/add-sentence")
# async def add_sentence(
#         sentence_en: str,
#         sentence_ru: str,
#         session: AsyncSession = Depends(get_async_session)):
#     new_translation_sentence = TranslationSentence(
#         name=sentence_ru,
#     )
#     session.add(new_translation_sentence)
#     await session.flush()
#
#     new_sentence = Sentence(
#         name=sentence_en,
#         translation_id=new_translation_sentence.id
#     )
#     session.add(new_sentence)
#     await session.commit()
#
#
# @router.get("/get-random-sentence", response_model=SentenceAnswerResponse)
# async def get_random_sentence(language: str, session: AsyncSession = Depends(get_async_session)):
#     query = select(Sentence).options(joinedload(Sentence.translation)).order_by(func.random()).limit(1)
#     sentence = await session.scalar(query)
#     if language == "ru":
#         sentence_words = sentence.translation.name.split()
#         query = await session.execute(select(TranslationWord)
#                                       .where(TranslationWord.name.notin_(sentence_words))
#                                       .order_by(func.random()).limit(random.randint(1, 3)))
#         result = query.scalars().all()
#         other_words = [w.name for w in result]
#         [other_words.append(w) for w in sentence_words]
#         random.shuffle(other_words)
#         response_data = SentenceAnswerResponse(
#             sentence_for_translate=SentenceInfo(id=sentence.id, name=sentence.name),
#             other_words=other_words,
#         )
#         return response_data
#
#     elif language == "en":
#         sentence_words = sentence.translation.name.split()
#         query = await session.execute(select(Word)
#                                       .options(joinedload(Word.translation))
#                                       .where(Word.name.notin_(sentence_words))
#                                       .order_by(func.random()).limit(random.randint(1, 3)))
#         result = query.scalars().all()
#         other_words = [w.translation.name for w in result]
#         [other_words.append(w) for w in sentence_words]
#         random.shuffle(other_words)
#         response_data = SentenceAnswerResponse(
#             sentence_for_translate=SentenceInfo(id=sentence.id, name=sentence.name),
#             other_words=other_words,
#         )
#         return response_data
#
#
# @router.get("/check-sentence-answer")
# async def check_sentence_answer(
#         sentence_id: uuid.UUID,
#         user_words: List[str] = Query(...),
#         session: AsyncSession = Depends(get_async_session)):
#     sentence = await session.scalar(select(Sentence).where(Sentence.id == sentence_id))
#     if sentence.name.lower().replace(",", "") == " ".join(user_words).lower():
#         return True
#     else:
#         return False

