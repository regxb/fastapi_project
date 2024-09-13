import random
import uuid
from typing import Optional

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import and_
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models import Word, User, Exam, ExamQuestion
from src.utils import get_random_words
from src.database import get_async_session

router = APIRouter(
    prefix="/exam",
    tags=["exam"]
)


@router.post("/start")
async def start_exam(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    query = select(Exam).join(Exam.user).where(and_(User.telegram_id == telegram_id, Exam.status == "going"))
    result = await session.execute(query)
    exam_data = result.scalar()
    if exam_data:
        exam_id = exam_data.id

        query = ((select(Word)
                  .join(ExamQuestion))
                 .options(joinedload(Word.translation))
                 .options(joinedload(Word.exam_question))
                 .where(and_(ExamQuestion.exam_id == exam_id, ExamQuestion.status == "awaiting response")))

        result = await session.execute(query)
        word_for_translate = result.scalar()
        if word_for_translate:
            word_for_translate_data = {
                "id": word_for_translate.translation.id,
                "name": word_for_translate.translation.name
            }
        else:
            query = select(ExamQuestion).where(ExamQuestion.exam_id == exam_id)
            result = await session.execute(query)
            word_objs = result.scalars().all()
            word_ids = [word_obj.word_id for word_obj in word_objs]
            query = (select(Word)
                     .options(joinedload(Word.translation))
                     .where(Word.id not in word_ids).order_by(func.random()).limit(1))
            result = await session.execute(query)
            word_for_translate = result.scalars().first()
            word_for_translate_data = {
                "id": word_for_translate.translation.id,
                "name": word_for_translate.translation.name
            }

            new_exam_question = ExamQuestion(
                exam_id=exam_id,
                word_id=word_for_translate.id,
                status="awaiting response"
            )
            session.add(new_exam_question)
            await session.commit()

        query = (((select(Word)
                   .where(and_(Word.part_of_speech == word_for_translate.part_of_speech,
                               Word.id != word_for_translate.id)))
                  .order_by(func.random()))
                 .limit(2))
        result = await session.execute(query)
        random_words = result.scalars().all()
        other_words = [{"id": random_word.id, "name": random_word.name} for random_word in random_words]
        other_words.append({"id": word_for_translate.id, "name": word_for_translate.name})
        random.shuffle(other_words)
        exam_way = await session.scalar(select(func.count(ExamQuestion.id)).where(ExamQuestion.exam_id == exam_id))
        return {"word_for_translate": word_for_translate_data, "other_words": other_words, "exam_way": exam_way}

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
            "word_for_translate": {'id': word_for_translate.translation_id,
                                   'name': word_for_translate.translation.name},
            "other_words": [
                {'id': word.id, 'name': word.name} for word in random_words
            ],
            "exam_way": 1
        }


@router.get("/check-answer", response_model=Optional[bool])
async def check_exam_answer(
        telegram_id: int,
        word_for_translate_id: uuid.UUID,
        user_choice_word_id: uuid.UUID,
        session: AsyncSession = Depends(get_async_session),
):
    query = select(Word).where(Word.translation_id == word_for_translate_id)
    word_for_translate = await session.scalar(query)
    if word_for_translate is None:
        raise HTTPException(status_code=404, detail=f"Слово с id {word_for_translate_id} не найдено")

    user_data = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    if user_data is None:
        raise HTTPException(status_code=404, detail=f"Пользователь с id {telegram_id} не найден")

    if word_for_translate.id == user_choice_word_id:
        query = (select(ExamQuestion)
                 .join(Exam)
                 .where(and_(Exam.user_id == user_data.id,
                             Exam.status == "going",
                             ExamQuestion.status == "awaiting response")))
        result = await session.execute(query)
        exam_question = result.scalar()

        if exam_question is None:
            raise HTTPException(status_code=404, detail="Вопрос экзамена не найден или уже был решен")

        exam_question.status = "right"

        session.add(exam_question)
        await session.commit()
        return True
    else:
        exam_data = await session.scalar(select(Exam).where(and_(Exam.status == "going", Exam.user_id == user_data.id)))
        exam_data.status = "failed"

        exam_question_data = await session.scalar(select(ExamQuestion)
                                                  .where(and_(ExamQuestion.status == "awaiting response",
                                                              ExamQuestion.exam_id == exam_data.id)))

        exam_question_data.status = "failed"
        await session.commit()
    return False
