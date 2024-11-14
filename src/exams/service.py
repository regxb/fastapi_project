import random
import uuid
from typing import List

from fastapi import HTTPException, Query

from src.database import async_session_maker
from src.exams.query import get_user_exam
from src.exams.utils import update_user_progress
from src.models import Exam, TranslationWord
from src.quizzes.query import get_sentence
from src.quizzes.router import get_match_words, get_random_word, get_random_sentence
from src.quizzes.utils import delete_punctuation
from src.users.query import get_user


class ExamService:

    exercises = [get_match_words, get_random_word, get_random_sentence]

    def __init__(self):
        self.session = async_session_maker()

    async def start_exam(self, telegram_id: int):
        async with self.session as session:
            user = await get_user(session, telegram_id)
            user_exam = await get_user_exam(session, user.id)
            if not user_exam:
                new_user_exam = Exam(user_id=user.id)
                session.add(new_user_exam)
                try:
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise HTTPException(status_code=500, detail="Ошибка при создании экзамена")
            random_exercise = random.choice(ExamService.exercises)
            exercise = await random_exercise(telegram_id)
            response = dict(exercise)
            response["user_progress"] = user_exam.progress
            response["total_progress"] = user_exam.total_exercises
            response["attempts"] = user_exam.attempts
            return response

    async def check_exam_sentence_answer(self, sentence_id: uuid.UUID, telegram_id: int,
                                         user_words: List[str] = Query(...)):
        async with self.session as session:
            user = await get_user(session, telegram_id)
            user_exam = await get_user_exam(session, user.id)
            sentence = await get_sentence(session, sentence_id)
            result = delete_punctuation(sentence.name).lower() == " ".join(user_words).lower()
            response = await update_user_progress(result, user_exam, user, session)
            return response

    async def check_exam_answer(
            self,
            word_for_translate_id: uuid.UUID,
            user_word_id: uuid.UUID,
            telegram_id: int,
    ):
        async with self.session as session:
            user = await get_user(session, telegram_id)
            user_exam = await get_user_exam(session, user.id)
            word = await session.get(TranslationWord, user_word_id)
            result = word_for_translate_id == word.word_id
            response = await update_user_progress(result, user_exam, user, session)
            return response
