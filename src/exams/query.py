from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Exam


async def get_user_exam(session: AsyncSession, user_id: int):
    query = select(Exam).where(and_(Exam.user_id == user_id, Exam.status == "started"))
    user_exam = await session.scalar(query)
    return user_exam
