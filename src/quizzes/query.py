from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import Word, TranslationWord, FavoriteWord


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
