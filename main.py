import random
import uuid

from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from fastapi.middleware.cors import CORSMiddleware

from models.models import Word, TranslationWord, session_maker

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

part_of_speech = [
    'noun', 'verb', 'adjective', 'adverb', 'determiner',
    'pronoun', 'preposition', 'numeral', 'conjunction', 'other'
]


@app.get("/get_word")
async def get_word():
    random_part_of_speech = random.choice(part_of_speech)
    async with session_maker() as session:
        query = select(Word).where(Word.part_of_speech == random_part_of_speech).options(joinedload(Word.translation)).order_by(func.random()).limit(3)
        result = await session.execute(query)
    random_words = [random_word for random_word in result.scalars().all()]
    word_for_translate = random_words[0]
    random.shuffle(random_words)

    return {
        "word_for_translate": {'id': word_for_translate.id,
                               'name': word_for_translate.name},
        "other_words": [
            {'id': word.translation.id, 'name': word.translation.name} for word in random_words
        ]
    }


@app.get("/check_answer")
async def check_answer(word_for_translate_id: uuid.UUID, user_choice_word_id: uuid.UUID):
    async with session_maker() as session:
        query = select(Word).where(Word.id == word_for_translate_id)
        word_for_translate = await session.scalar(query)
    if word_for_translate is None:
        return f"Слово с id {word_for_translate_id} не найдено"
    if word_for_translate.translation_id == user_choice_word_id:
        return True
    return False


@app.post("/words")
async def add_words(name: str, translation_name: str, part_of_speech: str, rating: str):
    async with session_maker() as session:
        translation_word = TranslationWord(name=translation_name)
        session.add(translation_word)
        await session.commit()
        word_with_translation = Word(
            name=name,
            translation_id=translation_word.id,
            part_of_speech=part_of_speech,
            rating=rating
        )
        session.add(word_with_translation)
        await session.commit()
