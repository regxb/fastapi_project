import random
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from models.models import Word, TranslationWord, session_maker

app = FastAPI()


class User(BaseModel):
    id: int
    name: Optional[str] = None


@app.get("/get_word")
async def get_word():
    async with session_maker() as session:
        query = select(Word).options(joinedload(Word.translation)).order_by(func.random()).limit(3)
        result = await session.execute(query)
    random_words = [random_word for random_word in result.scalars().all()]
    word_for_translate = random_words[0]
    random.shuffle(random_words)
    return {
        "word_for_translate": [{word_for_translate.name: word_for_translate.id}],
        "other_words": [
            {word.translation.name: word.id} for word in random_words
        ]
    }


@app.get("/check_answer")
async def check_answer(word_for_translate_id: int, user_choice_word_id: int):
    async with session_maker() as session:
        query = select(Word).where(Word.id == word_for_translate_id)
        word_for_translate = await session.scalar(query)
    if word_for_translate is None:
        return f"Слово с id {word_for_translate_id} не найдено"
    if word_for_translate.translation_id == user_choice_word_id:
        return True
    return False


@app.post("/words")
async def add_words(name: str, translation_name: str):
    async with session_maker() as session:
        translation_word = TranslationWord(name=translation_name)
        session.add(translation_word)
        await session.commit()
        word_with_translation = Word(name=name, translation_id=translation_word.id)
        session.add(word_with_translation)
        await session.commit()
