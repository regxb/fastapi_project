from sqlalchemy import select, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Language, Word


async def get_available_languages(session: AsyncSession):
    query = await session.execute(select(Language))
    languages = query.scalars().all()
    return languages


async def get_available_part_of_speech(session: AsyncSession):
    query = await session.execute(select(distinct(Word.part_of_speech)))
    available_part_of_speech = query.scalars().all()
    return [w for w in available_part_of_speech]
