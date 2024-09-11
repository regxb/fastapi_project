import random
import uuid

from fastapi import FastAPI, Depends
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from fastapi.middleware.cors import CORSMiddleware

from .models import Word
from .database import get_async_session

app = FastAPI(docs_url=None,title='Learn API')

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


@app.get("/get-word/eng")
async def get_word(session: AsyncSession = Depends(get_async_session)):
    random_part_of_speech = random.choice(part_of_speech)
    query = select(Word).where(Word.part_of_speech == random_part_of_speech, Word.rating == "A1"
                               ).options(joinedload(Word.translation)).order_by(func.random()).limit(3)
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


@app.get("/get-word/rus")
async def get_word(session: AsyncSession = Depends(get_async_session)):
    random_part_of_speech = random.choice(part_of_speech)
    query = select(Word).where(Word.part_of_speech == random_part_of_speech, Word.rating == "A1"
                               ).options(joinedload(Word.translation)).order_by(func.random()).limit(3)
    result = await session.execute(query)
    random_words = [random_word for random_word in result.scalars().all()]
    word_for_translate = random_words[0]
    random.shuffle(random_words)

    return {
        "word_for_translate": {'id': word_for_translate.id,
                               'name': word_for_translate.translation.name},
        "other_words": [
            {'id': word.id, 'name': word.name} for word in random_words
        ]
    }


@app.get("/check_answer")
async def check_answer(
        word_for_translate_id: uuid.UUID,
        user_choice_word_id: uuid.UUID,
        session: AsyncSession = Depends(get_async_session),
):
    query = select(Word).where(Word.id == word_for_translate_id)
    word_for_translate = await session.scalar(query)
    if word_for_translate is None:
        return f"Слово с id {word_for_translate_id} не найдено"
    if word_for_translate.translation_id == user_choice_word_id:
        return True
    return False
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    )