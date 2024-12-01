import random

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from src.exams.constants import levels
from src.exams.schemas import ExamAnswerResponse
from src.models import Exam, User
from src.utils import commit_changes_or_rollback


async def update_user_rating(user_rating: str) -> str:
    return levels[user_rating]


async def update_user_progress(result: bool, user_exam: Exam, user: User, session: AsyncSession) -> ExamAnswerResponse:
    if not user_exam:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="У пользователя нет активных экзаменов")
    if result:
        if user_exam.progress == user_exam.total_exercises:
            return await exam_is_complete(session, user_exam, user)
        user_exam.progress += 1
        await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
        return ExamAnswerResponse(success=True)
    else:
        if user_exam.attempts == 0:
            await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
            return await exam_is_failed(session, user_exam)
        user_exam.attempts -= 1
        await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
        return ExamAnswerResponse(success=False)


async def exam_is_complete(session: AsyncSession, user_exam: Exam, user: User) -> ExamAnswerResponse:
    user_exam.status = "completed"
    new_user_rating = await update_user_rating(user.rating)
    user.rating = new_user_rating
    await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
    response = ExamAnswerResponse(success=True, message="exam is completed")
    return response


async def exam_is_failed(session: AsyncSession, user_exam: Exam) -> ExamAnswerResponse:
    user_exam.status = "failed"
    await commit_changes_or_rollback(session, "Ошибка при обновлении данных")
    response = ExamAnswerResponse(success=False, message="exam is failed")
    return response


def add_user_statistics(exercise_data: dict, user_exam: Exam):
    exercise_data["user_progress"] = user_exam.progress
    exercise_data["total_progress"] = user_exam.total_exercises
    exercise_data["attempts"] = user_exam.attempts
    return exercise_data


async def get_random_exercise(exercises: list, telegram_id: int) -> dict:
    random_exercise = random.choice(exercises)
    random_exercise = await random_exercise(telegram_id)
    exercise = random_exercise.dict()
    return exercise


async def create_exam(user_id: int, session: AsyncSession):
    user_exam = Exam(user_id=user_id)
    session.add(user_exam)
    await commit_changes_or_rollback(session, "Ошибка при создании экзамена")
    return user_exam
