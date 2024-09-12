import random
import uuid

from fastapi import FastAPI, Depends
from sqlalchemy import func, select, and_
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from fastapi.middleware.cors import CORSMiddleware

from .models import Word, User, Exam
from .utils import get_random_words
from .database import get_async_session

app = FastAPI(docs_url=None,title='Learn API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/user")
async def create_user(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    user = User(telegram_id=telegram_id)
    session.add(user)
    await session.commit()


@app.get("/user")
async def get_user_list(session: AsyncSession = Depends(get_async_session)):
    result = await session.execute(select(User))
    users_list = result.scalars().all()

    return [{"user_id": user.id, "user_rating": user.rating, "created_at": user.created_at} for user in users_list]


@app.get("/get-word/eng")
async def get_word(session: AsyncSession = Depends(get_async_session)):
    word_for_translate, random_words = await get_random_words(session)

    return {
        "word_for_translate": {'id': word_for_translate.id,
                               'name': word_for_translate.name},
        "other_words": [
            {'id': word.translation.id, 'name': word.translation.name} for word in random_words
        ]
    }


@app.get("/get-word/rus")
async def get_word(session: AsyncSession = Depends(get_async_session)):
    word_for_translate, random_words = await get_random_words(session)

    return {
        "word_for_translate": {'id': word_for_translate.id,
                               'name': word_for_translate.translation.name},
        "other_words": [
            {'id': word.translation.id, 'name': word.name} for word in random_words
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


@app.get("/exam")
async def exam(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    query = (
        select(Exam)
        .join(Exam.user)
        .join(Exam.word)
        .join(Word.translation)
        .options(
            selectinload(Exam.user),
            selectinload(Exam.word),
            selectinload(Exam.word, Word.translation)
        )
        .where(and_(User.telegram_id == telegram_id, Exam.status == "going"))
        .order_by(Exam.id.desc())
    )
    result = await session.execute(query)
    exam_data = result.scalars().all()
    if exam_data:
        word_for_translate = exam_data[0]
        translated_word = {"id": word_for_translate.word.translation.id, "name": word_for_translate.word.name}
        word_ids = [word.word_id for word in exam_data]
        subquery = (
            select(Word)
            .join(Word.translation)
            .options(joinedload(Word.translation))
            .where(and_(Word.id.not_in(word_ids)),
                   Word.part_of_speech == word_for_translate.word.part_of_speech)
            .order_by(func.random()).limit(2)
        )
        result = await session.execute(subquery)
        random_words = [{"id": word.id, "name": word.name} for word in result.scalars().all()]
        random_words.append(translated_word)
        random.shuffle(random_words)
        return {
            "word_for_translate": {'id': word_for_translate.word.id, 'name': word_for_translate.word.translation.name},
            "other_words": random_words
        }
    else:
        word_for_translate, random_words = await get_random_words(session)
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        new_exam = Exam(
            user_id=user.id,
            status="going",
            word_id=word_for_translate.id,
            answer_status="awaiting response"
        )
        session.add(new_exam)
        await session.commit()

        return {
            "word_for_translate": {'id': word_for_translate.id,
                                   'name': word_for_translate.translation.name},
            "other_words": [
                {'id': word.id, 'name': word.name} for word in random_words
            ]
        }


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css",
    )