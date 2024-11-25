from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.exams.constants import levels
from src.models import Exam, User


async def update_user_rating(user_rating: str) -> str:
    return levels[user_rating]


async def update_user_progress(result: bool, user_exam: Exam, user: User, session: AsyncSession):
    if result:
        if user_exam.progress == user_exam.total_exercises:
            user_exam.status = "completed"
            new_user_rating = await update_user_rating(user.rating)
            user.rating = new_user_rating
            try:
                await session.commit()
                return {"message": "exam is completed"}
            except Exception:
                await session.rollback()
                raise HTTPException(status_code=500, detail="Ошибка при обновлении данных")
        user_exam.progress += 1
        await session.commit()
        return True
    else:
        if user_exam.attempts == 0:
            user_exam.status = "failed"
            try:
                await session.commit()
                return {"message": "exam is failed"}
            except Exception:
                await session.rollback()
                raise HTTPException(status_code=500, detail="Ошибка при обновлении данных")
        user_exam.attempts -= 1
        try:
            await session.commit()
            return False
        except Exception:
            await session.rollback()
            raise HTTPException(status_code=500, detail="Ошибка при обновлении данных")
