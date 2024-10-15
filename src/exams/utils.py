
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Exam, User


async def update_user_rating(user_rating: str) -> str:
    if user_rating == "A1":
        return "A2"
    elif user_rating == "A2":
        return "B1"
    elif user_rating == "B1":
        return "B2"
    elif user_rating == "B2":
        return "C1"
    elif user_rating == "C1":
        return "C2"
    elif user_rating == "C2":
        return "C2"


async def update_user_progress(result: bool, user_exam: Exam, user: User, session: AsyncSession):
    if result:
        if user_exam.progress == user_exam.total_exercises:
            user_exam.status = "completed"
            new_user_rating = await update_user_rating(user.rating)
            user.rating = new_user_rating
            await session.commit()
            return {"message": "exam is completed"}
        user_exam.progress += 1
        await session.commit()
        return True
    else:
        if user_exam.attempts == 0:
            user_exam.status = "failed"
            await session.commit()
            return {"message": "Exam is failed"}
        user_exam.attempts -= 1
        await session.commit()
        return False
