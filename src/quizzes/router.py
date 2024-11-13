import random
import string
import time
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
    get_user_favorite_words, get_random_sentence_for_translate, get_random_words_for_sentence, get_available_languages, \
    get_random_words_for_match, get_sentence
from src.quizzes.schemas import RandomWordResponse, UserFavoriteWord, RandomSentenceResponse
from src.quizzes.service import QuizService
from src.quizzes.utils import delete_punctuation, shuffle_random_words
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
async def get_random_word(telegram_id: int):
    quiz = QuizService()
    response = await quiz.get_random_word(telegram_id)
    return response


@router.post("/favorite-word")
async def add_favorite_word(data: UserFavoriteWord):
    quiz = QuizService()
    return await quiz.add_favorite_word(data)


@router.delete("/favorite-word")
async def delete_favorite_word(data: UserFavoriteWord):
    quiz = QuizService()
    return await quiz.delete_favorite_word(data)


@router.get("/favorite-word", response_model=RandomWordResponse)
async def get_random_favorite_word(telegram_id: int):
    quiz = QuizService()
    return await quiz.get_random_favorite_word(telegram_id)


@router.post("/add-word")
async def add_word(
        translation_from_language: AvailableLanguages,
        word_to_translate: str,
        translation_to_language: AvailableLanguages,
        translation_word: str,
        part_of_speech: AvailablePartOfSpeech,
        level: AvailableWordLevel):

    quiz = QuizService()
    return await quiz.add_word(translation_from_language, word_to_translate, translation_to_language, translation_word,
                               part_of_speech, level)


@router.post("/add-sentence")
async def add_sentence(
        translation_from_language: AvailableLanguages,
        sentence_to_translate: str,
        translation_to_language: AvailableLanguages,
        translation_sentence: str,
        level: AvailableWordLevel):

    quiz = QuizService()
    return await quiz.add_sentence(translation_from_language, sentence_to_translate, translation_to_language,
                                   translation_sentence, level)


@router.get("/get-random-sentence", response_model=RandomSentenceResponse)
async def get_random_sentence(telegram_id: int):
    quiz = QuizService()
    return await quiz.get_random_sentence(telegram_id)


@router.get("/check-sentence-answer")
async def check_sentence_answer(
        sentence_id: uuid.UUID,
        user_words: list[str] = Query(...)):
    quiz = QuizService()
    return await quiz.check_sentence_answer(sentence_id, user_words)


@router.get("/match-words")
async def get_match_words(telegram_id: int):
    quiz = QuizService()
    return await quiz.get_match_words(telegram_id)


@router.get("/test")
def get_test():
    time.sleep(10)
