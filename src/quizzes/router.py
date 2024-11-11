import random
import string
import uuid
from typing import List

from fastapi import Depends, HTTPException, APIRouter, Query
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

# from src.utils import get_random_words, check_favorite_words
from src.database import get_async_session
from src.models import Word, TranslationWord, User, FavoriteWord, TranslationSentence, Sentence, Language
from src.quizzes.constants import AvailableLanguages, AvailablePartOfSpeech, AvailableWordLevel, \
    parts_of_speech, levels, languages
from src.quizzes.query import get_random_word_for_translate, get_random_words, get_random_user_favorite_word, \
    check_word_in_favorite, get_random_sentence_for_translate, get_random_words_for_sentence, get_available_languages, \
    get_random_words_for_match
from src.quizzes.schemas import RandomWordResponse, UserFavoriteWord, RandomSentenceResponse
from src.schemas import WordInfo, SentenceInfo
from src.users.query import get_user

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)


@router.get("/check-available-language")
async def check_available_language(session: AsyncSession = Depends(get_async_session)):
    available_languages = await get_available_languages(session)
    return available_languages


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
        session: AsyncSession = Depends(get_async_session)):
    user = await get_user(session, telegram_id)
    language_from_id = user.learning_language_from_id
    language_to_id = user.learning_language_to_id

    word_for_translate = await get_random_word_for_translate(session, language_from_id)
    other_words = await get_random_words(session, language_to_id, word_for_translate.id)
    other_words.append(word_for_translate.translation)
    random.shuffle(other_words)

    in_favorite = await check_word_in_favorite(session, word_for_translate.id, user.id)

    response = RandomWordResponse(
        word_for_translate=WordInfo(name=word_for_translate.name, id=word_for_translate.id),
        other_words=[WordInfo(name=w.name, id=w.id) for w in other_words],
        in_favorite=in_favorite
    )
    return response


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


@router.post("/add-word")
async def add_word(
        translation_from_language: AvailableLanguages,
        word_to_translate: str,
        translation_to_language: AvailableLanguages,
        translation_word: str,
        part_of_speech: AvailablePartOfSpeech,
        level: AvailableWordLevel,
        session: AsyncSession = Depends(get_async_session)):
    new_word = Word(
        name=word_to_translate,
        language_id=languages.get(translation_from_language),
        part_of_speech=part_of_speech.name,
        level=levels.get(level.name)
    )
    session.add(new_word)
    await session.flush()

    new_translation_word = TranslationWord(
        name=translation_word,
        to_language_id=languages.get(translation_to_language),
        from_language_id=languages.get(translation_from_language),
        word_id=new_word.id
    )
    session.add(new_translation_word)
    await session.commit()


@router.post("/add-sentence")
async def add_sentence(
        translation_from_language: AvailableLanguages,
        sentence_to_translate: str,
        translation_to_language: AvailableLanguages,
        translation_sentence: str,
        session: AsyncSession = Depends(get_async_session)):
    new_sentence = Sentence(
        name=sentence_to_translate,
        language_id=languages.get(translation_from_language)
    )
    session.add(new_sentence)
    await session.flush()

    new_translation_sentence = TranslationSentence(
        name=translation_sentence,
        sentence_id=new_sentence.id,
        from_language_id=languages.get(translation_from_language),
        to_language_id=languages.get(translation_to_language),
    )
    session.add(new_translation_sentence)
    await session.commit()


@router.get("/get-random-sentence", response_model=RandomSentenceResponse)
async def get_random_sentence(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    user = await get_user(session, telegram_id)
    language_from_id = user.learning_language_from_id
    language_to_id = user.learning_language_to_id

    random_sentence_for_translate = await get_random_sentence_for_translate(session, language_to_id, language_from_id)
    words_for_sentence = random_sentence_for_translate.name.translate(str.maketrans('', '', string.punctuation)).split()

    random_words_for_sentence = await get_random_words_for_sentence(session, language_to_id, words_for_sentence)
    [words_for_sentence.append(w) for w in random_words_for_sentence]
    random.shuffle(words_for_sentence)

    response = RandomSentenceResponse(
        sentence_for_translate=SentenceInfo(
            id=random_sentence_for_translate.id,
            name=random_sentence_for_translate.translation.name
        ),
        words_for_sentence=words_for_sentence
    )
    return response


@router.get("/check-sentence-answer")
async def check_sentence_answer(
        sentence_id: uuid.UUID,
        user_words: list[str] = Query(...),
        session: AsyncSession = Depends(get_async_session)):
    sentence = await session.scalar(select(Sentence).where(Sentence.id == sentence_id))
    return sentence.name.translate(str.maketrans('', '', string.punctuation)).lower() == " ".join(user_words).lower()


@router.get("/match-words")
async def get_match_words(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    user = await get_user(session, telegram_id)
    language_from_id = user.learning_language_from_id
    words = await get_random_words_for_match(session, language_from_id)
    words_list = [{"id": w.id, "name": w.name} for w in words]
    random.shuffle(words_list)
    translation_words_list = [{"id": w.translation.id, "name": w.translation.name} for w in words]
    random.shuffle(translation_words_list)
    response = {"words": words_list, "translation_words": translation_words_list}
    return response


@router.get("/test")
async def get_test():
    return {"message": "test1"}
