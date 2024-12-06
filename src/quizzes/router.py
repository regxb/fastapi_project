import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.quizzes.schemas import RandomSentenceResponse, RandomWordResponse
from src.quizzes.service import (FavoriteWordService, QuizAnswerService,
                                 SentenceService, WordService)

router = APIRouter(
    prefix="/quiz",
    tags=["quiz"]
)


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
    answer_service = QuizAnswerService(session)
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
    answer_service = QuizAnswerService(session)
    return await answer_service.check_sentence_answer(sentence_id, user_words)


@router.get("/match-words")
async def get_match_words(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    word_service = WordService(session)
    return await word_service.get_match_words(telegram_id)
