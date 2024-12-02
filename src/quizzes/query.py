import json
import random
import uuid
from typing import Optional
import redis.asyncio as redis
from sqlalchemy import select, func, and_, distinct
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import Word, TranslationWord, FavoriteWord, Sentence, TranslationSentence, Language, User
from src.constants import AvailableLanguages


async def get_translation_words(session: AsyncSession, word_id: uuid.UUID) -> Optional[TranslationWord]:
    query = select(TranslationWord).where(TranslationWord.word_id == word_id)
    word = await session.scalar(query)
    return word


async def get_random_word_for_translate(session: AsyncSession, language_from_id: int):
    query = (select(Word)
             .options(joinedload(Word.translation))
             .where(Word.language_id == language_from_id).order_by(func.random()).limit(1))
    word_for_translate = await session.scalar(query)
    return word_for_translate


async def get_random_words(session: AsyncSession, language_to_id: int, word_for_translate_id):
    query = (select(TranslationWord)
             .where(and_(TranslationWord.to_language_id == language_to_id,
                         TranslationWord.word_id != word_for_translate_id))
             .order_by(func.random()).limit(2))
    result = await session.execute(query)
    other_words = [w for w in result.scalars().all()]
    return other_words


async def get_random_user_favorite_word(session: AsyncSession, user_id: int):
    query = ((select(FavoriteWord).join(FavoriteWord.word).join(Word.translation)
              .options(joinedload(FavoriteWord.word).options(joinedload(Word.translation)))
              .where(FavoriteWord.user_id == user_id))
             .order_by(func.random())
             .limit(1))
    random_user_favorite_word = await session.scalar(query)
    return random_user_favorite_word.word


async def get_user_favorite_words(session: AsyncSession, word_id: uuid.UUID, user_id: int):
    query = select(FavoriteWord).where(and_(FavoriteWord.word_id == word_id, FavoriteWord.user_id == user_id))
    result = await session.scalar(query)
    return result


async def get_user_favorite_word(session: AsyncSession, telegram_id: int, word_id: uuid.UUID):
    query = (select(FavoriteWord)
             .join(FavoriteWord.user)
             .where(and_(User.telegram_id == telegram_id, FavoriteWord.word_id == word_id)))
    user_favorite_word = await session.scalar(query)
    return user_favorite_word


async def get_sentence(session: AsyncSession, sentence_id):
    sentence = await session.scalar(select(Sentence).where(Sentence.id == sentence_id))
    return sentence


async def get_sentence_translation(session: AsyncSession, sentence_id: uuid.UUID):
    query = select(TranslationSentence).where(TranslationSentence.sentence_id == sentence_id)
    translation = await session.scalar(query)
    return translation


async def get_random_sentence_for_translate(session: AsyncSession, language_from_id):
    query = (select(Sentence)
             .join(Sentence.translation)
             .options(joinedload(Sentence.translation))
             .where(Sentence.language_id == language_from_id)
             .order_by(func.random())
             .limit(1))
    random_sentence_for_translate = await session.scalar(query)
    return random_sentence_for_translate


async def get_random_words_for_sentence(session: AsyncSession, language_to_id: int, words_for_sentence: Optional[list]):
    query = (select(TranslationWord.name)
             .where(and_(TranslationWord.to_language_id == language_to_id),
                    TranslationWord.name.notin_(words_for_sentence))
             .order_by(func.random())
             .limit(random.randint(2, 4))
             )
    result = await session.execute(query)
    random_words_for_sentence = result.scalars().all()
    return random_words_for_sentence


async def get_available_languages(session: AsyncSession):
    redis_conn = await redis.from_url("redis://redis:6379")

    value = await redis_conn.get("languages")
    if value:
        return json.loads(value)
    query = await session.execute(select(Language))
    languages = query.scalars().all()
    languages_data = [{"id": w.id, "name": w.language} for w in languages]
    await redis_conn.set("languages", json.dumps(languages_data), ex=3600)
    return languages_data


async def get_available_part_of_speech(session: AsyncSession):
    redis_conn = await redis.from_url("redis://redis:6379")
    value = await redis_conn.get("parts_of_speech")
    if value:
        return json.loads(value)
    query = await session.execute(select(distinct(Word.part_of_speech)))
    available_part_of_speech = query.scalars().all()
    await redis_conn.set("parts_of_speech", json.dumps([w for w in available_part_of_speech]), ex=3600)
    return [w for w in available_part_of_speech]


async def get_random_words_for_match(session: AsyncSession, language_from_id):
    query = ((select(Word)
              .options(joinedload(Word.translation))
              .where(Word.language_id == language_from_id))
             .order_by(func.random())
             .limit(8))
    result = await session.execute(query)
    words = result.scalars().all()
    return words


async def get_language_to(session: AsyncSession, language_to: AvailableLanguages):
    language_to = await session.scalar(select(Language).where(Language.language == language_to.value))
    return language_to


async def get_language_from(session: AsyncSession, language_from: AvailableLanguages):
    language_from = await session.scalar(select(Language).where(Language.language == language_from.value))
    return language_from
