import json

import redis
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import (FavoriteWord, Sentence, TranslationSentence,
                        TranslationWord, Word)
from src.quizzes.query import get_user_favorite_word, get_user_favorite_words
from src.quizzes.schemas import UserFavoriteWord
from src.users.query import get_user_by_telegram_id
from src.utils import commit_changes_or_rollback
from src.words.query import get_available_part_of_speech, get_available_languages
from src.words.schemas import WordSchema, SentenceSchema


class CacheRedisService:

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    async def get_cached_value(self, key: str):
        value = await self.redis.get(key)
        if value:
            await self.redis.delete(key)
            return json.loads(value)
        return None

    async def set_cached_value(self, key: str, data, expire: int = 3600):
        await self.redis.set(key, json.dumps(data), ex=expire)


class BaseManager:
    def __init__(self, session: AsyncSession):
        self.session = session


class WordManager(BaseManager):

    async def add_word(self, word_data: WordSchema):
        async with self.session as session:
            new_word = Word(
                name=word_data.word_to_translate,
                language_id=word_data.translation_from_language.value,
                part_of_speech=word_data.part_of_speech.name,
                level=word_data.level.upper()
            )

            session.add(new_word)
            await session.flush()

            new_translation_word = TranslationWord(
                name=word_data.translation_word,
                to_language_id=word_data.translation_to_language.value,
                from_language_id=word_data.translation_from_language.value,
                word_id=new_word.id
            )
            session.add(new_translation_word)
            await commit_changes_or_rollback(session, "Ошибка при добавлении слова")
            return {"message": "Слово успешно добавлено"}

    async def get_parts_of_speech(self, cache_service: CacheRedisService):
        parts_of_speech = await cache_service.get_cached_value("parts_of_speech")
        if parts_of_speech:
            return parts_of_speech
        async with self.session as session:
            parts_of_speech = await get_available_part_of_speech(session)
            await cache_service.set_cached_value(
                "parts_of_speech", [part for part in parts_of_speech], 3600
            )
            return parts_of_speech

    async def get_languages(self, cache_service: CacheRedisService):
        languages = await cache_service.get_cached_value("languages")
        if languages:
            return languages
        async with self.session as session:
            languages = await get_available_languages(session)
            languages_data = [{"language": language.language, "id": language.id} for language in languages]
            await cache_service.set_cached_value("languages", languages_data, 3600)
            return languages


class FavoriteWordManager(BaseManager):

    async def add_favorite_word(self, data: UserFavoriteWord):
        async with self.session as session:
            user = await get_user_by_telegram_id(session, data.telegram_id)
            word = await session.get(Word, data.word_id)
            if word is None:
                raise HTTPException(status_code=404, detail="Слово не найдено")

            new_favorite_word_is_exists = await get_user_favorite_words(session, word.id, user.id)

            if new_favorite_word_is_exists:
                raise HTTPException(status_code=201, detail="Данное слово уже добавлено пользователем")

            new_favorite_word = FavoriteWord(
                user_id=user.id,
                word_id=word.id
            )
            session.add(new_favorite_word)
            await commit_changes_or_rollback(session, "Ошибка при добавлении слова в избранное")
            return {"message": "Слово успешно добавлено в избранное"}

    async def delete_favorite_word(self, data: UserFavoriteWord):
        async with self.session as session:
            user_favorite_word = await get_user_favorite_word(session, data.telegram_id, data.word_id)

            if user_favorite_word is None:
                raise HTTPException(status_code=404, detail="Пользователь не добавлял это слово в избранное")

            await session.delete(user_favorite_word)
            await commit_changes_or_rollback(session, "Ошибка при удалении слова из избранного")
            return {"message": "Слово было удалено"}


class SentenceManager(BaseManager):

    async def add_sentence(self, sentence_data: SentenceSchema):
        async with self.session as session:

            new_sentence = Sentence(
                name=sentence_data.sentence_to_translate,
                language_id=sentence_data.translation_from_language.value,
                level=sentence_data.level.value
            )

            session.add(new_sentence)
            await session.flush()

            new_translation_sentence = TranslationSentence(
                name=sentence_data.translation_sentence,
                sentence_id=new_sentence.id,
                from_language_id=sentence_data.translation_from_language.value,
                to_language_id=sentence_data.translation_to_language.value,
            )
            session.add(new_translation_sentence)
            await commit_changes_or_rollback(session, "Ошибка при добавлении предложения")
            return {"message": "Предложение успешно добавлено"}
