from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.constants import AvailableLanguages
from src.database import get_async_session
from src.quizzes.constants import AvailablePartOfSpeech, AvailableWordLevel
from src.quizzes.query import (get_available_languages,
                               get_available_part_of_speech)
from src.quizzes.schemas import UserFavoriteWord
from src.words.service import (FavoriteWordManagementService,
                               SentenceManagementService,
                               WordManagementService)

router = APIRouter(
    prefix="/words",
    tags=["words"]
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
    word_service = WordManagementService(session)
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
    sentence_service = SentenceManagementService(session)
    return await sentence_service.add_sentence(translation_from_language, sentence_to_translate,
                                               translation_to_language,
                                               translation_sentence, level)


@router.post("/favorite-word")
async def add_favorite_word(data: UserFavoriteWord, session: AsyncSession = Depends(get_async_session)):
    favorite_word_service = FavoriteWordManagementService(session)
    return await favorite_word_service.add_favorite_word(data)


@router.delete("/favorite-word")
async def delete_favorite_word(data: UserFavoriteWord, session: AsyncSession = Depends(get_async_session)):
    favorite_word_service = FavoriteWordManagementService(session)
    return await favorite_word_service.delete_favorite_word(data)


@router.get("/check-available-language")
async def check_available_language(session: AsyncSession = Depends(get_async_session)):
    available_languages = await get_available_languages(session)
    return available_languages


@router.get("/check-available-part-of-speech")
async def check_available_part_of_speech(session: AsyncSession = Depends(get_async_session)):
    available_part_of_speech = await get_available_part_of_speech(session)
    return available_part_of_speech
