from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session
from src.exams.service import ExamService


def get_exam_service(session: AsyncSession = Depends(get_async_session)):
    return ExamService(session)
