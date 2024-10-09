from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User


async def get_user(session: AsyncSession, telegram_id: int):
    query = select(User).where(User.telegram_id == telegram_id)
    user = await session.scalar(query)
    return user
