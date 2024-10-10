import random
import uuid
from typing import Optional

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import Word, TranslationWord, FavoriteWord, Sentence, TranslationSentence, Language


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
    return random_user_favorite_word


async def check_word_in_favorite(session: AsyncSession, word_id: uuid.UUID, user_id: int):
    query = select(FavoriteWord).where(and_(FavoriteWord.word_id == word_id, FavoriteWord.user_id == user_id))
    result = await session.scalar(query)
    return False if result is None else True


async def get_random_sentence_for_translate(session: AsyncSession, language_from_id, language_to_id):
    query = (select(Sentence)
             .join(Sentence.translation)
             .options(joinedload(Sentence.translation))
             .where(and_(Sentence.language_id == language_from_id,
                         TranslationSentence.to_language_id == language_to_id))
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
    available_languages = await session.execute(select(Language))
    return [{"id": w.id, "name": w.language} for w in available_languages.scalars().all()]


async def get_random_words_for_match(session: AsyncSession, language_from_id):
    query = ((select(Word)
              .options(joinedload(Word.translation))
              .where(Word.language_id == language_from_id))
             .order_by(func.random())
             .limit(8))
    result = await session.execute(query)
    words = result.scalars().all()
    return words
