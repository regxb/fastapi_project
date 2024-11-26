import uuid

from fastapi import Depends, APIRouter, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.constants import AvailableLanguages
from src.quizzes.constants import AvailablePartOfSpeech, AvailableWordLevel
from src.quizzes.query import get_available_languages, get_available_part_of_speech
from src.quizzes.schemas import RandomWordResponse, UserFavoriteWord, RandomSentenceResponse
from src.quizzes.service import FavoriteWordService, WordService, SentenceService, AnswerService

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)


@router.post("/add-word")
async def add_word(
        language_from: AvailableLanguages,
        word_to_translate: str,
        language_to: AvailableLanguages,
        translation_word: str,
        part_of_speech: AvailablePartOfSpeech,
        level: AvailableWordLevel,
        session: AsyncSession = Depends(get_async_session)
):
    word_service = WordService(session)
    return await word_service.add_word(language_from, word_to_translate, language_to, translation_word, part_of_speech,
                                       level)


@router.post("/add-sentence")
async def add_sentence(
        translation_from_language: AvailableLanguages,
        sentence_to_translate: str,
        translation_to_language: AvailableLanguages,
        translation_sentence: str,
        level: AvailableWordLevel,
        session: AsyncSession = Depends(get_async_session)
):
    sentence_service = SentenceService(session)
    return await sentence_service.add_sentence(translation_from_language, sentence_to_translate,
                                               translation_to_language,
                                               translation_sentence, level)


@router.post("/favorite-word")
async def add_favorite_word(data: UserFavoriteWord, session: AsyncSession = Depends(get_async_session)):
    favorite_word_service = FavoriteWordService(session)
    return await favorite_word_service.add_favorite_word(data)


@router.delete("/favorite-word")
async def delete_favorite_word(data: UserFavoriteWord, session: AsyncSession = Depends(get_async_session)):
    favorite_word_service = FavoriteWordService(session)
    return await favorite_word_service.delete_favorite_word(data)


@router.get("/check-available-language")
async def check_available_language(session: AsyncSession = Depends(get_async_session)):
    available_languages = await get_available_languages(session)
    return available_languages


@router.get("/check-available-part-of-speech")
async def check_available_part_of_speech(session: AsyncSession = Depends(get_async_session)):
    available_part_of_speech = await get_available_part_of_speech(session)
    return available_part_of_speech


@router.get("/random-word", response_model=RandomWordResponse)
async def get_random_word(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    word_service = WordService(session)
    response = await word_service.get_random_word(telegram_id)
    return response


@router.get("/favorite-word", response_model=RandomWordResponse)
async def get_random_favorite_word(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    favorite_word_service = FavoriteWordService(session)
    return await favorite_word_service.get_random_favorite_word(telegram_id)


@router.get("/check-answer", response_model=bool)
async def check_answer(word_for_translate_id: uuid.UUID, user_word_id: uuid.UUID,
                       session: AsyncSession = Depends(get_async_session)):
    answer_service = AnswerService(session)
    return await answer_service.check_answer(word_for_translate_id, user_word_id)


@router.get("/get-random-sentence", response_model=RandomSentenceResponse)
async def get_random_sentence(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    sentence_service = SentenceService(session)
    return await sentence_service.get_random_sentence(telegram_id)


@router.get("/check-sentence-answer", response_model=bool)
async def check_sentence_answer(
        sentence_id: uuid.UUID,
        user_words: list[str] = Query(...),
        session: AsyncSession = Depends(get_async_session)
):
    answer_service = AnswerService(session)
    return await answer_service.check_sentence_answer(sentence_id, user_words)


@router.get("/match-words")
async def get_match_words(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    word_service = WordService(session)
    return await word_service.get_match_words(telegram_id)
