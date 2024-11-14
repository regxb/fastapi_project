from typing import List, Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User


async def get_user(session: AsyncSession, telegram_id: int) -> User:
    query = select(User).where(User.telegram_id == telegram_id)
    user = await session.scalar(query)
    return user


async def get_all_users(session: AsyncSession) -> Sequence[User]:
    result = await session.execute(select(User))
    users_list = result.scalars().all()
    return users_list


async def get_user_data(session: AsyncSession, telegram_id: int) -> User:
    user_data = await session.scalar(select(User).where(User.telegram_id == telegram_id))
    return user_data
