import random
import uuid

from fastapi import FastAPI, Depends
from sqlalchemy import func, select, and_
from fastapi.openapi.docs import get_swagger_ui_html
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload
from fastapi.middleware.cors import CORSMiddleware

from .models import Word, User, Exam, ExamQuestion
from .utils import get_random_words
from .database import get_async_session

app = FastAPI(docs_url=None, title='Learn API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/user")
async def create_user(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user:
        return "Пользователь уже зарегестрирован"
    user = User(telegram_id=telegram_id)
    session.add(user)
    await session.commit()
    return "Есть пробитие"


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


@app.get("/check-answer")
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
    query = select(Exam).join(Exam.user).where(and_(User.telegram_id == telegram_id, Exam.status == "going"))
    result = await session.execute(query)
    exam_data = result.scalar()
    if exam_data:
        exam_id = exam_data.id
        query = (select(ExamQuestion).options(joinedload(ExamQuestion.word).options(joinedload(Word.translation)))
                 .where(ExamQuestion.exam_id == exam_id))
        result = await session.execute(query)
        exam_answer_data = result.scalars().all()
        obj_for_translate = exam_answer_data[-1]
        word_for_translate_data = {"id": obj_for_translate.word_id, "name": obj_for_translate.word.translation.name}

        query = (((select(Word)
                 .where(and_(Word.part_of_speech == obj_for_translate.word.part_of_speech,
                             Word.id != obj_for_translate.word_id)))
                 .order_by(func.random()))
                 .limit(2))
        result = await session.execute(query)
        random_words = result.scalars().all()
        other_words = [{"id": random_word.id, "name": random_word.name} for random_word in random_words]
        other_words.append({"id": obj_for_translate.word_id, "name": obj_for_translate.word.name})
        random.shuffle(other_words)
        return {"word_for_translate": word_for_translate_data, "other_words": other_words}

    else:
        word_for_translate, random_words = await get_random_words(session)
        user = await session.scalar(select(User).where(User.telegram_id == telegram_id))
        new_exam = Exam(
            user_id=user.id,
            status="going",
        )
        session.add(new_exam)
        await session.commit()

        new_exam_question = ExamQuestion(
            exam_id=new_exam.id,
            word_id=word_for_translate.id,
            status="awaiting response"
        )
        session.add(new_exam_question)
        await session.commit()

        return {
            "word_for_translate": {'id': word_for_translate.id,
                                   'name': word_for_translate.translation.name},
            "other_words": [
                {'id': word.id, 'name': word.name} for word in random_words
            ]
        }


@app.get("/check-exam-answer")
async def check_answer(
        telegram_id: int,
        word_for_translate_id: uuid.UUID,
        user_choice_word_id: uuid.UUID,
        session: AsyncSession = Depends(get_async_session),
):
    query = select(Word).where(Word.id == word_for_translate_id)
    word_for_translate = await session.scalar(query)
    user_data = await session.execute(
        select(User).options(selectinload(User.exam)).where(User.telegram_id == telegram_id))
    if word_for_translate is None:
        return f"Слово с id {word_for_translate_id} не найдено"
    if word_for_translate.translation_id == user_choice_word_id:
        print(user_data.scalars().all())

        # new_exam = Exam(
        #     user_id=user.id,
        #     status="going",
        #     word_id=word_for_translate.id,
        #     answer_status="awaiting response"
        # )
        # session.add(new_exam)
        # await session.commit()
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
