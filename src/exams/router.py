import uuid
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.exams.schemas import ExamAnswerResponse, ExamSchema
from src.exams.service import ExamService

router = APIRouter(
    prefix="/exam",
    tags=["exam"]
)


@router.get("/exam", response_model=ExamSchema)
async def start_exam(telegram_id: int, session: AsyncSession = Depends(get_async_session)):
    exam = ExamService(session)
    return await exam.start_exam(telegram_id)


@router.get("/check-exam-sentence-answer", response_model=ExamAnswerResponse)
async def check_exam_sentence_answer(
        sentence_id: uuid.UUID,
        telegram_id: int,
        user_words: List[str] = Query(...),
        session: AsyncSession = Depends(get_async_session)):
    exam = ExamService(session)
    return await exam.check_exam_sentence_answer(sentence_id, telegram_id, user_words)


@router.get("/check-exam-answer", response_model=ExamAnswerResponse)
async def check_exam_answer(word_for_translate_id: uuid.UUID, user_word_id: uuid.UUID, telegram_id: int,
                            session: AsyncSession = Depends(get_async_session)):
    exam = ExamService(session)
    return await exam.check_exam_answer(word_for_translate_id, user_word_id, telegram_id)
