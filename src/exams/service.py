import uuid
from typing import List

from fastapi import Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.exams.query import get_user_exam
from src.exams.schemas import ExamSchema, ExamAnswerResponse
from src.exams.utils import update_user_progress, get_random_exercise, create_exam
from src.models import TranslationWord
from src.quizzes.query import get_sentence_translation
from src.quizzes.service import WordService, SentenceService
from src.quizzes.utils import delete_punctuation
from src.users.query import get_user


class ExamService:

    def __init__(self, session: AsyncSession):
        self.session = session
        self.word_service = WordService(session)
        self.sentence_service = SentenceService(session)
        self.exercises = [self.sentence_service.get_random_sentence,
                          self.word_service.get_random_word]
                          # self.word_service.get_match_words

    async def start_exam(self, telegram_id: int) -> ExamSchema:
        async with self.session as session:
            user = await get_user(session, telegram_id)
            user_exam = await get_user_exam(session, user.id)
            if not user_exam:
                user_exam = await create_exam(user.id, session)

            exercise = await get_random_exercise(self.exercises, telegram_id)
            exercise_type = exercise["type"]
            del exercise["type"]

            response = ExamSchema(
                type=exercise_type,
                exercise=exercise,
                user_progress=user_exam.progress,
                total_progress=user_exam.total_exercises,
                attempts=user_exam.attempts
            )
            return response

    async def check_exam_sentence_answer(self, sentence_id: uuid.UUID, telegram_id: int,
                                         user_words: List[str] = Query(...)) -> ExamAnswerResponse:
        async with self.session as session:
            user = await get_user(session, telegram_id)
            user_exam = await get_user_exam(session, user.id)
            sentence = await get_sentence_translation(session, sentence_id)
            result = delete_punctuation(sentence.name).lower() == " ".join(user_words).lower()
            response = await update_user_progress(result, user_exam, user, session)
            return response

    async def check_exam_answer(
            self,
            word_for_translate_id: uuid.UUID,
            user_word_id: uuid.UUID,
            telegram_id: int,
    ) -> ExamAnswerResponse:
        async with self.session as session:
            user = await get_user(session, telegram_id)
            user_exam = await get_user_exam(session, user.id)
            word = await session.get(TranslationWord, user_word_id)
            result = word_for_translate_id == word.word_id
            response = await update_user_progress(result, user_exam, user, session)
            return response
