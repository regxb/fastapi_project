import random
import uuid
from typing import List

from fastapi import Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.exams.query import get_user_exam
from src.exams.schemas import ExamAnswerResponseSchema, ExamSchema
from src.models import TranslationWord, Exam, User
from src.quizzes.query import get_sentence_translation
from src.quizzes.service import SentenceService, WordService
from src.quizzes.utils import delete_punctuation
from src.users.query import get_user
from src.users.service import UserService
from src.utils import commit_changes_or_rollback


class ExamManager:

    @staticmethod
    async def create_exam(user_id: int, session: AsyncSession):
        user_exam = Exam(user_id=user_id)
        session.add(user_exam)
        await commit_changes_or_rollback(session, "Ошибка при создании экзамена")
        return user_exam


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
                user_exam = await ExamManager.create_exam(user.id, session)

            exercise = await self.get_random_exercise(telegram_id)
            exercise_type = exercise["type"]

            response = ExamResponseService.create_exam_exercise_response(exercise_type, exercise, user_exam)
            return response

    async def get_random_exercise(self, telegram_id: int) -> dict:
        random_exercise = random.choice(self.exercises)
        random_exercise_data = await random_exercise(telegram_id)
        exercise = random_exercise_data.dict()
        return exercise

    async def check_exam_sentence_answer(self, sentence_id: uuid.UUID, telegram_id: int,
                                         user_words: List[str] = Query(...)) -> ExamAnswerResponseSchema:
        async with self.session as session:
            user = await get_user(session, telegram_id)
            user_exam = await get_user_exam(session, user.id)
            sentence = await get_sentence_translation(session, sentence_id)
            result = delete_punctuation(sentence.name).lower() == " ".join(user_words).lower()
            response = await self.update_user_progress(result, user_exam, user)
            return response

    async def check_exam_answer(
            self,
            word_for_translate_id: uuid.UUID,
            user_word_id: uuid.UUID,
            telegram_id: int,
    ) -> ExamAnswerResponseSchema:
        async with self.session as session:
            user = await get_user(session, telegram_id)
            user_exam = await get_user_exam(session, user.id)
            word = await session.get(TranslationWord, user_word_id)
            result = word_for_translate_id == word.word_id
            response = await self.update_user_progress(result, user_exam, user)
            return response

    async def update_user_progress(self, result: bool, user_exam: Exam, user: User) -> ExamAnswerResponseSchema:
        if not user_exam:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="У пользователя нет активных экзаменов")
        if result:
            return await self.handle_success_answer(user_exam, user)
        else:
            return await self.handle_wrong_answer(user_exam)

    async def handle_success_answer(self, user_exam, user: User):
        async with self.session as session:
            if user_exam.progress == user_exam.total_exercises:
                return await self.exam_is_complete(user_exam, user)
            user_exam.progress += 1
            await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
            return ExamAnswerResponseSchema(success=True)

    async def exam_is_complete(self, user_exam: Exam, user: User) -> ExamAnswerResponseSchema:
        async with self.session as session:
            user_exam.status = "completed"
            new_user_rating = await UserService.update_user_rating(user.rating)
            user.rating = new_user_rating
            await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
            response = ExamAnswerResponseSchema(success=True, message="exam is completed")
        return response

    async def handle_wrong_answer(self, user_exam):
        async with self.session as session:
            if user_exam.attempts == 0:
                await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
                return await self.exam_is_failed(user_exam)
            user_exam.attempts -= 1
            await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
            return ExamAnswerResponseSchema(success=False)

    async def exam_is_failed(self, user_exam: Exam) -> ExamAnswerResponseSchema:
        async with self.session as session:
            user_exam.status = "failed"
            await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
            response = ExamAnswerResponseSchema(success=False, message="exam is failed")
            return response


class ExamResponseService:

    @staticmethod
    def create_exam_exercise_response(exercise_type, exercise, user_exam):
        response = ExamSchema(
            type=exercise_type,
            exercise=exercise,
            user_progress=user_exam.progress,
            total_progress=user_exam.total_exercises,
            attempts=user_exam.attempts
        )
        return response
