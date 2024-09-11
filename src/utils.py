import random

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from .models import Word

part_of_speech = [
    'noun', 'verb', 'adjective', 'adverb', 'determiner',
    'pronoun', 'preposition', 'numeral', 'conjunction', 'other'
]


async def get_random_words(session: AsyncSession):
    random_part_of_speech = random.choice(part_of_speech)
    query = select(Word).where(Word.part_of_speech == random_part_of_speech, Word.rating == "A1"
                               ).options(joinedload(Word.translation)).order_by(func.random()).limit(3)
    result = await session.execute(query)
    random_words = [random_word for random_word in result.scalars().all()]
    word_for_translate = random_words[0]
    random.shuffle(random_words)
    return word_for_translate, random_words