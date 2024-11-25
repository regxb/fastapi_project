import random
import string
import uuid
from typing import List, Union

from fastapi import Depends, HTTPException, APIRouter, Query
from sqlalchemy import and_
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.exams.query import get_user_exam
from src.exams.schemas import ExamAnswerResponse
from src.exams.service import ExamService
from src.exams.utils import update_user_progress
from src.models import Word, User, TranslationWord, Sentence, Exam
from src.quizzes.query import get_sentence
from src.quizzes.router import get_match_words, get_random_word, get_random_sentence
from src.quizzes.utils import delete_punctuation
from src.schemas import WordInfo
from src.users.query import get_user
from src.utils import get_random_words, check_favorite_words
from src.database import get_async_session

router = APIRouter(
    prefix="/exam",
    tags=["exam"]
)


@router.get("/exam")
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
