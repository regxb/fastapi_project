import time
import uuid

from fastapi import Depends, APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.quizzes.constants import AvailableLanguages, AvailablePartOfSpeech, AvailableWordLevel
from src.quizzes.query import get_available_languages
from src.quizzes.schemas import RandomWordResponse, UserFavoriteWord, RandomSentenceResponse
from src.quizzes.service import QuizService

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)


@router.post("/add-word")
async def add_word(
        translation_from_language: AvailableLanguages,
        word_to_translate: str,
        translation_to_language: AvailableLanguages,
        translation_word: str,
        part_of_speech: AvailablePartOfSpeech,
        level: AvailableWordLevel,
        session: AsyncSession = Depends(get_async_session)
):
    quiz = QuizService(session)
    return await quiz.add_word(translation_from_language, word_to_translate, translation_to_language, translation_word,
                               part_of_speech, level)


@router.post("/add-sentence")
async def add_sentence(
        translation_from_language: AvailableLanguages,
        sentence_to_translate: str,
        translation_to_language: AvailableLanguages,
        translation_sentence: str,
        level: AvailableWordLevel,
        session: AsyncSession = Depends(get_async_session)
):
    quiz = QuizService(session)
    return await quiz.add_sentence(translation_from_language, sentence_to_translate, translation_to_language,
                                   translation_sentence, level)


@router.post("/favorite-word")
async def add_favorite_word(data: UserFavoriteWord, session: AsyncSession = Depends(get_async_session)):
    quiz = QuizService(session)
    return await quiz.add_favorite_word(data)


@router.delete("/favorite-word")
async def delete_favorite_word(data: UserFavoriteWord, session: AsyncSession = Depends(get_async_session)):
    quiz = QuizService(session)
    return await quiz.delete_favorite_word(data)


@router.get("/check-available-language")
async def check_available_language(session: AsyncSession = Depends(get_async_session)):
    available_languages = await get_available_languages(session)
    return available_languages


@router.get("/random-word", response_model=RandomWordResponse)
async def get_random_word(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    quiz = QuizService(session)
    response = await quiz.get_random_word(telegram_id)
    return response


@router.get("/favorite-word", response_model=RandomWordResponse)
async def get_random_favorite_word(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    quiz = QuizService(session)
    return await quiz.get_random_favorite_word(telegram_id)


@router.get("/check-answer", response_model=bool)
async def check_answer(word_for_translate_id: uuid.UUID, user_word_id: uuid.UUID,
                       session: AsyncSession = Depends(get_async_session)):
    quiz = QuizService(session)
    return await quiz.check_answer(word_for_translate_id, user_word_id)


@router.get("/get-random-sentence", response_model=RandomSentenceResponse)
async def get_random_sentence(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    quiz = QuizService(session)
    return await quiz.get_random_sentence(telegram_id)


@router.get("/check-sentence-answer", response_model=bool)
async def check_sentence_answer(
        sentence_id: uuid.UUID,
        user_words: list[str] = Query(...),
        session: AsyncSession = Depends(get_async_session)
):
    quiz = QuizService(session)
    return await quiz.check_sentence_answer(sentence_id, user_words)


@router.get("/match-words")
async def get_match_words(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    quiz = QuizService(session)
    return await quiz.get_match_words(telegram_id)



